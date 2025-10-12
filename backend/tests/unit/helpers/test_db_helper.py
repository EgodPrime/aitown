import sqlite3
from pathlib import Path

import pytest

from aitown.helpers import db_helper as initmod
from aitown.repos import item_repo, npc_repo, place_repo, player_repo


def test_init_db_memory_has_tables_and_row_factory():
    conn = initmod.init_db(":memory:", seed=False)
    try:
        # tables from migrations should exist
        names = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "player" in names
        assert "place" in names
        assert "item" in names

        # row_factory should be sqlite3.Row (allowing name access)
        row = conn.execute("SELECT 1 as v").fetchone()
        assert isinstance(row, sqlite3.Row)
    finally:
        conn.close()


def test_init_db_with_connection_object_not_closed():
    conn0 = sqlite3.connect(":memory:")
    try:
        ret = initmod.init_db(conn0, seed=False)
        # same object returned
        assert ret is conn0

        # migrations applied
        names = {
            r[0]
            for r in conn0.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "player" in names
    finally:
        conn0.close()


def test_init_db_missing_migration_file_raises_and_closes(monkeypatch, tmp_path):
    # Force _migration_path to point to a non-existent file and use a fake sqlite3.connect
    fake = type("FakeConn", (), {})()
    fake.closed = False

    def fake_execute(*args, **kwargs):
        return None

    def fake_close():
        fake.closed = True

    fake.execute = fake_execute
    fake.close = fake_close

    def fake_connect(path):
        return fake

    monkeypatch.setattr(initmod, "_migration_path", lambda: Path(tmp_path) / "nope.sql")
    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    with pytest.raises(FileNotFoundError):
        initmod.init_db(":memory:")

    # ensure the fake connection was closed by the function when migration missing
    assert fake.closed is True


def test_init_db_seed_inserts_rows():
    conn = initmod.init_db(":memory:", seed=True)
    try:
        r = conn.execute(
            "SELECT id FROM player WHERE id = ?", ("player:seed",)
        ).fetchone()
        assert r is not None and r[0] == "player:seed"

        # static_data.yaml should have been seeded into place/item/effect tables
        r = conn.execute("SELECT id FROM place WHERE id = ?", ("place:home",)).fetchone()
        assert r is not None and r[0] == "place:home"

        r = conn.execute("SELECT id FROM item WHERE id = ?", ("item_bronze_coin",)).fetchone()
        assert r is not None and r[0] == "item_bronze_coin"

        r = conn.execute("SELECT id FROM effect WHERE id = ?", ("effect_hunger_plus_5",)).fetchone()
        assert r is not None and r[0] == "effect_hunger_plus_5"
    finally:
        conn.close()


def test_init_db_row_factory_assignment_ignored(monkeypatch):
    # simulate a connection-like object where setting row_factory raises
    class FakeConn:
        def __init__(self):
            self.closed = False

        def execute(self, *args, **kwargs):
            # used for PRAGMA and other statements
            return None

        def executescript(self, sql):
            return None

        def cursor(self):
            class C:
                def execute(self, *a, **k):
                    return None

                def fetchone(self):
                    return None

            return C()

        def commit(self):
            return None

        def close(self):
            self.closed = True

        def __getattr__(self, name):
            # row_factory assignment will be caught in __setattr__ below
            raise AttributeError(name)

        def __setattr__(self, name, value):
            if name == "row_factory":
                raise RuntimeError("no row factory")
            super().__setattr__(name, value)

    fake = FakeConn()
    # monkeypatch sqlite3.Connection so isinstance check passes
    import sqlite3 as _sqlite

    monkeypatch.setattr(_sqlite, "Connection", FakeConn, raising=False)

    # call init_db with the fake connection; should not raise
    ret = initmod.init_db(fake, seed=False)
    assert ret is fake
    # cleanup
    ret.close()


def test_cli_closes_file_db(monkeypatch, tmp_path):
    # create a temporary migrations file so init_db will succeed
    mig = tmp_path / "0001_init.sql"
    mig.write_text((initmod._migration_path()).read_text())

    # patch _migration_path to use our temp dir
    monkeypatch.setattr(initmod, "_migration_path", lambda: mig)

    # Mock sqlite3.connect to track if close is called
    closed = False

    class FakeConn:
        def execute(self, *args, **kwargs):
            pass

        def executescript(self, sql):
            pass

        def cursor(self):
            class C:
                def execute(self, *a, **k):
                    pass

                def fetchone(self):
                    pass

            return C()

        def commit(self):
            pass

        def close(self):
            nonlocal closed
            closed = True

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def fake_connect(path):
        return FakeConn()

    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    # run _cli with a file DB and ensure it closes connection
    dbfile = tmp_path / "db.sqlite"
    monkeypatch.setattr("sys.argv", ["prog", "--db", str(dbfile)])
    # run the cli which should create the file and then close
    initmod.main()
    assert closed is True


def test_init_db_invalid_type_raises():
    with pytest.raises(TypeError):
        initmod.init_db(123)


class BadConn:
    def __init__(self):
        self._cur = initmod.init_db(":memory:")

    def cursor(self):
        return self._cur.cursor()

    def execute(self, *a, **k):
        return self._cur.execute(*a, **k)

    def commit(self):
        return self._cur.commit()

    def close(self):
        self._cur.close()

    # deliberately do NOT support row_factory assignment


def test_repo_initialization_with_badconn():
    bad = BadConn()
    try:
        # constructing repos should not raise when row_factory assignment fails
        item_repo.ItemRepository(bad)
        player_repo.PlayerRepository(bad)
        place_repo.PlaceRepository(bad)
        npc_repo.NpcRepository(bad)
    finally:
        bad.close()


class NoRowFactoryConn:
    def __init__(self):
        # underlying real conn for cursor operations if needed
        import sqlite3

        self._real = sqlite3.connect(":memory:")

    def __getattr__(self, name):
        return getattr(self._real, name)

    def __setattr__(self, name, value):
        if name == "row_factory":
            raise AttributeError("cannot set row_factory")
        return super().__setattr__(name, value)

    def close(self):
        self._real.close()


def test_repos_handle_row_factory_attribute_error():
    bad = NoRowFactoryConn()
    try:
        # constructing repos should swallow AttributeError when assigning row_factory
        item_repo.ItemRepository(bad)
        player_repo.PlayerRepository(bad)
        place_repo.PlaceRepository(bad)
        npc_repo.NpcRepository(bad)
    finally:
        bad.close()


def test_load_db_with_config(monkeypatch, tmp_path):
    # Mock get_config to return a db_path
    def mock_get_config(section):
        if section == "repos":
            return {"db_path": str(tmp_path / "test.db")}
        raise KeyError(section)

    monkeypatch.setattr(initmod, "get_config", mock_get_config)

    # Create a temporary migrations file
    mig = tmp_path / "0001_init.sql"
    mig.write_text((initmod._migration_path()).read_text())
    monkeypatch.setattr(initmod, "_migration_path", lambda: mig)

    conn = initmod.load_db()
    try:
        # Check that tables exist
        names = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "player" in names
        assert "place" in names
        assert "item" in names
    finally:
        conn.close()


def test_load_db_with_explicit_path(tmp_path):
    # Create a temporary migrations file
    mig = tmp_path / "0001_init.sql"
    mig.write_text((initmod._migration_path()).read_text())
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(initmod, "_migration_path", lambda: mig)

    db_path = str(tmp_path / "explicit.db")
    conn = initmod.load_db(db_path)
    try:
        # Check that tables exist
        names = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "player" in names
    finally:
        conn.close()
    monkeypatch.undo()


def test_load_db_missing_migration_raises(monkeypatch, tmp_path):
    def mock_get_config(section):
        if section == "repos":
            return {"db_path": str(tmp_path / "test.db")}
        raise KeyError(section)

    monkeypatch.setattr(initmod, "get_config", mock_get_config)
    monkeypatch.setattr(initmod, "_migration_path", lambda: Path(tmp_path) / "nope.sql")

    with pytest.raises(FileNotFoundError):
        initmod.load_db()


def test_load_db_row_factory_assignment_ignored(monkeypatch, tmp_path):
    # Mock get_config
    def mock_get_config(section):
        if section == "repos":
            return {"db_path": str(tmp_path / "test.db")}
        raise KeyError(section)

    monkeypatch.setattr(initmod, "get_config", mock_get_config)

    # Create migrations file
    mig = tmp_path / "0001_init.sql"
    mig.write_text((initmod._migration_path()).read_text())
    monkeypatch.setattr(initmod, "_migration_path", lambda: mig)

    # Mock sqlite3.connect to return a connection where row_factory assignment raises
    class FakeConn:
        def __init__(self):
            self.closed = False

        def execute(self, *args, **kwargs):
            pass

        def executescript(self, sql):
            pass

        def close(self):
            self.closed = True

        def __setattr__(self, name, value):
            if name == "row_factory":
                raise RuntimeError("no row factory")
            super().__setattr__(name, value)

    def fake_connect(path):
        return FakeConn()

    monkeypatch.setattr(sqlite3, "connect", fake_connect)

    # Should not raise
    conn = initmod.load_db()
    assert conn is not None
    conn.close()
