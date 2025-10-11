"""NPC model and repository.

Defines the NPC Pydantic model and a SQLite-backed NpcRepository.
"""

from __future__ import annotations

import enum
import sqlite3
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from aitown.repos.base import NotFoundError, from_json_text, to_json_text
from aitown.repos.interfaces import NPCRepositoryInterface


class NPCStatus(enum.StrEnum):
    PEACEFUL = "peaceful"
    SLEEPING = "sleeping"
    WORKING = "working"
    UNWELL = "unwell"
    AWFUL = "awful"


class NPC(BaseModel):
    """Persistent NPC state and metadata."""
    id: Optional[str] = None
    player_id: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    prompt: Optional[str] = None
    location_id: Optional[str] = None
    status: str = "peaceful"
    hunger: int = 100
    energy: int = 100
    mood: int = 100
    # inventory is stored as JSON text in DB. Tests expect a mapping of item_id->num
    inventory: dict[str, int] = Field(default_factory=dict)
    long_memory: Optional[str] = None
    is_dead: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class NpcRepository(NPCRepositoryInterface):
    """SQLite-backed repository for NPC objects."""

    def _row_to_npc(self, row: sqlite3.Row) -> NPC:
        """Convert a DB row into an NPC model instance."""
        inv = from_json_text(row["inventory"]) if row["inventory"] is not None else None
        return NPC(
            id=row["id"],
            player_id=row["player_id"],
            name=row["name"],
            gender=row["gender"],
            age=row["age"],
            prompt=row["prompt"],
            location_id=row["location_id"],
            status=row["status"],
            hunger=row["hunger"],
            energy=row["energy"],
            mood=row["mood"],
            inventory=inv,
            long_memory=row["long_memory"],
            is_dead=row["is_dead"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create(self, npc: NPC) -> NPC:
        """Persist a new NPC record and return the model."""
        if not npc.id:
            npc.id = str(uuid.uuid4())
        # serialize inventory mapping to JSON
        inv_text = to_json_text(npc.inventory or {})
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO npc (id, player_id, name, gender, age, prompt, location_id, hunger, energy, mood, inventory, long_memory, is_dead, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                npc.id,
                npc.player_id,
                npc.name,
                npc.gender,
                npc.age,
                npc.prompt,
                npc.location_id,
                npc.hunger,
                npc.energy,
                npc.mood,
                inv_text,
                npc.long_memory,
                npc.is_dead,
                npc.created_at,
                npc.updated_at,
            ),
        )
        self.conn.commit()
        return npc

    def get_by_id(self, id: str) -> NPC:
        """Retrieve an NPC by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM npc WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"NPC not found: {id}")
        return self._row_to_npc(row)

    def list_by_player(self, player_id: str) -> List[NPC]:
        """List NPCs belonging to a player id."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM npc WHERE player_id = ?", (player_id,))
        rows = cur.fetchall()
        return [self._row_to_npc(r) for r in rows]

    def update(self, id: str, patch: dict) -> NPC:
        """Apply a partial patch to an NPC and persist the updated state.

        This implementation loads the NPC, sets attributes from `patch`, and writes back.
        """
        # simple patch implementation: fetch, update fields in memory, write back
        npc = self.get_by_id(id)
        for k, v in patch.items():
            if hasattr(npc, k):
                setattr(npc, k, v)
        inv_text = to_json_text(npc.inventory or {})
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE npc SET player_id=?, name=?, gender=?, age=?, prompt=?, location_id=?, status=?, hunger=?, energy=?, mood=?, inventory=?, long_memory=?, is_dead=?, created_at=?, updated_at=? WHERE id=?",
            (
                npc.player_id,
                npc.name,
                npc.gender,
                npc.age,
                npc.prompt,
                npc.location_id,
                npc.status,
                npc.hunger,
                npc.energy,
                npc.mood,
                inv_text,
                npc.long_memory,
                npc.is_dead,
                npc.created_at,
                npc.updated_at,
                npc.id,
            ),
        )
        self.conn.commit()
        return npc

    def delete(self, id: str) -> None:
        """Delete an NPC by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM npc WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"NPC not found: {id}")
        self.conn.commit()
