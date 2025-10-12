from aitown.repos.npc_repo import NPC, NpcRepository
from aitown.services.sim_service import sim_clock
from aitown.kernel.event_bus import EventType

npc_repo = NpcRepository()
NPC_ENTITIES = []

def create_npc(npc_data: dict) -> NPC:
    npc = NPC(
        id=npc_data.get("id"),
        player_id=npc_data.get("player_id"),
        name=npc_data.get("name"),
    )
    npc_repo.create(npc)
    NPC_ENTITIES.append(npc)

    sim_clock.event_bus.subscribe(EventType.NPC_DECISION, lambda evt: None)
    return npc