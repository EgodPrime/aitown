import datetime
import time

from aitown.helpers.db_helper import init_db
from aitown.repos import npc_repo


def test_npc_repo_crud_roundtrip():
    conn = init_db(":memory:")

    # Create a player to reference
    now = datetime.datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("player:1", "P1", None, now),
    )
    conn.commit()

    NpcRepository = npc_repo.NpcRepository
    NPC = npc_repo.NPC

    repo = NpcRepository(conn)

    npc = NPC(
        id="npc:1",
        player_id="player:1",
        name="Bob",
        gender="m",
        age=30,
        prompt=None,
        location_id=None,
    )
    # inventory is a mapping of item_id -> quantity
    npc.inventory = {"item:coin": 5}
    created = repo.create(npc)
    assert created.id == "npc:1"

    fetched = repo.get_by_id("npc:1")
    assert fetched.name == "Bob"
    assert isinstance(fetched.inventory, dict)
    assert fetched.inventory.get("item:coin") == 5

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


def test_remember_uses_module_memory_repo_and_summary_false(monkeypatch):
    # Replace the MemoryEntryRepository class in the npc_repo module with a simple fake
    created = []

    class FakeMemRepo:
        def __init__(self):
            pass

        def create(self, mem):
            created.append(mem)

    monkeypatch.setattr("aitown.repos.npc_repo.MemoryEntryRepository", FakeMemRepo)

    # Use an NPC instance directly and call remember with None to trigger module-level instantiation
    npc = npc_repo.NPC(id="npc:fake", player_id=None, name="Fake")
    npc.remember(None, "an event")
    assert len(created) == 1

    # Now ensure summary_memory returns False when generate returns empty string
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: "")
    npc.long_memory = "x" * 9001
    assert npc.summary_memory() is False


def test_remember_with_none_and_explicit_repo(monkeypatch):
    calls = []

    class FakeMemRepo2:
        def __init__(self, conn=None):
            pass

        def create(self, mem):
            calls.append(mem)

    # monkeypatch module-level MemoryEntryRepository
    monkeypatch.setattr("aitown.repos.npc_repo.MemoryEntryRepository", FakeMemRepo2)

    npc = npc_repo.NPC(id="npc:both", name="B")
    # call remember without repo -> should instantiate FakeMemRepo2
    npc.remember(None, "one")
    # call remember with explicit repo instance
    r = FakeMemRepo2()
    npc.remember(r, "two")
    assert len(calls) >= 1


def test_create_npc_without_id_generates_uuid_and_inventory_none():
    conn = init_db(":memory:")
    # ensure player exists for player_id relation
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)",
        ("p0", "P0", None, "now"),
    )
    conn.commit()
    repo = npc_repo.NpcRepository(conn)
    npc = npc_repo.NPC(
        id=None,
        player_id="p0",
        name="NGen",
        gender=None,
        age=None,
        prompt=None,
        location_id=None,
    )
    created = repo.create(npc)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "NGen"
    # inventory should be a dict mapping even if None was provided
    assert isinstance(fetched.inventory, dict)
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


def test_row_to_npc_inventory_none_and_json():
    conn = init_db(":memory:")
    # create player
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)",
        ("player:1", "P1", None, "now"),
    )
    conn.commit()

    repo = npc_repo.NpcRepository(conn)

    # Insert raw row with inventory NULL
    cur.execute(
        "INSERT INTO npc (id, player_id, name, created_at) VALUES (?,?,?,?)",
        ("npc:row1", "player:1", "R1", time.time()),
    )
    conn.commit()

    n1 = repo.get_by_id("npc:row1")
    assert isinstance(n1.inventory, dict)

    # insert an npc with JSON inventory
    import json

    inv_text = json.dumps({"item:1": 2}, ensure_ascii=False)
    cur.execute(
        "INSERT INTO npc (id, player_id, name, inventory, created_at) VALUES (?,?,?,?,?)",
        ("npc:row2", "player:1", "R2", inv_text, time.time()),
    )
    conn.commit()

    n2 = repo.get_by_id("npc:row2")
    assert isinstance(n2.inventory, dict)
    assert n2.inventory.get("item:1") == 2

    conn.close()


def test_create_npc_with_zero_created_at_sets_time():
    conn = init_db(":memory:")
    cur = conn.cursor()
    cur.execute("INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)", ("player:1","P1",None,time.time()))
    conn.commit()

    repo = npc_repo.NpcRepository(conn)
    npc = npc_repo.NPC(id="npc:z", player_id="player:1", name="Z")
    created = repo.create(npc)
    assert created.created_at != 0
    conn.close()


def test_npc_remember_and_summary_memory(monkeypatch):
    # Ensure generate returns a summary so summary_memory sets long_memory
    # npc_repo imports generate at module import time, patch that symbol
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: "<summary>I am Bob, short</summary>")

    conn = init_db(":memory:")
    # make a player and npc
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO player (id, display_name, password_hash, created_at) VALUES (?,?,?,?)",
        ("player:1", "P1", None, "now"),
    )
    conn.commit()

    repo = npc_repo.NpcRepository(conn)
    npc = npc_repo.NPC(id="npc:mem", player_id="player:1", name="Bob")
    repo.create(npc)

    # call remember passing an explicit memory repo to avoid creating repos with None
    from aitown.repos.memory_repo import MemoryEntryRepository

    mem_repo = MemoryEntryRepository(conn)
    result = repo.record_memory("npc:mem", mem_repo, "an event happened")
    # Verify memory repo has an entry for npc:mem
    assert mem_repo.count_by_npc("npc:mem") >= 1

    # fetch npc and set long_memory long enough to trigger summary
    fetched = repo.get_by_id("npc:mem")
    fetched.long_memory = "x" * 9000
    ok = fetched.summary_memory()
    assert ok is True
    assert fetched.long_memory.startswith("<summary>")
    conn.close()


def test_remember_triggers_summary_when_long(monkeypatch):
    # monkeypatch MemoryEntryRepository to a fake using an in-memory DB returned by load_db
    created = []

    class FakeMemRepo3:
        def __init__(self, conn=None):
            pass

        def create(self, mem):
            created.append(mem)

    monkeypatch.setattr("aitown.repos.npc_repo.MemoryEntryRepository", FakeMemRepo3)
    # ensure generate returns a summary so summary_memory() will set long_memory
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: "<summary>I am X</summary>")

    npc = npc_repo.NPC(id="npc:long", name="Long")
    npc.long_memory = "x" * 9001
    # call remember with None so it will create FakeMemRepo3 and then call summary
    npc.remember(None, "event")
    # after remember, summary should have been applied (long_memory replaced by summary)
    assert npc.long_memory.startswith("<summary>")
