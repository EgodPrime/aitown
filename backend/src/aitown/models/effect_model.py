"""Effect model extracted from repos/effect_repo.py"""
from typing import Optional
from pydantic import BaseModel


class Effect(BaseModel):
    id: Optional[str] = None
    name: str
    attribute: str
    change: int

    def apply_to_npc(self, npc_id: str, factor: int = 1):
        # kept minimal here; behavior remains in repositories/services
        from aitown.repos.npc_repo import NpcRepository

        npc_repo = NpcRepository()
        npc = npc_repo.get_by_id(npc_id)
        match self.attribute:
            case "hunger":
                npc.hunger = max(0, min(100, npc.hunger + self.change * factor))
                npc_repo.update(npc_id, {"hunger": npc.hunger})
            case "energy":
                npc.energy = max(0, min(100, npc.energy + self.change * factor))
                npc_repo.update(npc_id, {"energy": npc.energy})
            case "mood":
                npc.mood = max(0, min(100, npc.mood + self.change * factor))
                npc_repo.update(npc_id, {"mood": npc.mood})
            case _:
                pass