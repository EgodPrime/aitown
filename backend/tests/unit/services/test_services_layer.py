import time

from aitown.helpers.db_helper import init_db
from aitown.services.player_service import PlayerService
from aitown.services.npc_service import NPCService
from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.npc_repo import NPC


def test_player_service_create_get_delete():
    conn = init_db(":memory:")
    ps = PlayerService(conn)

    p = ps.create("Tester", password_hash=None, id="player:srv1")
    assert p.id == "player:srv1"

    fetched = ps.get("player:srv1")
    assert fetched.display_name == "Tester"

    ps.delete("player:srv1")
    try:
        ps.get("player:srv1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass


def test_npc_service_create():
    conn = init_db(":memory:")
    ps = PlayerService(conn)
    ns = NPCService(conn)

    # create player and npc
    ps.create("Owner", id="player:owner")
    npc = NPC(id="npc:srv1", player_id="player:owner", name="Servant")
    ns.create(npc)

    conn.close()
