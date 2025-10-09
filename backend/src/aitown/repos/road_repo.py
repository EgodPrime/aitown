from typing import Optional, List
import sqlite3
import uuid
from pydantic import BaseModel
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import RoadRepositoryInterface
from aitown.helpers.db_helper import load_db


class Road(BaseModel):
    id: Optional[str] = None
    from_place: str
    to_place: str
    direction: str


class RoadRepository(RoadRepositoryInterface):

    def create(self, road: Road) -> Road:
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
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM road WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Road not found: {id}")
        return Road(id=row["id"], from_place=row["from_place"], to_place=row["to_place"], direction=row["direction"])

    def list_nearby(self, place_id: str) -> List[Road]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM road WHERE from_place = ? OR to_place = ?", (place_id, place_id))
        rows = cur.fetchall()
        return [Road(id=r["id"], from_place=r["from_place"], to_place=r["to_place"], direction=r["direction"]) for r in rows]

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM road WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Road not found: {id}")
        self.conn.commit()
