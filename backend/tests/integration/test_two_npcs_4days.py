import json
import time

import pytest

from aitown.helpers.db_helper import init_db
from aitown.kernel.sim_clock import SimClock
from aitown.services.event_service import register_all

from aitown.kernel.npc_actions import ActionExecutor
from aitown.repos.npc_repo import NPC
from aitown.services.npc_service import NPCService, NPC_INSTANCE_LIST
from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.npc_repo import NpcRepository
from aitown.repos.place_repo import PlaceRepository
from aitown.repos.road_repo import RoadRepository
from aitown.repos.town_repo import TownRepository


def _wire_action_executor_repos(conn):
    # Ensure ActionExecutor uses the test DB connection and repo instances
    ActionExecutor.conn = conn
    ActionExecutor.npc_repo = NpcRepository(conn)
    ActionExecutor.item_repo = ActionExecutor.item_repo.__class__(conn)
    ActionExecutor.effect_repo = ActionExecutor.effect_repo.__class__(conn)
    ActionExecutor.place_repo = PlaceRepository(conn)
    ActionExecutor.memory_repo = MemoryEntryRepository(conn)
    ActionExecutor.road_repo = RoadRepository(conn)


def test_two_npcs_live_four_days(monkeypatch):
    # Setup in-memory DB with seed data
    conn = init_db(":memory:", seed=True)

    # Wire ActionExecutor to use our test DB
    _wire_action_executor_repos(conn)

    # Ensure NPC instance list is empty before creating NPCs
    try:
        NPC_INSTANCE_LIST.clear()
    except Exception:
        pass

    # Create a town row so sim clock can set sim_start_time
    town_repo = TownRepository(conn)
    try:
        town_repo.create(type('T', (), {'id': 'town:001', 'name': 'TestTown', 'description': 'x'}))
    except Exception:
        # ignore if already exists
        pass

    # Create two places and a road connecting them
    place_repo = PlaceRepository(conn)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO place (id, name, tags, shop_inventory) VALUES (?,?,?,?)", ("place:home", "Home", '[]', '{}'))
    cur.execute("INSERT OR IGNORE INTO place (id, name, tags, shop_inventory) VALUES (?,?,?,?)", ("place:market", "Market", '[]', '{}'))
    conn.commit()
    road_repo = RoadRepository(conn)
    # Add a road
    cur.execute("INSERT OR IGNORE INTO road (id, from_place, to_place, direction) VALUES (?,?,?,?)", ("road:1", "place:home", "place:market", "both"))
    conn.commit()

    # Create a player for NPC ownership
    cur.execute("INSERT OR IGNORE INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)", ("player:1","P1",None,time.time()))
    conn.commit()

    # Insert an item so buy action can reference it
    cur.execute(
        "INSERT OR IGNORE INTO item (id, name, value, type, effect_ids, description) VALUES (?,?,?,?,?,?)",
        ("item_bread", "Bread", 5, "CONSUMABLE", "[]", "Simple bread"),
    )
    # update market shop_inventory (list of item ids)
    cur.execute("UPDATE place SET shop_inventory = ? WHERE id = ?", (json.dumps(["item_bread"]), "place:market"))
    conn.commit()

    # Patch NPC.generate to return deterministic actions per NPC based on prompt
    # We'll parse npc id from the prompt (it contains 'NPC id: <id>') and return a simple
    # sequence: npc:1 will alternate move->work->idle, npc:2 will alternate idle->move->buy
    sequences = {
        "npc:1": [
            {"action_type": "move", "place_id": "place:market"},
            {"action_type": "work", "duration_hours": 2},
            {"action_type": "idle"},
        ],
        "npc:2": [
            {"action_type": "idle"},
            {"action_type": "move", "place_id": "place:home"},
            {"action_type": "work", "duration_hours": 1},
        ],
    }

    counters = {"npc:1": 0, "npc:2": 0}

    def fake_generate(prompt: str):
        # extract npc id from prompt
        for nid in sequences.keys():
            if f"NPC id: {nid}" in prompt:
                seq = sequences[nid]
                idx = counters[nid] % len(seq)
                counters[nid] += 1
                return json.dumps(seq[idx])
        return json.dumps({"action_type": "idle"})

    monkeypatch.setattr("aitown.repos.npc_repo.generate", fake_generate)

    # Create NPCs via NPCService so NPC_INSTANCE_LIST is populated and callbacks can be registered
    svc = NPCService(conn)
    n1 = NPC(id="npc:1", player_id="player:1", name="Alice", location_id="place:home")
    n2 = NPC(id="npc:2", player_id="player:1", name="Bob", location_id="place:market")
    svc.create(n1)
    svc.create(n2)

    # Create sim clock, register NPC callbacks
    sim_clock = SimClock()
    register_all(sim_clock.event_bus)

    # Start clock (sets town sim start time)
    sim_clock.start()

    # Step the clock for 100 days (100 * 24 = 2400 hours/ticks)
    steps = 100 * 24
    sim_clock.step(steps)

    # After simulation, assert that both NPCs have recorded memories
    mem_repo = MemoryEntryRepository(conn)
    count1 = mem_repo.count_by_npc("npc:1")
    count2 = mem_repo.count_by_npc("npc:2")

    # Basic existence checks
    assert count1 > 0, f"npc:1 had no memories after simulation (count={count1})"
    assert count2 > 0, f"npc:2 had no memories after simulation (count={count2})"

    # Verify sim clock tick count increased as expected
    assert sim_clock.tick_count == steps, f"expected tick_count {steps}, got {sim_clock.tick_count}"

    # Check NPC current state (energy/mood should be in 0..100, location valid)
    repo = NpcRepository(conn)
    fetched1 = repo.get_by_id("npc:1")
    fetched2 = repo.get_by_id("npc:2")

    assert 0 <= fetched1.energy <= 100
    assert 0 <= fetched1.mood <= 100
    assert fetched1.location_id in ("place:home", "place:market")

    assert 0 <= fetched2.energy <= 100
    assert 0 <= fetched2.mood <= 100
    assert fetched2.location_id in ("place:home", "place:market")

    # Check that Event repo has marked some events as processed
    from aitown.repos.event_repo import EventRepository

    ev_repo = EventRepository(conn)
    unprocessed = ev_repo.fetch_unprocessed()
    # after many ticks, we expect the system to have processed some events and left few unprocessed
    assert len(unprocessed) <= 100
