"""Repository interfaces for persistence layer.

Abstract base classes describing repository contracts used across the codebase.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional, TypeVar, Generic
import json

from loguru import logger
from aitown.models.interface import Model
from aitown.helpers.db_helper import load_db

T = TypeVar('T', bound=Model)


class RepositoryInterface(Generic[T]):
    def __init__(self, conn: Optional[sqlite3.Connection]=None):
        if conn is None:
            conn = load_db()
        self.conn = conn
        self.table_name = 'object'  # Placeholder, should be overridden in subclasses
        

    def create(self, obj: T) -> Optional[T]:
        """Persist a new object and return it, or None on failure."""
        cur = self.conn.cursor()
        data = obj.model_dump()
        placeholders = ', '.join('?' * len(data))
        columns = ', '.join(data.keys())
        values = tuple(data.values())
        try:
            cur.execute(f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})", values)
            self.conn.commit()
            obj.id = cur.lastrowid
            return obj
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error creating object: {e}")
            return None
        
    def delete(self, id: int) -> bool:
        """Delete an object by id. Returns True if deleted, False if not found or error."""
        cur = self.conn.cursor()
        try:
            cur.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (id,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error deleting object: {e}")
            return False

    def get(self, id: int) -> Optional[T]:
        """Fetch an object by id or return None if not found."""
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {self.table_name} WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            return None
        return T.model_validate(dict(row))

    def list(self, limit: int=100, offset: int=0) -> List[T]:
        """List objects with pagination."""
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM {self.table_name} LIMIT ? OFFSET ?", (limit, offset))
        rows = cur.fetchall()
        return [T.model_validate(dict(r)) for r in rows]

    def update(self, id: int, obj: T) -> Optional[T]:
        cur = self.conn.cursor()
        data = obj.model_dump()
        columns = ', '.join(f"{k}=?" for k in data.keys() if k != 'id')
        values = tuple(v for k, v in data.items() if k != 'id') + (id,)
        try:
            cur.execute(f"UPDATE {self.table_name} SET {columns} WHERE id = ?", values)
            if cur.rowcount == 0:
                return None
            self.conn.commit()
            return obj
        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Error updating object: {e}")
            return None
