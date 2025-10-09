from dataclasses import dataclass
from typing import Optional, List
import sqlite3
from aitown.repos.base import NotFoundError, to_json_text, from_json_text
from aitown.repos.interfaces import EventRepositoryInterface


@dataclass
class Event:
    id: Optional[int]
    npc_id: Optional[str]
    event_type: str
    payload: dict
    created_at: str
    processed: int = 0
    processed_at: Optional[str] = None


class EventRepository(EventRepositoryInterface):
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def append_event(self, npc_id: Optional[str], event_type: str, payload: dict, created_at: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO event (npc_id, event_type, payload, created_at, processed) VALUES (?, ?, ?, ?, 0)",
            (npc_id, event_type, to_json_text(payload), created_at),
        )
        self.conn.commit()
        return cur.lastrowid

    def fetch_unprocessed(self, limit: int = 100) -> List[Event]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM event WHERE processed = 0 ORDER BY id ASC LIMIT ?", (limit,))
        rows = cur.fetchall()
        events = []
        for r in rows:
            events.append(Event(id=r["id"], npc_id=r["npc_id"], event_type=r["event_type"], payload=from_json_text(r["payload"]) or {}, created_at=r["created_at"], processed=r["processed"], processed_at=r["processed_at"]))
        return events

    def mark_processed(self, event_id: int, processed_at: str) -> None:
        cur = self.conn.cursor()
        cur.execute("UPDATE event SET processed = 1, processed_at = ? WHERE id = ?", (processed_at, event_id))
        self.conn.commit()
