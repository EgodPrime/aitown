import pytest

import aitown.kernel.event_bus as event_bus_module
import aitown.kernel.npc_actions as npc_actions_module
import aitown.repos.effect_repo as effect_repo_module
from aitown.helpers.db_helper import init_db
from aitown.kernel.event_bus import EventType
from aitown.kernel.npc_actions import ActionExecutor
from aitown.kernel.sim_clock import SimClock
from aitown.repos.base import from_json_text
from aitown.repos.effect_repo import Effect, EffectRepository
from aitown.repos.event_repo import Event, EventRepository
from aitown.repos.item_repo import Item, ItemRepository, ItemType
from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.npc_repo import NPC, NpcRepository
from aitown.repos.place_repo import Place, PlaceRepository, PlaceTag
from aitown.repos.road_repo import Road, RoadRepository


@pytest.mark.integration
def test_npc_action_sequence_end_to_end(monkeypatch):
    conn = init_db(":memory:")
    npc_repo = NpcRepository(conn)
    item_repo = ItemRepository(conn)
    effect_repo = EffectRepository(conn)
    place_repo = PlaceRepository(conn)
    memory_repo = MemoryEntryRepository(conn)
    road_repo = RoadRepository(conn)
    event_repo = EventRepository(conn)

    class PatchedPlaceRepository:
        def __init__(self, *args, **kwargs):
            self._repo = place_repo

        def get_by_id(self, place_id: str) -> Place:
            return place_repo.get_by_id(place_id)

    monkeypatch.setattr(npc_actions_module, "PlaceRepository", PatchedPlaceRepository)
    monkeypatch.setattr(effect_repo_module, "NpcRepository", lambda: npc_repo)
    monkeypatch.setattr(
        event_bus_module,
        "EventRepository",
        lambda *_args, **_kwargs: EventRepository(conn),
    )

    original_conn = ActionExecutor.conn
    original_npc_repo = ActionExecutor.npc_repo
    original_item_repo = ActionExecutor.item_repo
    original_effect_repo = ActionExecutor.effect_repo
    original_place_repo = ActionExecutor.place_repo
    original_memory_repo = ActionExecutor.memory_repo
    original_road_repo = ActionExecutor.road_repo

    ActionExecutor.conn = conn
    ActionExecutor.npc_repo = npc_repo
    ActionExecutor.item_repo = item_repo
    ActionExecutor.effect_repo = effect_repo
    ActionExecutor.place_repo = place_repo
    ActionExecutor.memory_repo = memory_repo
    ActionExecutor.road_repo = road_repo

    place_repo.create(Place(id="place:home", name="Home", tags=[PlaceTag.HOUSE.value]))
    place_repo.create(
        Place(id="place:work", name="Workshop", tags=[PlaceTag.WORKABLE.value])
    )
    road_repo.create(
        Road(
            id="road:home-work",
            from_place="place:home",
            to_place="place:work",
            direction="two-way",
        )
    )

    effect_repo.create(
        Effect(
            id="effect:energy_boost", name="Energy Boost", attribute="energy", change=15
        )
    )
    effect_repo.create(
        Effect(id="effect:mood_boost", name="Mood Boost", attribute="mood", change=5)
    )
    item_repo.create(
        Item(
            id="item:snack",
            name="Snack",
            value=5,
            type=ItemType.CONSUMABLE,
            effect_ids=["effect:energy_boost", "effect:mood_boost"],
        )
    )

    npc_repo.create(
        NPC(
            id="npc:hero",
            name="Hero",
            location_id="place:home",
            hunger=30,
            energy=40,
            mood=50,
            inventory={"item:snack": 1},
        )
    )

    clock = SimClock()
    clock.event_bus.event_repo = event_repo

    def publish_and_tick(action_type: str, **kwargs) -> None:
        payload = {"action_type": action_type, "npc_id": "npc:hero"}
        payload.update(kwargs)
        clock.event_bus.publish(
            Event(event_type=EventType.NPC_ACTION, payload=payload, npc_id="npc:hero")
        )
        clock.step()

    try:
        publish_and_tick("move", place_id="place:work")
        publish_and_tick("work", duration_hours=1)
        publish_and_tick("move", place_id="place:home")
        publish_and_tick("sleep", duration_hours=1)
        publish_and_tick("eat", item_id="item:snack", item_amount=1)
    finally:
        ActionExecutor.conn = original_conn
        ActionExecutor.npc_repo = original_npc_repo
        ActionExecutor.item_repo = original_item_repo
        ActionExecutor.effect_repo = original_effect_repo
        ActionExecutor.place_repo = original_place_repo
        ActionExecutor.memory_repo = original_memory_repo
        ActionExecutor.road_repo = original_road_repo

    updated = npc_repo.get_by_id("npc:hero")
    assert updated.location_id == "place:home"
    assert updated.energy == 57
    assert updated.mood == 56
    assert updated.inventory.get("item_silver_coin") == 2
    assert "item:snack" not in updated.inventory
    assert len(memory_repo.list_by_npc("npc:hero")) == 5

    cur = conn.cursor()
    cur.execute("SELECT payload, processed FROM event ORDER BY id ASC")
    rows = cur.fetchall()
    assert len(rows) == 5
    assert all(row["processed"] == 1 for row in rows)
    recorded_actions = [
        from_json_text(row["payload"]).get("action_type") for row in rows
    ]
    assert recorded_actions == ["move", "work", "move", "sleep", "eat"]

    assert EventRepository(conn).fetch_unprocessed() == []

    conn.close()
