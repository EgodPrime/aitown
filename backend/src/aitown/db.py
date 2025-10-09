import sqlite3
from pathlib import Path
from typing import Optional


def get_connection(db_path: str = ":memory:") -> sqlite3.Connection:
    """Return a sqlite3 Connection with recommended pragmas set."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Ensure foreign keys are enabled for the connection
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: sqlite3.Connection, migrations_path: Optional[str] = None) -> None:
    """Initialize DB schema by running the migration SQL file.

    If migrations_path is None, it will look for migrations/0001_init.sql
    relative to this file (../migrations/0001_init.sql).
    """
    if migrations_path is None:
        migrations_path = Path(__file__).resolve().parents[1] / "migrations" / "0001_init.sql"
    else:
        migrations_path = Path(migrations_path)

    if not migrations_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migrations_path}")

    sql = migrations_path.read_text(encoding="utf-8")
    conn.executescript(sql)
