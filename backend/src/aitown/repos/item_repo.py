"""Item repository and item model.

Provides Item pydantic model and ItemRepository for DB operations.
"""

import enum
import sqlite3
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from aitown.repos.base import NotFoundError, from_json_text, to_json_text
from aitown.repos.interfaces import ItemRepositoryInterface


class ItemType(enum.StrEnum):
    CONSUMABLE = "CONSUMABLE"
    EQUIPMENT = "EQUIPMENT"
    MONETARY = "MONETARY"
    MISC = "MISC"


class Item(BaseModel):
    """Represents an in-game item and its metadata."""
    id: Optional[str] = None
    name: str
    value: int = 0
    # keep a non-null default to match DB NOT NULL constraint
    type: str = ItemType.MISC
    effect_ids: list[str] = Field(default_factory=list)
    description: Optional[str] = None


class ItemRepository(ItemRepositoryInterface):
    """SQLite-backed repository for Item objects."""
    def create(self, item: Item) -> Item:
        """Persist a new Item to the database and return it.

        Raises ConflictError if id conflicts.
        """
        if not item.id:
            item.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO item (id, name, value, type, effect_ids, description) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.id,
                    item.name,
                    item.value,
                    str(item.type),
                    to_json_text(item.effect_ids),
                    item.description,
                ),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return item

    def get_by_id(self, id: str) -> Item:
        """Return an Item by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Item not found: {id}")
        return Item(
            id=row["id"],
            name=row["name"],
            value=row["value"],
            type=row["type"],
            effect_ids=from_json_text(row["effect_ids"]) or [],
            description=row["description"],
        )

    def list_all(self) -> List[Item]:
        """Return all items stored in the DB."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item")
        rows = cur.fetchall()
        return [
            Item(
                id=r["id"],
                name=r["name"],
                value=r["value"],
                type=r["type"],
                effect_ids=from_json_text(r["effect_ids"]) or [],
                description=r["description"],
            )
            for r in rows
        ]

    def delete(self, id: str) -> None:
        """Delete an item by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM item WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Item not found: {id}")
        self.conn.commit()
