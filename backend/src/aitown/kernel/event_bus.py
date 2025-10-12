import enum
import time
from datetime import datetime
from typing import Callable, Dict, Iterator, List

from aitown.repos.event_repo import Event, EventRepository


class EventType(enum.StrEnum):
    NPC_DECISION = "NPC_DECISION" # 由EVENT_BUS创建，NPC消费 (1 producer : n consumers)
    NPC_ACTION = "NPC_ACTION" # 由NPC创建，EVENT_BUS传递，ActionExecutor消费 (n producers : 1 consumer)
    NPC_MEMORY = "NPC_MEMORY" # 由EVENT_BUS创建，NPC消费 (1 producer : n consumers)


class InMemoryEventBus:
    """Minimal event bus used for tests and local wiring.

    Stores published Event instances in a list and calls optional subscriber callbacks.
    Also exposes a simple drain method to consume events by type.
    """

    def __init__(self):
        self.events: List[Event] = []
        self.event_repo: EventRepository = EventRepository(None)
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def publish(self, event: Event) -> None:
        """
        Publish an Event instance into the bus.
        """
        # ensure created_at exists (use numeric timestamp)
        if not event.created_at:
            event.created_at = time.time()
        self.events.append(event)
        # persist to database
        event.id = self.event_repo.append_event(event)

    def subscribe(self, event_type: str, callback: Callable[[Event], None]) -> None:
        """Subscribe a callback function to an event type."""
        self.subscribers.setdefault(event_type, []).append(callback)

    def drain(self, event_type: str) -> List[Event]:
        matched = [evt for evt in self.events if evt.event_type == event_type]
        return matched

    def drainI(self, event_type: str) -> Iterator[Event]:
        for evt in self.events:
            if evt.event_type == event_type:
                yield evt

    def pre_tick(self) -> None:
        for evt in self.drainI(EventType.NPC_ACTION):
            for cb in self.subscribers.get(EventType.NPC_ACTION, []):
                cb(evt)

    def on_tick(self) -> None:
        """
        Processes events on each tick by persisting processed events to the database and removing them from the event list.
        """
        # 已处理的事件进行数据库持久化
        processed_events = [evt for evt in self.events if evt.processed == 1]
        for evt in processed_events:
            self.event_repo.mark_processed(evt.id, time.time())
        # 删除已处理的事件
        self.events = [evt for evt in self.events if evt.processed == 0]

    def post_tick(self) -> None:
        # First, process NPC_MEMORY events so memories are recorded before NPC decisions
        evt = Event(
            event_type=EventType.NPC_MEMORY, created_at=time.time()
        )
        for cb in self.subscribers.get(EventType.NPC_MEMORY, []):
            cb(evt)
        # Then process NPC_DECISION events to potentially generate new actions
        evt = Event(
            event_type=EventType.NPC_DECISION, created_at=time.time()
        )
        for cb in self.subscribers.get(EventType.NPC_DECISION, []):
            cb(evt)

