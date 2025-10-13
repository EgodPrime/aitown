"""Event repository and Event model.

Represents queued events and provides a simple repository for persistence.
"""

import json
from typing import List, Optional
import time

from aitown.models.event_model import Event
from aitown.repos.interfaces import RepositoryInterface


class EventRepository(RepositoryInterface[Event]):
    """SQLite-backed repository for Event objects."""

    def get_unprocessed(self, limit: int = 100) -> List[Event]:
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
                    payload=json.dumps(r["payload"]),
                    created_at=r["created_at"],
                    processed=r["processed"],
                    processed_at=r["processed_at"],
                )
            )
        return events

    def mark_processed(self, event_id: int, processed_at: str) -> None:
        """Mark the event row as processed with a timestamp.
        Should be moved to the service layer
        """
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE event SET processed = 1, processed_at = ? WHERE id = ?",
            (processed_at, event_id),
        )
        self.conn.commit()
