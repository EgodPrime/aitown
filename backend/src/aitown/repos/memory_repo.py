import datetime
import sqlite3
from typing import List, Optional

from pydantic import BaseModel

from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import MemoryEntryRepositoryInterface


class MemoryEntry(BaseModel):
    id: Optional[int] = None
    npc_id: Optional[str] = None
    content: Optional[str] = None
    created_at: Optional[str] = None


class MemoryEntryRepository(MemoryEntryRepositoryInterface):
    def create(self, memory_entry: MemoryEntry) -> MemoryEntry:
        if not memory_entry.created_at:
            memory_entry.created_at = datetime.datetime.now().isoformat()
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO memory_entry (npc_id, content, created_at) VALUES (?, ?, ?)",
                (memory_entry.npc_id, memory_entry.content, memory_entry.created_at),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        memory_entry.id = cur.lastrowid
        self.conn.commit()
        return memory_entry

    def get_by_id(self, id: int) -> MemoryEntry:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM memory_entry WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"MemoryEntry not found: {id}")
        return MemoryEntry(
            id=row["id"],
            npc_id=row["npc_id"],
            content=row["content"],
            created_at=row["created_at"],
        )

    def list_by_npc(self, npc_id: str, limit: int = 100) -> List[MemoryEntry]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM memory_entry WHERE npc_id = ? ORDER BY created_at DESC LIMIT ?",
            (npc_id, limit),
        )
        rows = cur.fetchall()
        return [
            MemoryEntry(
                id=r["id"],
                npc_id=r["npc_id"],
                content=r["content"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete(self, id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM memory_entry WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"MemoryEntry not found: {id}")
        self.conn.commit()
