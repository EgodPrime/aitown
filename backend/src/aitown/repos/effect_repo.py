"""Effect repository and Effect model.

Represents effects that can be applied to NPC attributes and a repository to persist them.
"""

import sqlite3
from typing import Optional

from aitown.models.effect_model import Effect
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import EffectRepositoryInterface
from aitown.repos.npc_repo import NpcRepository


class EffectRepository(EffectRepositoryInterface):
    def create(self, effect: Effect) -> Effect:
        """Insert an effect row and return it."""
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO effect (id, name, attribute, change) VALUES (?, ?, ?, ?)",
                (effect.id, effect.name, effect.attribute, effect.change),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return effect

    def get_by_id(self, id: str) -> Effect:
        """Fetch an Effect by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM effect WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Effect not found: {id}")
        return Effect(
            id=row["id"],
            name=row["name"],
            attribute=row["attribute"],
            change=row["change"],
        )

    def delete(self, id: str) -> None:
        """Delete an effect row or raise NotFoundError if absent."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM effect WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Effect not found: {id}")
        self.conn.commit()
