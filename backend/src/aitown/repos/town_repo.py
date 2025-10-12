"""Town repository and model.

Provides a simple Town model and SQLite-backed TownRepository following the
project's repository conventions.
"""

import sqlite3
import uuid
import time
from typing import List, Optional

from pydantic import BaseModel

from aitown.repos.base import ConflictError, NotFoundError
from aitown.repos.interfaces import RepositoryIterface


class Town(BaseModel):
    """Represents a town grouping (meta information)."""

    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    sim_start_time: Optional[float] = None


class TownRepository(RepositoryIterface):
    """SQLite-backed repository for Town objects."""

    def create(self, town: Town) -> Town:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO town (id, name, description) VALUES (?, ?, ?)",
                (town.id, town.name, town.description),
            )
        except sqlite3.IntegrityError as e:
            raise ConflictError(str(e))
        else:
            self.conn.commit()
            return town

    def get_by_id(self, id: str) -> Town:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM town WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Town not found: {id}")
        return Town(id=row["id"], name=row["name"], description=row["description"], created_at=row["created_at"])

    def list_all(self) -> List[Town]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM town")
        rows = cur.fetchall()
        towns: List[Town] = []
        for r in rows:
            towns.append(Town(id=r["id"], name=r["name"], description=r["description"], created_at=r["created_at"]))
        return towns

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM town WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Town not found: {id}")
        self.conn.commit()

    def set_sim_start_time(self, town_id: str, sim_start_time: float) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE town SET sim_start_time = ? WHERE id = ?",
            (sim_start_time, town_id),
        )
        self.conn.commit()

    def get_sim_start_time(self, town_id: str) -> Optional[float]:
        cur = self.conn.cursor()
        cur.execute("SELECT sim_start_time FROM town WHERE id = ?", (town_id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Town not found: {town_id}")
        return row["sim_start_time"]
