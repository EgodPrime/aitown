"""NPC model extracted from repos/npc_repo.py"""
from typing import Optional
from pydantic import BaseModel, Field
import enum
import time


class NPCStatus(enum.StrEnum):
    PEACEFUL = "peaceful"
    SLEEPING = "sleeping"
    WORKING = "working"
    UNWELL = "unwell"
    AWFUL = "awful"


class NPC(BaseModel):
    id: Optional[int] = None
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
    inventory: dict[str, int] = Field(default_factory=dict)
    long_memory: Optional[str] = None
    is_dead: int = 0
    created_at: float = Field(default_factory=time.time)
    updated_at: Optional[float] = None

    def remember(self, memory_repo, content: str) -> bool:
        mr = memory_repo
        if mr is None:
            from aitown.repos.memory_repo import MemoryEntryRepository

            mr = MemoryEntryRepository()

        from aitown.repos.memory_repo import MemoryEntry

        mem = MemoryEntry(npc_id=self.id, content=content)
        mr.create(mem)

        self.long_memory = (self.long_memory or "") + "\n" + content
        # do not import config at module import time here
        try:
            from aitown.helpers.config_helper import get_config

            cfg = get_config("npc")
            if self.long_memory and len(self.long_memory) > cfg.get("max_long_memory_chars", 8400):
                self.summary_memory()
        except Exception:
            pass

    def register_decision_callback(self, event_bus, event):
        # original logic depends on LLM and services; keep simple delegation
        from aitown.helpers.llm_helper import generate
        import json
        import re
        from loguru import logger

        prompt = f"NPC id: {self.id}\nname: {self.name}\n"  # shortened
        all_ok = True
        resp = generate(prompt)
        if not resp:
            logger.error("NPC.generate returned empty response")
            all_ok = False

        if all_ok:
            try:
                payload = json.loads(resp)
            except Exception:
                m = re.search(r"\{[\s\S]*\}", resp or "")
                if m:
                    try:
                        payload = json.loads(m.group(0))
                    except Exception:
                        all_ok = False
                else:
                    all_ok = False

        if all_ok:
            if isinstance(payload, dict):
                payload.setdefault("npc_id", self.id)
            from aitown.models.event_model import Event

            evt = Event(event_type="NPC_ACTION", payload=payload, npc_id=self.id)
        else:
            from aitown.models.event_model import Event

            evt = Event(npc_id=self.id, event_type="NPC_ACTION", payload={"action_type": "idle", "npc_id": self.id})
        event_bus.publish(evt)

    def summary_memory(self) -> bool:
        from aitown.helpers.llm_helper import generate

        prompt = f"<long_memory>{self.long_memory}</long_memory>"
        summary = generate(prompt)
        if summary:
            self.long_memory = summary
            return True
        return False
