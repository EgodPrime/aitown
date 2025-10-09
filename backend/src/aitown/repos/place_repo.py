from typing import Optional, List
import sqlite3
import uuid
import datetime
from pydantic import BaseModel, Field
from aitown.repos.base import NotFoundError, from_json_text, to_json_text, ConflictError
from aitown.repos.interfaces import PlaceRepositoryInterface
from aitown.helpers.db_helper import load_db


class Place(BaseModel):
    id: Optional[str] = None
    name: str
    tags: List[str] = []
    shop_inventory: List[str] = []
    created_at: Optional[str] = None


class PlaceRepository(PlaceRepositoryInterface):

    def create(self, place: Place) -> Place:
        if not place.id:
            place.id = str(uuid.uuid4())
        if not place.created_at:
            place.created_at = datetime.datetime.now().isoformat()
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO place (id, name, tags, shop_inventory, created_at) VALUES (?, ?, ?, ?, ?)",
                (place.id, place.name, to_json_text(place.tags), to_json_text(place.shop_inventory), place.created_at),
            )
        except sqlite3.IntegrityError as e:
            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return place

    def get_by_id(self, id: str) -> Place:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM place WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Place not found: {id}")
        return Place(id=row["id"], name=row["name"], tags=from_json_text(row["tags"]) or [], shop_inventory=from_json_text(row["shop_inventory"]) or [], created_at=row["created_at"])

    def list_all(self) -> List[Place]:
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
                    created_at=r["created_at"],
                )
            )
        return places

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM place WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Place not found: {id}")
        self.conn.commit()
