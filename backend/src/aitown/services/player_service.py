"""Player service layer: thin wrappers around PlayerRepository.

Provides a minimal service abstraction for creating, fetching and deleting players.
"""
from typing import Optional

from aitown.repos.player_repo import Player, PlayerRepository


class PlayerService:
    """Simple player service that delegates to PlayerRepository."""

    def __init__(self, conn=None):
        self.repo = PlayerRepository(conn)

    def create(self, display_name: str, password_hash: Optional[str] = None, id: Optional[str] = None) -> Player:
        p = Player(id=id, display_name=display_name, password_hash=password_hash)
        return self.repo.create(p)

    def get(self, id: str) -> Player:
        return self.repo.get_by_id(id)

    def delete(self, id: str) -> None:
        return self.repo.delete(id)
