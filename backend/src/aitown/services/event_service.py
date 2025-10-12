"""Event wiring service.

This module provides a small helper to register NPC callbacks with an
InMemoryEventBus at system startup. It reads the live `NPC_INSTANCE_LIST`
exposed by `npc_service` and registers each NPC instance's callbacks for
memory and decision events.
"""
from typing import Iterable

from aitown.kernel.event_bus import EventType, InMemoryEventBus
from aitown.services.npc_service import NPC_INSTANCE_LIST


class EventService:
    @staticmethod
    def register_all(event_bus: InMemoryEventBus) -> None:
        """Register callbacks for every NPC in NPC_INSTANCE_LIST.

        event_bus must implement `subscribe(event_type, callback)`.
        """
        if not hasattr(event_bus, "subscribe"):
            raise ValueError("event_bus does not expose subscribe(event_type, callback)")

        for npc in list(NPC_INSTANCE_LIST):
            # register decision callback
            try:
                event_bus.subscribe(EventType.NPC_DECISION, npc.register_decision_callback)
            except Exception:
                pass


def register_all(event_bus: InMemoryEventBus) -> None:
    """Convenience wrapper for procedural startup scripts."""
    EventService.register_all(event_bus)
