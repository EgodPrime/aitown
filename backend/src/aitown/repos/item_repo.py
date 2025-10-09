from dataclasses import dataclass
from typing import Optional, List
import sqlite3
import uuid
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import ItemRepositoryInterface


@dataclass
class Item:
    id: str
    name: str
    description: Optional[str]


class ItemRepository(ItemRepositoryInterface):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        try:
            self.conn.row_factory = sqlite3.Row
        except Exception:
            pass

    def create(self, item: Item) -> Item:
        if not item.id:
            item.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO item (id, name, description) VALUES (?, ?, ?)",
                (item.id, item.name, item.description),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return item

    def get_by_id(self, id: str) -> Item:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Item not found: {id}")
        return Item(id=row["id"], name=row["name"], description=row["description"])

    def list_all(self) -> List[Item]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item")
        rows = cur.fetchall()
        return [Item(id=r["id"], name=r["name"], description=r["description"]) for r in rows]

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM item WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Item not found: {id}")
        self.conn.commit()
