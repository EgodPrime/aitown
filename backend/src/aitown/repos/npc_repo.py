"""NPC model and repository.

Defines the NPC Pydantic model and a SQLite-backed NpcRepository.
"""

from __future__ import annotations

import enum
import sqlite3
import uuid
from typing import List, Optional
from loguru import logger

from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.memory_repo import MemoryEntry
from pydantic import BaseModel, Field
import time

from aitown.repos.base import NotFoundError, from_json_text, to_json_text
from aitown.repos.interfaces import NPCRepositoryInterface
from aitown.helpers.config_helper import get_config
from aitown.helpers.llm_helper import generate
import json
import re
from aitown.repos.event_repo import Event
from aitown.kernel.event_bus import InMemoryEventBus
from aitown.kernel.event_bus import EventType

cfg = get_config("npc")


class NPCStatus(enum.StrEnum):
    PEACEFUL = "peaceful"
    SLEEPING = "sleeping"
    WORKING = "working"
    UNWELL = "unwell"
    AWFUL = "awful"


class NPC(BaseModel):
    """Persistent NPC state and metadata."""
    id: Optional[str] = None
    player_id: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    prompt: Optional[str] = None
    location_id: Optional[str] = None
    status: str = "peaceful"
    hunger: int = 100
    energy: int = 100
    mood: int = 100
    # inventory is stored as JSON text in DB. Tests expect a mapping of item_id->num
    inventory: dict[str, int] = Field(default_factory=dict)
    long_memory: Optional[str] = None
    is_dead: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: Optional[float] = None

    def remember(self, memory_repo: Optional[MemoryEntryRepository], content: str) -> bool:
        """Convenience instance method to record a memory for this NPC."""
        mr = memory_repo
        if mr is None:
            mr = MemoryEntryRepository()

        mem = MemoryEntry(npc_id=self.id, content=content)
        mr.create(mem)

        self.long_memory = (self.long_memory or "") + "\n" + content
        if self.long_memory and len(self.long_memory) > cfg.get("max_long_memory_chars", 8400):
            self.summary_memory()

    def register_decision_callback(self, event_bus: InMemoryEventBus, event: Event) -> None:
        """
        NPC基于自己的信息、记忆、环境等，做出决策，并通过event回调传递给事件总线
        决策应该是json格式，体现为对`npc_actions`中方法的调用，结构为:
        {
            "action_type": "move" | "eat" | ....
            other payload fields...
        }
        """
        # Build a prompt describing the NPC state and ask the LLM to return a JSON
        # object describing an action to take. The JSON MUST contain an
        # "action_type" string and any other fields required by the action.
        prompt = (
            """
# Data
NPC id: %s
name: %s
player_id: %s
location_id: %s
status: %s
long_memory: %s

# Task
Generate a single JSON object describing an action this NPC should take.
The object must contain the key "action_type" whose value is one of the
actions handled by the simulation (e.g. "move", "eat", "sleep", "work",
"buy", "sell", "idle"). 

# Possible actions:
{
    "action_type": "move",
    "npc_id": "<npc_id>",
    "place_id": "<place_id>"
}
{
    "action_type": "eat",
    "npc_id": "<npc_id>",
    "item_id": "<item_id>",
    "item_amount": <amount> # integer
}
{
    "action_type": "sleep",
    "npc_id": "<npc_id>",
    "duration_hours": <hours> # integer
}
{
    "action_type": "work",
    "npc_id": "<npc_id>",
    "duration_hours": <hours> # integer
}
{
    "action_type": "buy",
    "npc_id": "<npc_id>",
    "item_id": "<item_id>",
    "item_amount": <amount> # integer
}
{
    "action_type": "sell",
    "npc_id": "<npc_id>",
    "item_id": "<item_id>",
    "item_amount": <amount> # integer
}
{
    "action_type": "idle",
    "npc_id": "<npc_id>"
}

# Output
Return only the JSON object (no surrounding text). 
"""
            % (
                self.id,
                self.name,
                self.player_id,
                self.location_id,
                self.status,
                (self.long_memory or ""),
            )
        )
        all_ok = True
        resp = generate(prompt)
        if not resp:
            logger.error("NPC.generate returned empty response")
            all_ok = False
            
        if all_ok:
            # Try to extract a JSON object from the response
            try:
                payload = json.loads(resp)
            except Exception:
                logger.warning("NPC.generate returned non-JSON response, trying to extract JSON")
                # attempt to extract the first {...} block
                m = re.search(r"\{[\s\S]*\}", resp)
                if m:
                    try:
                        payload = json.loads(m.group(0))
                    except Exception:
                        logger.error("NPC.generate returned non-JSON response, unable to extract JSON")
                        all_ok = False
                else:
                    logger.error("NPC.generate returned non-JSON response, unable to extract JSON")
                    all_ok = False

        if all_ok:
            # ensure payload includes npc_id for downstream handlers
            if isinstance(payload, dict):
                payload.setdefault("npc_id", self.id)
            evt = Event(event_type=EventType.NPC_ACTION, payload=payload, npc_id=self.id)
        else:
            evt = Event(
                npc_id=self.id,
                event_type=EventType.NPC_ACTION,
                payload={"action_type": "idle", "npc_id": self.id},
            )
        event_bus.publish(evt)


    def summary_memory(self) -> bool:
        """Summarize old memories for this NPC."""
        prompt = f"""
# Data
<long_memory>{self.long_memory}</long_memory>
# Task
`long_memory` is the long-term memory of an NPC character (named {self.name}) in a simulation game.
Please generate a concise summary of the key events and facts from this memory.
# Constraints
- Summary should be no more than 100 words.
- output the summary only wrapped in <summary>...</summary> tags.
- The summary should start with "I am <name>, "
# Output
"""
        summary = generate(prompt)
        if summary:
            self.long_memory = summary
            return True
        return False

class NpcRepository(NPCRepositoryInterface):
    """SQLite-backed repository for NPC objects."""

    def _row_to_npc(self, row: sqlite3.Row) -> NPC:
        """Convert a DB row into an NPC model instance."""
        inv = from_json_text(row["inventory"]) if row["inventory"] is not None else None
        return NPC(
            id=row["id"],
            player_id=row["player_id"],
            name=row["name"],
            gender=row["gender"],
            age=row["age"],
            prompt=row["prompt"],
            location_id=row["location_id"],
            status=row["status"],
            hunger=row["hunger"],
            energy=row["energy"],
            mood=row["mood"],
            inventory=inv,
            long_memory=row["long_memory"],
            is_dead=row["is_dead"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def create(self, npc: NPC) -> NPC:
        """Persist a new NPC record and return the model."""
        # ensure created_at is set when falsy (tests may pass 0)
        if not npc.created_at:
            npc.created_at = time.time()
        if not npc.id:
            npc.id = str(uuid.uuid4())
        # serialize inventory mapping to JSON
        inv_text = to_json_text(npc.inventory or {})
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO npc (id, player_id, name, gender, age, prompt, location_id, hunger, energy, mood, inventory, long_memory, is_dead, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                npc.id,
                npc.player_id,
                npc.name,
                npc.gender,
                npc.age,
                npc.prompt,
                npc.location_id,
                npc.hunger,
                npc.energy,
                npc.mood,
                inv_text,
                npc.long_memory,
                npc.is_dead,
                npc.created_at,
                npc.updated_at,
            ),
        )
        self.conn.commit()
        return npc

    def get_by_id(self, id: str) -> NPC:
        """Retrieve an NPC by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM npc WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"NPC not found: {id}")
        return self._row_to_npc(row)

    def list_by_player(self, player_id: str) -> List[NPC]:
        """List NPCs belonging to a player id."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM npc WHERE player_id = ?", (player_id,))
        rows = cur.fetchall()
        return [self._row_to_npc(r) for r in rows]

    def update(self, id: str, patch: dict) -> NPC:
        """Apply a partial patch to an NPC and persist the updated state.

        This implementation loads the NPC, sets attributes from `patch`, and writes back.
        """
        # simple patch implementation: fetch, update fields in memory, write back
        npc = self.get_by_id(id)
        for k, v in patch.items():
            if hasattr(npc, k):
                setattr(npc, k, v)
        inv_text = to_json_text(npc.inventory or {})
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE npc SET player_id=?, name=?, gender=?, age=?, prompt=?, location_id=?, status=?, hunger=?, energy=?, mood=?, inventory=?, long_memory=?, is_dead=?, created_at=?, updated_at=? WHERE id=?",
            (
                npc.player_id,
                npc.name,
                npc.gender,
                npc.age,
                npc.prompt,
                npc.location_id,
                npc.status,
                npc.hunger,
                npc.energy,
                npc.mood,
                inv_text,
                npc.long_memory,
                npc.is_dead,
                npc.created_at,
                npc.updated_at,
                npc.id,
            ),
        )
        self.conn.commit()
        return npc

    def delete(self, id: str) -> None:
        """Delete an NPC by id or raise NotFoundError."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM npc WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"NPC not found: {id}")
        self.conn.commit()

    # helper to record memory for NPC in repository context
    def record_memory(self, npc_id: str, memory_repo, content: str):
        npc = self.get_by_id(npc_id)
        return npc.remember(memory_repo, content)
