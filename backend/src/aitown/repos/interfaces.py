"""Repository interfaces for persistence layer.

Abstract base classes describing repository contracts used across the codebase.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional, Generic, TypeVar, Protocol

from aitown.helpers.db_helper import load_db

T = TypeVar('T')

class RepositoryInterface(Protocol, Generic[T]):
    def get(self, id: int) -> Optional[T]: ...
    def list(self, limit: int, offset: int) -> List[T]: ...
    def create(self, obj: T) -> T: ...
    def update(self, id: int, obj: T) -> Optional[T]: ...
    def delete(self, id: int) -> bool: ...

    def __init__(self, conn: Optional[sqlite3.Connection]=None):
        self.created = False
        if conn is None:
            conn = load_db()
            self.created = True
        self.conn = conn

        try:
            self.conn.row_factory = sqlite3.Row
        except Exception:
            pass

    def __del__(self):
        if self.created and self.conn:
            try:
                self.conn.close()
            except Exception:  # pragma: no cover
                pass  # pragma: no cover