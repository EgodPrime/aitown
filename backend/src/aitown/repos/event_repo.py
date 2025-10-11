"""Event repository and Event model.

Represents queued events and provides a simple repository for persistence.
"""

from typing import List, Optional

from pydantic import BaseModel

from aitown.repos.base import from_json_text, to_json_text
from aitown.repos.interfaces import EventRepositoryInterface


class Event(BaseModel):
    """A queued event that will be processed by the event bus."""
    id: Optional[int] = None
    npc_id: Optional[str] = None
    event_type: str
    payload: dict = {}
    created_at: Optional[str] = None
    processed: int = 0
    processed_at: Optional[str] = None


class EventRepository(EventRepositoryInterface):
    """SQLite-backed repository for Event objects."""
    def append_event(self, event: Event) -> int:
        """Append an event to the DB and return the new row id."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO event (event_type, payload, created_at, processed) VALUES (?, ?, ?, 0)",
            (event.event_type, to_json_text(event.payload), event.created_at),
        )
        self.conn.commit()

        return cur.lastrowid

    def fetch_unprocessed(self, limit: int = 100) -> List[Event]:
        """Return up to `limit` unprocessed events ordered by id."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM event WHERE processed = 0 ORDER BY id ASC LIMIT ?", (limit,)
        )
        rows = cur.fetchall()
        events = []
        for r in rows:
            events.append(
                Event(
                    id=r["id"],
                    event_type=r["event_type"],
                    payload=from_json_text(r["payload"]) or {},
                    created_at=r["created_at"],
                    processed=r["processed"],
                    processed_at=r["processed_at"],
                )
            )
        return events

    def mark_processed(self, event_id: int, processed_at: str) -> None:
        """Mark the event row as processed with a timestamp."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE event SET processed = 1, processed_at = ? WHERE id = ?",
            (processed_at, event_id),
        )
        self.conn.commit()
