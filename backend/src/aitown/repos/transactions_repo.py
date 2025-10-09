from dataclasses import dataclass
from typing import Optional, List
import sqlite3
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import TransactionsRepositoryInterface


@dataclass
class Transaction:
    id: Optional[int]
    npc_id: Optional[str]
    item_id: Optional[str]
    amount: int
    reason: Optional[str]
    created_at: str


class TransactionsRepository(TransactionsRepositoryInterface):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        try:
            self.conn.row_factory = sqlite3.Row
        except Exception:
            pass

    def append(self, npc_id: Optional[str], item_id: Optional[str], amount: int, reason: Optional[str], created_at: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO transactions (npc_id, item_id, amount, reason, created_at) VALUES (?, ?, ?, ?, ?)",
            (npc_id, item_id, amount, reason, created_at),
        )
        self.conn.commit()
        return cur.lastrowid

    def list_by_npc(self, npc_id: str, limit: int = 100) -> List[Transaction]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM transactions WHERE npc_id = ? ORDER BY id DESC LIMIT ?", (npc_id, int(limit)))
        rows = cur.fetchall()
        return [Transaction(id=r["id"], npc_id=r["npc_id"], item_id=r["item_id"], amount=r["amount"], reason=r["reason"], created_at=r["created_at"]) for r in rows]
