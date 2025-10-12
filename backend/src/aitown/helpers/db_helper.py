from __future__ import annotations

import argparse
import datetime
import time
import sqlite3
from pathlib import Path
from typing import Union
import weakref

from aitown.helpers.config_helper import get_config
from aitown.helpers.path_helper import PROJECT_ROOT
from aitown.repos.base import to_json_text


def _migration_path() -> Path:
    # backend/scripts/init_db.py -> backend/
    return PROJECT_ROOT / "migrations" / "0001_init.sql"


def init_db(
    conn_or_path: Union[str, sqlite3.Connection], seed: bool = False
) -> sqlite3.Connection:
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
        now = time.time()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)",
            ("player:seed", "Seed Player", None, now),
        )
   
        from aitown.helpers.static_data_helper import (
            get_towns,
            get_effects,
            get_items,
            get_places,
        )

        for t in get_towns():
            cur.execute(
                "INSERT OR IGNORE INTO town (id, name, description) VALUES (?,?,?)",
                (t.get("id"), t.get("name"), t.get("description")),
            )

        for p in get_places():
            cur.execute(
                "INSERT OR IGNORE INTO place (id, name, tags, shop_inventory) VALUES (?,?,?,?)",
                (
                    p.get("id"),
                    p.get("name"),
                    to_json_text(p.get("tags", [])),
                    to_json_text(p.get("shop_inventory", [])),
                ),
            )

        for e in get_effects():
            cur.execute(
                "INSERT OR IGNORE INTO effect (id, name, attribute, change) VALUES (?, ?, ?, ?)",
                (e.get("id"), e.get("name"), e.get("attribute"), e.get("change")),
            )

        for i in get_items():
            cur.execute(
                "INSERT OR IGNORE INTO item (id, name, value, type, effect_ids, description) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    i.get("id"),
                    i.get("name"),
                    i.get("value", 0),
                    i.get("type", "MISC"),
                    to_json_text(i.get("effect_ids", [])),
                    i.get("description"),
                ),
            )

        conn.commit()

    # If we created the connection internally, return a thin proxy that will
    # ensure the underlying sqlite3.Connection is closed if the test does not
    # explicitly close it. This prevents ResourceWarning: unclosed database
    # when pytest collects garbage.
    if created:
        class _ConnProxy:
            def __init__(self, conn: sqlite3.Connection):
                self._conn = conn
                # use weakref.finalize to ensure conn.close is called when
                # the proxy object is garbage-collected; this is more
                # reliable than relying solely on __del__.
                try:
                    weakref.finalize(self, conn.close)
                except Exception: # pragma: no cover
                    pass # pragma: no cover

            def __getattr__(self, name):
                return getattr(self._conn, name)

            def close(self):
                try:
                    self._conn.close()
                except Exception:
                    pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                self.close()

            def __del__(self):
                # Ensure underlying connection is closed to avoid ResourceWarning
                try:
                    self._conn.close()
                except Exception:
                    pass

        return _ConnProxy(conn)

    return conn


def load_db(db_path: str = None) -> sqlite3.Connection:
    """Load database connection, reading db_path from config if None.

    Creates a connection without initializing the database schema.
    Use init_db() if you need to initialize the database structure.

    Args:
        db_path: Optional database path. If None, reads from config.toml [repos].db_path

    Returns:
        sqlite3.Connection: database connection

    Raises:
        KeyError: if db_path is None and config doesn't contain repos.db_path
        FileNotFoundError: if config file not found
    """
    if db_path is None:
        repos_config = get_config("repos")
        db_path = repos_config["db_path"]

    conn = sqlite3.connect(db_path)
    # Ensure foreign keys behavior is consistent
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        conn.row_factory = sqlite3.Row
    except Exception:
        # If the connection object doesn't support row_factory assignment, ignore
        pass

    mig = _migration_path()
    if not mig.exists():
        conn.close()
        raise FileNotFoundError(f"Migration file not found: {mig}")

    sql = mig.read_text(encoding="utf-8")
    conn.executescript(sql)

    # Wrap connections we created so that they are closed on GC to avoid
    # ResourceWarning in tests which don't explicitly close the connection.
    class _ConnProxy:
        def __init__(self, conn: sqlite3.Connection):
            self._conn = conn
            try:
                weakref.finalize(self, conn.close)
            except Exception: # pragma: no cover
                pass # pragma: no cover

        def __getattr__(self, name):
            return getattr(self._conn, name)

        def close(self):
            try:
                self._conn.close()
            except Exception:
                pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

        def __del__(self):
            try:
                self._conn.close()
            except Exception:
                pass

    return _ConnProxy(conn)


def main():
    p = argparse.ArgumentParser(
        description="Initialize SQLite DB from migrations/0001_init.sql"
    )
    p.add_argument(
        "--db", default=":memory:", help="SQLite DB path or ':memory:' (default)"
    )
    p.add_argument("--seed", action="store_true", help="Insert minimal seed data")
    args = p.parse_args()

    conn = init_db(args.db, seed=args.seed)
    # If using a file DB, close when done
    if args.db != ":memory:":
        conn.close()
