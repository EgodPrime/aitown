"""Player repository and model.

Defines a simple Player model and repository for persistence.
"""

import datetime
import sqlite3
import uuid
from typing import Optional

from pydantic import Field
import time

from aitown.models.player_model import Player
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import PlayerRepositoryInterface


class PlayerRepository(PlayerRepositoryInterface):
    """SQLite-backed repository for Player objects."""

    def create(self, player: Player) -> Player:
        """Persist a Player record and return it."""
        # ensure created_at is set when falsy (tests may pass 0)
        if not player.created_at:
            player.created_at = time.time()
        if not player.id:
            player.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (
                    player.id,
                    player.display_name,
                    player.password_hash,
                    player.created_at,
                ),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return player

    def get_by_id(self, id: str) -> Player:
        """Retrieve a player by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM player WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Player not found: {id}")
        return Player(
            id=row["id"],
            display_name=row["display_name"],
            password_hash=row["password_hash"],
            created_at=row["created_at"],
        )

    def delete(self, id: str) -> None:
        """Delete a player record or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM player WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Player not found: {id}")
        self.conn.commit()
