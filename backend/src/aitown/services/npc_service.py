"""NPC service layer: wraps NPC repository and provides convenience methods.

This service keeps thin logic around creating/listing/updating NPCs and recording
memories via the existing MemoryEntryRepository.
"""
from typing import List, Optional

from aitown.repos.npc_repo import NpcRepository, NPC
from aitown.repos.memory_repo import MemoryEntryRepository

NPC_INSTANCE_LIST: list[NPC] = []

class NPCService:
    def __init__(self, conn=None):
        self.repo = NpcRepository(conn)

    def create(self, npc: NPC) -> NPC:
        created = self.repo.create(npc)
        # keep an in-memory list of NPC instances for event wiring at startup
        try:
            NPC_INSTANCE_LIST.append(created)
        except Exception:
            pass
        return created

    def get(self, npc_id: str) -> NPC:
        return self.repo.get_by_id(npc_id)

    def list_by_player(self, player_id: str) -> List[NPC]:
        return self.repo.list_by_player(player_id)

    def update(self, npc_id: str, patch: dict) -> NPC:
        return self.repo.update(npc_id, patch)

    def delete(self, npc_id: str) -> None:
        return self.repo.delete(npc_id)

    def record_memory(self, npc_id: str, content: str, memory_repo: MemoryEntryRepository | None = None):
        return self.repo.record_memory(npc_id, memory_repo, content)