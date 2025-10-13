"""Town repository and model.

Provides a simple Town model and SQLite-backed TownRepository following the
project's repository conventions.
"""

import sqlite3
import uuid
import time
from typing import List, Optional

from aitown.models.town_model import Town
from aitown.repos.interfaces import RepositoryInterface


class TownRepository(RepositoryInterface[Town]):
    """SQLite-backed repository for Town objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "town"

    def set_sim_start_time(self, town_id: str, sim_start_time: float) -> None:
        """ This function should be moved to the service layer """
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE town SET sim_start_time = ? WHERE id = ?",
            (sim_start_time, town_id),
        )
        self.conn.commit()

    def get_sim_start_time(self, town_id: str) -> Optional[float]:
        """ This function should be moved to the service layer """
        cur = self.conn.cursor()
        cur.execute("SELECT sim_start_time FROM town WHERE id = ?", (town_id,))
        row = cur.fetchone()
        if not row:
            return None
        return row["sim_start_time"]
