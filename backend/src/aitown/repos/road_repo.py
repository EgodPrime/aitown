"""Road repository and the Road model.

Represents bidirectional connections between places and a repository to persist them.
"""

import uuid
from typing import List, Optional

from pydantic import BaseModel

from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import RoadRepositoryInterface


class Road(BaseModel):
    """A connection between two places used for NPC movement."""
    id: Optional[str] = None
    from_place: str
    to_place: str
    direction: str


class RoadRepository(RoadRepositoryInterface):
    """SQLite-backed repository for Road objects."""

    def create(self, road: Road) -> Road:
        """Insert a Road and return it."""
        if not road.id:
            road.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO road (id, from_place, to_place, direction) VALUES (?, ?, ?, ?)",
            (road.id, road.from_place, road.to_place, road.direction),
        )
        self.conn.commit()
        return road

    def get_by_id(self, id: str) -> Road:
        """Return a Road by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM road WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Road not found: {id}")
        return Road(
            id=row["id"],
            from_place=row["from_place"],
            to_place=row["to_place"],
            direction=row["direction"],
        )

    def list_nearby(self, place_id: str) -> List[Road]:
        """List roads connected to the given place id."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM road WHERE from_place = ? OR to_place = ?",
            (place_id, place_id),
        )
        rows = cur.fetchall()
        return [
            Road(
                id=r["id"],
                from_place=r["from_place"],
                to_place=r["to_place"],
                direction=r["direction"],
            )
            for r in rows
        ]

    def delete(self, id: str) -> None:
        """Delete a road by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM road WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Road not found: {id}")
        self.conn.commit()
