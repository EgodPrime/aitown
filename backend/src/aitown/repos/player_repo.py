from typing import Optional
import sqlite3
import uuid
import datetime
from pydantic import BaseModel
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import PlayerRepositoryInterface
from aitown.helpers.db_helper import load_db


class Player(BaseModel):
    id: Optional[str] = None
    display_name: str
    password_hash: Optional[str] = None
    created_at: Optional[str] = None


class PlayerRepository(PlayerRepositoryInterface):


    def create(self, player: Player) -> Player:
        if not player.id:
            player.id = str(uuid.uuid4())
        if not player.created_at:
            player.created_at = datetime.datetime.now().isoformat()
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (player.id, player.display_name, player.password_hash, player.created_at),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return player

    def get_by_id(self, id: str) -> Player:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM player WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Player not found: {id}")
        return Player(id=row["id"], display_name=row["display_name"], password_hash=row["password_hash"], created_at=row["created_at"])

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM player WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Player not found: {id}")
        self.conn.commit()
