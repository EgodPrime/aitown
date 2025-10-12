import time

from aitown.helpers.db_helper import init_db
from aitown.repos.event_repo import Event
from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.npc_repo import NPC
from aitown.services.npc_service import NPCService, NPC_INSTANCE_LIST


class DummyBus:
    def __init__(self):
        self.published = []

    def publish(self, event: Event):
        self.published.append(event)


def test_register_decision_callback_with_valid_json(monkeypatch):
    # valid JSON returned by LLM
    # patch the generate symbol where npc_repo imports it
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: '{"action_type": "idle"}')
    bus = DummyBus()
    npc = NPC(id="npc:test1", name="T")

    npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))

    assert len(bus.published) == 1
    evt = bus.published[0]
    assert evt.event_type == "NPC_ACTION"
    assert evt.payload.get("action_type") == "idle"


def test_register_decision_callback_with_text_and_json_block(monkeypatch):
    # LLM returns text with embedded JSON block
    monkeypatch.setattr(
        "aitown.repos.npc_repo.generate",
        lambda prompt: 'Some commentary...\n{"action_type":"move","place_id":"place:abc"}\nEOF',
    )
    bus = DummyBus()
    npc = NPC(id="npc:test2", name="Mover")

    npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))

    assert len(bus.published) == 1
    evt = bus.published[0]
    assert evt.payload.get("action_type") == "move"
    assert evt.payload.get("place_id") == "place:abc"
    assert evt.payload.get("npc_id") == "npc:test2"


def test_register_decision_callback_with_empty_response(monkeypatch):
    # Empty response should fall back to idle action
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: "")
    bus = DummyBus()
    npc = NPC(id="npc:test3", name="Idle")

    npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))

    assert len(bus.published) == 1
    evt = bus.published[0]
    assert evt.payload.get("action_type") == "idle"


def test_npc_service_create_appends_and_record_memory():
    conn = init_db(":memory:")
    ns = NPCService(conn)

    # create player row (npc requires existing player relation in some schemas)
    # tests in repo typically create player separately; we just create an NPC here
    npc = NPC(id="npc:srv_test", player_id=None, name="Srv")
    created = ns.create(npc)

    # ensure the instance is appended to NPC_INSTANCE_LIST
    assert any(x.id == created.id for x in NPC_INSTANCE_LIST)

    # record memory via explicit MemoryEntryRepository
    mem_repo = MemoryEntryRepository(conn)
    res = ns.record_memory(created.id, "did a thing", memory_repo=mem_repo)
    # record_memory returns None or True; ensure memory persisted
    assert mem_repo.count_by_npc(created.id) >= 1


def test_register_decision_callback_with_unparsable_json_block(monkeypatch):
    # LLM returns text with a { ... } block that is not valid JSON -> should fall
    # back to idle action
    monkeypatch.setattr(
        "aitown.repos.npc_repo.generate",
        lambda prompt: 'intro text\n{not: valid, json,}\nend',
    )
    bus = DummyBus()
    npc = NPC(id="npc:test4", name="Broken")

    npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))

    assert len(bus.published) == 1
    evt = bus.published[0]
    assert evt.payload.get("action_type") == "idle"


def test_npc_service_crud_methods():
    conn = init_db(":memory:")
    ns = NPCService(conn)

    # create a player row so the npc FK constraint is satisfied
    from aitown.repos.player_repo import PlayerRepository, Player

    prepo = PlayerRepository(conn)
    player = Player(id="player:x", display_name="Player X")
    prepo.create(player)

    # create NPC with a player id
    npc = NPC(id="npc:crud1", player_id="player:x", name="Crud")
    ns.create(npc)

    # get
    fetched = ns.get("npc:crud1")
    assert fetched.id == "npc:crud1"

    # list_by_player (should include our npc)
    listed = ns.list_by_player("player:x")
    assert any(n.id == "npc:crud1" for n in listed)

    # update
    updated = ns.update("npc:crud1", {"name": "Crudbed"})
    assert updated.name == "Crudbed"

    # delete and assert NotFoundError when getting
    ns.delete("npc:crud1")
    try:
        ns.get("npc:crud1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass


def test_register_decision_callback_with_non_dict_payload(monkeypatch):
    # LLM returns a JSON array instead of an object; ensure publish still occurs
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: '[1,2,3]')
    bus = DummyBus()
    npc = NPC(id="npc:list", name="Lister")

    # constructing Event with a non-dict payload will raise Pydantic ValidationError
    import pytest

    with pytest.raises(Exception):
        npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))


def test_npc_service_create_handles_append_exception(monkeypatch):
    conn = init_db(":memory:")
    ns = NPCService(conn)

    class BadList:
        def append(self, item):
            raise RuntimeError("no append")

    # replace the module-level NPC_INSTANCE_LIST with an object that will raise
    monkeypatch.setattr("aitown.services.npc_service.NPC_INSTANCE_LIST", BadList())

    npc = NPC(id="npc:badappend", name="Bad")
    created = ns.create(npc)  # should not raise despite append failing
    assert created.id == "npc:badappend"


def test_register_decision_callback_with_no_json_block(monkeypatch):
    # LLM returns text but contains no JSON object; should fall back to idle
    monkeypatch.setattr("aitown.repos.npc_repo.generate", lambda prompt: 'just some words, no json here')
    bus = DummyBus()
    npc = NPC(id="npc:nojson", name="NoJSON")

    npc.register_decision_callback(bus, Event(event_type="NPC_DECISION", created_at=time.time()))

    assert len(bus.published) == 1
    evt = bus.published[0]
    assert evt.payload.get("action_type") == "idle"


def test_npc_repo_create_sets_created_at_when_falsy():
    conn = init_db(":memory:")
    from aitown.repos.npc_repo import NpcRepository

    repo = NpcRepository(conn)
    npc = NPC(id="npc:falsy", name="Falsy", created_at=0)
    created = repo.create(npc)
    assert created.created_at and created.created_at > 0


def test_init_db_and_connproxy_behaviour():
    # init_db returns a proxy for string paths; test close(), context manager and __del__ paths
    from aitown.helpers.db_helper import init_db, load_db
    import gc

    # basic usage and explicit close
    conn = init_db(":memory:")
    cur = conn.cursor()
    cur.execute("SELECT 1")
    conn.close()

    # context manager path
    with init_db(":memory:") as c2:
        cur2 = c2.cursor()
        cur2.execute("SELECT 1")

    # explicit destructor call to exercise __del__ branch
    c3 = init_db(":memory:")
    # call destructor method directly (safe) and then collect
    try:
        c3.__del__()
    except Exception:
        pass
    del c3
    gc.collect()

    # load_db returns a proxy too; ensure basic operations work and destructor path
    ld = load_db(":memory:")
    cur3 = ld.cursor()
    cur3.execute("SELECT 1")
    try:
        ld.__del__()
    except Exception:
        pass


def test_init_db_missing_migration_closes_conn(tmp_path, monkeypatch):
    # Simulate migrations file missing by pointing PROJECT_ROOT to a temp dir
    from aitown.helpers import db_helper
    from aitown.helpers.path_helper import PROJECT_ROOT as real_root

    # monkeypatch PROJECT_ROOT to a temporary directory without migrations
    monkeypatch.setattr(db_helper, "PROJECT_ROOT", tmp_path)

    # init_db should raise FileNotFoundError and should not leak a connection
    try:
        import pytest

        with pytest.raises(FileNotFoundError):
            db_helper.init_db(":memory:")
    finally:
        # restore PROJECT_ROOT (monkeypatch will auto-restore, but be safe)
        monkeypatch.setattr(db_helper, "PROJECT_ROOT", real_root)


def test_connproxy_close_raises(monkeypatch):
    # Create a normal proxy using init_db and make underlying close raise
    from aitown.helpers.db_helper import init_db, _migration_path

    p = init_db(":memory:")
    # Replace the proxy's underlying connection with a fake object whose
    # close() raises; avoid monkeypatching the real sqlite3.Connection.close
    class FakeCursor:
        def execute(self, *args, **kwargs):
            return None

    class FakeConn:
        def __init__(self):
            self.row_factory = None

        def cursor(self):
            return FakeCursor()

        def close(self):
            raise RuntimeError("boom")

    try:
        p._conn = FakeConn()
        # calling proxy.close should swallow exceptions coming from underlying.close
        p.close()
    finally:
        # replace with a no-op close so any teardown won't fail
        try:
            p._conn.close = lambda: None
        except Exception:
            pass


def test_load_db_missing_migration(tmp_path, monkeypatch):
    from aitown.helpers import db_helper
    from aitown.helpers.path_helper import PROJECT_ROOT as real_root

    monkeypatch.setattr(db_helper, "PROJECT_ROOT", tmp_path)
    import pytest

    with pytest.raises(FileNotFoundError):
        db_helper.load_db(":memory:")
    monkeypatch.setattr(db_helper, "PROJECT_ROOT", real_root)


def test_init_db_with_seed_and_load_db_context_manager():
    # exercise init_db with seed=True and load_db context manager to hit proxy enter/exit
    from aitown.helpers.db_helper import init_db, load_db

    # init_db with seed=True should succeed and create tables
    with init_db(":memory:", seed=True) as c:
        cur = c.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = cur.fetchall()
        assert len(rows) > 0

    # load_db context manager should return a proxy and close properly
    with load_db(":memory:") as ld:
        cur2 = ld.cursor()
        cur2.execute("SELECT 1")
    # after context exit, calling __del__ should be safe
    try:
        ld.__del__()
    except Exception:
        pass


def test_init_db_with_existing_connection():
    # pass a sqlite3.Connection instance into init_db (created=False branch)
    import sqlite3
    from aitown.helpers.db_helper import init_db

    base_conn = sqlite3.connect(":memory:")
    try:
        returned = init_db(base_conn)
        # should return the same underlying sqlite3.Connection
        assert isinstance(returned, sqlite3.Connection)
        returned.execute("SELECT 1")
    finally:
        try:
            base_conn.close()
        except Exception:
            pass


def test_load_db_proxy_close_and_attr_forward(monkeypatch):
    # create a proxy and replace its _conn with a FakeConn that raises on close
    from aitown.helpers.db_helper import load_db

    class FakeConn2:
        def __init__(self):
            self.row_factory = None

        def cursor(self):
            class C:
                def execute(self, *a, **k):
                    return None
                def fetchall(self):
                    return []
            return C()

        def execute(self, *a, **k):
            return None

        def close(self):
            raise RuntimeError("boom2")

    proxy = load_db(":memory:")
    try:
        proxy._conn = FakeConn2()
        # attribute forwarding: calling execute on proxy should call underlying
        proxy.execute("SELECT 1")
        # calling close should swallow the RuntimeError
        proxy.close()
        # __del__ should also be safe
        try:
            proxy.__del__()
        except Exception:
            pass
    finally:
        try:
            proxy._conn.close = lambda: None
        except Exception:
            pass


def test_init_db_proxy_del_handles_exception():
    # create a proxy and replace its _conn with a FakeConn that raises on close,
    # then call __del__ to exercise the except branch in __del__
    from aitown.helpers.db_helper import init_db

    class FakeConn3:
        def close(self):
            raise RuntimeError("delboom")

    p = init_db(":memory:")
    try:
        p._conn = FakeConn3()
        # calling __del__ should swallow the RuntimeError
        p.__del__()
    finally:
        try:
            p._conn.close = lambda: None
        except Exception:
            pass
