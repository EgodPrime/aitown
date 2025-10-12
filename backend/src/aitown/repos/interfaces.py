"""Repository interfaces for persistence layer.

Abstract base classes describing repository contracts used across the codebase.
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from typing import List, Optional

from aitown.helpers.db_helper import load_db


class RepositoryIterface(ABC):
    def __init__(self, conn: Optional[sqlite3.Connection]=None):
        self.created = False
        if conn is None:
            conn = load_db()
            self.created = True
        self.conn = conn

        try:
            self.conn.row_factory = sqlite3.Row
        except Exception:
            pass

    def __del__(self):
        if self.created and self.conn:
            try:
                self.conn.close()
            except Exception:  # pragma: no cover
                pass  # pragma: no cover


class NPCRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, npc) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def list_by_player(self, player_id: str) -> List[object]:
        pass

    @abstractmethod
    def update(self, id: str, patch: dict):
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class PlayerRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, player) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class PlaceRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, place) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def list_all(self) -> List[object]:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class EventRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def append_event(
        self, npc_id: Optional[str], event_type: str, payload: dict, created_at: str
    ) -> int:
        pass

    @abstractmethod
    def fetch_unprocessed(self, limit: int = 100) -> List[object]:
        pass

    @abstractmethod
    def mark_processed(self, event_id: int, processed_at: str) -> None:
        pass


class TransactionsRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def append(
        self,
        npc_id: Optional[str],
        item_id: Optional[str],
        amount: int,
        reason: Optional[str],
        created_at: str,
    ) -> int:
        pass

    @abstractmethod
    def list_by_npc(self, npc_id: str, limit: int = 100) -> List[object]:
        pass


class ItemRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, item) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def list_all(self) -> List[object]:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class EffectRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, effect) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class RoadRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, road) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def list_nearby(self, place_id: str) -> List[object]:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class MemoryEntryRepositoryInterface(RepositoryIterface):
    @abstractmethod
    def create(self, memory_entry) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def list_by_npc(
        self, npc_id: str, limit: int = 100
    ) -> List[MemoryEntryRepositoryInterface]:
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass
