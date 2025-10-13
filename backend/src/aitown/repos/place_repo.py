"""Place repository and models.

This module provides the Place Pydantic model and a SQLite-backed PlaceRepository.
"""

import datetime
import enum
import sqlite3
import uuid
from typing import List, Optional

from pydantic import Field
import time

from aitown.models.place_model import Place, PlaceTag
from aitown.repos.base import ConflictError, NotFoundError, from_json_text, to_json_text
from aitown.repos.interfaces import PlaceRepositoryInterface


class PlaceRepository(PlaceRepositoryInterface):
    """SQLite-backed repository for Place objects."""

    def create(self, place: Place) -> Place:
        """Insert a new Place into the DB and return it.

        Raises ConflictError on duplicate id.
        """
        if not place.id:
            place.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        try:
            # leave DB-created created_at to migrations/seed logic; do not supply created_at here
            cur.execute(
                "INSERT INTO place (id, name, tags, shop_inventory) VALUES (?, ?, ?, ?)",
                (
                    place.id,
                    place.name,
                    to_json_text(place.tags),
                    to_json_text(place.shop_inventory),
                ),
            )
        except sqlite3.IntegrityError as e:
            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return place

    def get_by_id(self, id: str) -> Place:
        """Return a Place by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM place WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Place not found: {id}")
        return Place(
            id=row["id"],
            name=row["name"],
            tags=from_json_text(row["tags"]) or [],
            shop_inventory=from_json_text(row["shop_inventory"]) or [],
        )

    def list_all(self) -> List[Place]:
        """List all Place records from the DB."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM place")
        rows = cur.fetchall()
        places = []
        for r in rows:
            places.append(
                Place(
                    id=r["id"],
                    name=r["name"],
                    tags=from_json_text(r["tags"]) or [],
                    shop_inventory=from_json_text(r["shop_inventory"]) or [],
                )
            )
        return places

    def delete(self, id: str) -> None:
        """Delete a Place by id or raise NotFoundError if not present."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM place WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Place not found: {id}")
        self.conn.commit()
