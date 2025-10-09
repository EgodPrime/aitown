import sqlite3
import datetime
from aitown.helpers.init_db import init_db
from aitown.repos import npc_repo


def test_npc_repo_crud_roundtrip():
    conn = init_db(":memory:")

    # Create a player to reference
    now = datetime.datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute("INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)", ("player:1", "P1", None, now))
    conn.commit()

    NpcRepository = npc_repo.NpcRepository
    NPC = npc_repo.NPC

    repo = NpcRepository(conn)

    npc = NPC(id="npc:1", player_id="player:1", name="Bob", gender="m", age=30, prompt=None, location_id=None)
    npc.inventory = [{"item_id": "item:coin", "num": 5}]
    created = repo.create(npc)
    assert created.id == "npc:1"

    fetched = repo.get_by_id("npc:1")
    assert fetched.name == "Bob"
    assert isinstance(fetched.inventory, list)
    assert fetched.inventory[0]["item_id"] == "item:coin"

    # list_by_player
    lst = repo.list_by_player("player:1")
    assert any(n.id == "npc:1" for n in lst)

    # update
    repo.update("npc:1", {"name": "Bobby"})
    updated = repo.get_by_id("npc:1")
    assert updated.name == "Bobby"

    # delete
    repo.delete("npc:1")
    try:
        repo.get_by_id("npc:1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass

    conn.close()


def test_create_npc_without_id_generates_uuid_and_inventory_none():
    conn = init_db(":memory:")
    # ensure player exists for player_id relation
    cur = conn.cursor()
    cur.execute("INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)", ("p0", "P0", None, "now"))
    conn.commit()
    repo = npc_repo.NpcRepository(conn)
    npc = npc_repo.NPC(id=None, player_id="p0", name="NGen", gender=None, age=None, prompt=None, location_id=None)
    created = repo.create(npc)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "NGen"
    # inventory should be parsed as list (even if None was provided)
    assert isinstance(fetched.inventory, list)
    conn.close()


def test_npc_notfound_delete_additional():
    conn = init_db(":memory:")
    Repo = npc_repo.NpcRepository
    repo = Repo(conn)
    import pytest

    with pytest.raises(Exception):
        repo.get_by_id("missing:npc")
    with pytest.raises(Exception):
        repo.delete("missing:npc")
    conn.close()
