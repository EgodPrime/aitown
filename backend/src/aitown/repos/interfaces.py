from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional


class NPCRepositoryInterface(ABC):
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


class PlayerRepositoryInterface(ABC):
    @abstractmethod
    def create(self, player) -> object:
        pass

    @abstractmethod
    def get_by_id(self, id: str):
        pass

    @abstractmethod
    def delete(self, id: str) -> None:
        pass


class PlaceRepositoryInterface(ABC):
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


class EventRepositoryInterface(ABC):
    @abstractmethod
    def append_event(self, npc_id: Optional[str], event_type: str, payload: dict, created_at: str) -> int:
        pass

    @abstractmethod
    def fetch_unprocessed(self, limit: int = 100) -> List[object]:
        pass

    @abstractmethod
    def mark_processed(self, event_id: int, processed_at: str) -> None:
        pass


class TransactionsRepositoryInterface(ABC):
    @abstractmethod
    def append(self, npc_id: Optional[str], item_id: Optional[str], amount: int, reason: Optional[str], created_at: str) -> int:
        pass

    @abstractmethod
    def list_by_npc(self, npc_id: str, limit: int = 100) -> List[object]:
        pass


class ItemRepositoryInterface(ABC):
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


class RoadRepositoryInterface(ABC):
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
