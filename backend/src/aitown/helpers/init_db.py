from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Union
import datetime
import argparse

from aitown.helpers.paths import PROJECT_ROOT


def _migration_path() -> Path:
    # backend/scripts/init_db.py -> backend/
    return PROJECT_ROOT / "migrations" / "0001_init.sql"


def init_db(conn_or_path: Union[str, sqlite3.Connection], seed: bool = False) -> sqlite3.Connection:
    """Initialize an SQLite database using migrations/0001_init.sql.

    Args:
        conn_or_path: sqlite3.Connection or a path string (e.g. ':memory:' or '/tmp/db.sqlite').
        seed: if True, insert minimal seed data (player/place/item).

    Returns:
        sqlite3.Connection: the opened connection (caller is responsible for closing if they passed a path).
    """
    created = False
    if isinstance(conn_or_path, str):
        conn = sqlite3.connect(conn_or_path)
        created = True
    elif isinstance(conn_or_path, sqlite3.Connection):
        conn = conn_or_path
    else:
        raise TypeError("conn_or_path must be sqlite3.Connection or path string")

    # Ensure foreign keys behavior is consistent
    conn.execute("PRAGMA foreign_keys = ON;")
    # Make row access by name convenient for callers/repos
    try:
        conn.row_factory = sqlite3.Row
    except Exception:
        # If the connection object doesn't support row_factory assignment, ignore
        pass

    mig = _migration_path()
    if not mig.exists():
        if created:
            conn.close()
        raise FileNotFoundError(f"Migration file not found: {mig}")

    sql = mig.read_text(encoding="utf-8")
    conn.executescript(sql)

    if seed:
        now = datetime.datetime.now().isoformat()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)",
            ("player:seed", "Seed Player", None, now),
        )
        cur.execute(
            "INSERT OR IGNORE INTO place (id, name, tags, shop_inventory, created_at) VALUES (?,?,?,?,?)",
            ("place:seed", "Seed Place", "[]", "[]", now),
        )
        cur.execute(
            "INSERT OR IGNORE INTO item (id, name, description) VALUES (?,?,?)",
            ("item:seed", "Seed Item", "Seed item description"),
        )
        conn.commit()

    return conn


def main():
    p = argparse.ArgumentParser(description="Initialize SQLite DB from migrations/0001_init.sql")
    p.add_argument("--db", default=":memory:", help="SQLite DB path or ':memory:' (default)")
    p.add_argument("--seed", action="store_true", help="Insert minimal seed data")
    args = p.parse_args()

    conn = init_db(args.db, seed=args.seed)
    # If using a file DB, close when done
    if args.db != ":memory:":
        conn.close()