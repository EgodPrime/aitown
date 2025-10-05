import os
import json
from typing import Dict, Any, Optional
import sqlite3
from pathlib import Path

from loguru import logger

_RAISE_ON_ERROR = os.environ.get('RAISE_ON_PERSISTENCE_ERROR') == '1'

_PATH = os.environ.get('PLAYER_API_CONFIG_PATH', 'player_api_configs.json')
_SECRET = os.environ.get('PLAYER_API_SECRET')
_SQLITE_PATH = os.environ.get('SQLITE_DB_PATH')


def _init_sqlite(path: str):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS player_api_configs (
        player_id TEXT PRIMARY KEY,
        cfg TEXT NOT NULL
    )
    ''')
    cur.execute('''
    CREATE TABLE IF NOT EXISTS npcs (
        npc_id TEXT PRIMARY KEY,
        data TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

try:
    from cryptography.fernet import Fernet
    _HAS_FERNET = True
except Exception:
    Fernet = None  # type: ignore
    _HAS_FERNET = False


def _get_fernet() -> Optional[object]:
    if not _HAS_FERNET or not _SECRET:
        return None
    # SECRET should be base64 urlsafe key for Fernet
    try:
        return Fernet(_SECRET)
    except Exception:
        return None


def load_all_configs(path: str = _PATH) -> Dict[str, Dict[str, Any]]:
    # If sqlite is configured, load from sqlite
    if _SQLITE_PATH:
        try:
            _init_sqlite(_SQLITE_PATH)
            conn = sqlite3.connect(_SQLITE_PATH)
            cur = conn.cursor()
            cur.execute('SELECT player_id, cfg FROM player_api_configs')
            rows = cur.fetchall()
            conn.close()
            out: Dict[str, Dict[str, Any]] = {}
            for pid, cfg_text in rows:
                try:
                    out[pid] = json.loads(cfg_text)
                except Exception:
                    out[pid] = {}
            return out
        except Exception:
            return {}

    if not os.path.exists(path):
        return {}
    raw = open(path, 'rb').read()
    f = _get_fernet()
    if f:
        try:
            raw = f.decrypt(raw)
        except Exception:
            # decryption failed
            return {}
    try:
        return json.loads(raw.decode('utf-8'))
    except Exception:
        return {}


def save_config(player_id: str, cfg: Dict[str, Any], path: str = _PATH) -> None:
    # If sqlite is configured, save into sqlite table
    if _SQLITE_PATH:
        try:
            _init_sqlite(_SQLITE_PATH)
            conn = sqlite3.connect(_SQLITE_PATH)
            cur = conn.cursor()
            cur.execute('INSERT OR REPLACE INTO player_api_configs(player_id, cfg) VALUES(?, ?)',
                        (player_id, json.dumps(cfg)))
            conn.commit()
            conn.close()
            return
        except Exception:
            # fallback to file-based if sqlite fails
            pass

    data = load_all_configs(path)
    data[player_id] = cfg
    raw = json.dumps(data, indent=2).encode('utf-8')
    f = _get_fernet()
    if f:
        raw = f.encrypt(raw)
    with open(path, 'wb') as fh:
        fh.write(raw)


def load_all_npcs(sqlite_path: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    db = sqlite_path or _SQLITE_PATH
    if db:
        try:
            _init_sqlite(db)
            conn = sqlite3.connect(db, check_same_thread=False)
            # enable WAL and reasonable busy timeout for better concurrency
            try:
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=5000')
            except Exception:
                # pragma may be unsupported in some environments; ignore
                pass
            cur = conn.cursor()
            cur.execute('SELECT npc_id, data FROM npcs')
            rows = cur.fetchall()
            conn.close()
            out: Dict[str, Dict[str, Any]] = {}
            for nid, data_text in rows:
                try:
                    out[nid] = json.loads(data_text)
                except Exception:
                    out[nid] = {}
            return out
        except Exception as e:
            logger.exception('Failed loading NPCs from sqlite: {}', e)
            if _RAISE_ON_ERROR:
                raise
            return {}
    return {}


def save_npc(npc_id: str, data: Dict[str, Any], sqlite_path: Optional[str] = None) -> None:
    db = sqlite_path or _SQLITE_PATH
    if db:
        try:
            _init_sqlite(db)
            conn = sqlite3.connect(db, check_same_thread=False)
            cur = conn.cursor()
            cur.execute('INSERT OR REPLACE INTO npcs(npc_id, data) VALUES(?, ?)', (npc_id, json.dumps(data)))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            logger.exception('Failed saving NPC {} to sqlite: {}', npc_id, e)
            if _RAISE_ON_ERROR:
                raise
            # fallback to file-based behavior (no-op here)
            pass


def delete_npc(npc_id: str, sqlite_path: Optional[str] = None) -> None:
    db = sqlite_path or _SQLITE_PATH
    if db:
        try:
            _init_sqlite(db)
            conn = sqlite3.connect(db, check_same_thread=False)
            cur = conn.cursor()
            cur.execute('DELETE FROM npcs WHERE npc_id = ?', (npc_id,))
            conn.commit()
            conn.close()
            return
        except Exception as e:
            logger.exception('Failed deleting NPC {} from sqlite: {}', npc_id, e)
            if _RAISE_ON_ERROR:
                raise
            pass
