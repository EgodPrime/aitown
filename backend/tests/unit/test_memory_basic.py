import sqlite3
import datetime
import pytest
from aitown.repos.memory_repo import MemoryEntry, MemoryEntryRepository
from aitown.repos.npc_repo import NPC, NpcRepository
from aitown.repos.player_repo import Player, PlayerRepository
from aitown.helpers.db_helper import init_db
from aitown.repos.base import NotFoundError, ConflictError


def make_conn():
    # Create an in-memory DB and initialize schema
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_create_and_get_by_id_sets_defaults_and_returns():
    conn = make_conn()
    repo = MemoryEntryRepository(conn)
    npc_repo = NpcRepository(conn)
    player_repo = PlayerRepository(conn)

    # First create a Player to satisfy foreign key constraint
    player = Player(id="player:1", display_name="Test Player")
    player_repo.create(player)

    # create an NPC to satisfy foreign key constraint
    npc = NPC(id="npc:1", player_id="player:1", name="Test NPC")
    npc_repo.create(npc)

    # create without created_at
    entry = MemoryEntry(npc_id="npc:1", content="hello world")
    created = repo.create(entry)

    assert created.id is not None
    assert created.npc_id == "npc:1"
    assert created.content == "hello world"
    assert created.created_at is not None

    # fetch by id
    fetched = repo.get_by_id(created.id)
    assert fetched.id == created.id
    assert fetched.npc_id == created.npc_id
    assert fetched.content == created.content
    assert fetched.created_at == created.created_at
    conn.close()


def test_get_by_id_not_found_raises():
    conn = make_conn()
    repo = MemoryEntryRepository(conn)

    with pytest.raises(NotFoundError):
        repo.get_by_id(9999)
    conn.close()


def test_list_by_npc_order_and_limit():
    conn = make_conn()
    repo = MemoryEntryRepository(conn)
    npc_repo = NpcRepository(conn)
    player_repo = PlayerRepository(conn)

    # First create a Player to satisfy foreign key constraint
    player = Player(id="player:1", display_name="Test Player")
    player_repo.create(player)

    # create an NPC to satisfy foreign key constraint
    npc = NPC(id="npc:A", player_id="player:1", name="Test NPC A")
    npc_repo.create(npc)

    # insert several entries with different created_at
    now = datetime.datetime.now()
    for i in range(5):
        ent = MemoryEntry(npc_id="npc:A", content=f"msg {i}", created_at=(now - datetime.timedelta(minutes=i)).isoformat())
        repo.create(ent)

    # list should be ordered by created_at DESC
    results = repo.list_by_npc("npc:A", limit=3)
    assert len(results) == 3
    # newest first -> msg 0,1,2
    assert results[0].content == "msg 0"
    assert results[1].content == "msg 1"
    assert results[2].content == "msg 2"
    conn.close()


def test_delete_existing_and_missing():
    conn = make_conn()
    repo = MemoryEntryRepository(conn)
    npc_repo = NpcRepository(conn)
    player_repo = PlayerRepository(conn)

    # First create a Player to satisfy foreign key constraint
    player = Player(id="player:1", display_name="Test Player")
    player_repo.create(player)
    # create an NPC to satisfy foreign key constraint
    npc = NPC(id="npc:del", player_id="player:1", name="Test NPC Del")
    npc_repo.create(npc)

    ent = MemoryEntry(npc_id="npc:del", content="to be deleted")
    saved = repo.create(ent)

    # delete should not raise
    repo.delete(saved.id)

    # now deleting again should raise NotFoundError
    with pytest.raises(NotFoundError):
        repo.delete(saved.id)
    conn.close()


def test_create_conflict_raises():
    # Attempt to create a memory entry referencing a non-existent NPC to
    # trigger sqlite3.IntegrityError -> ConflictError in the repo.
    conn = make_conn()
    repo = MemoryEntryRepository(conn)

    # do NOT create the NPC; using npc id that doesn't exist should fail
    entry = MemoryEntry(npc_id="npc:missing", content="x")

    with pytest.raises(ConflictError):
        repo.create(entry)
    conn.close()
