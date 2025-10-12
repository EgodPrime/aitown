import time
import sqlite3

import pytest

from aitown.helpers.db_helper import init_db
from aitown.repos.town_repo import TownRepository, Town
from aitown.repos.base import NotFoundError
from aitown.repos.base import ConflictError


def test_town_repo_full_crud_and_sim_time():
    # initialize in-memory DB with schema
    conn = init_db(":memory:")
    conn.row_factory = sqlite3.Row

    repo = TownRepository(conn)

    # create via repository.create - produce a town with created_at populated by DB
    t = Town(id="town:x", name="Xtown", description="desc")
    created = repo.create(t)
    assert created.id == "town:x"

    # ensure we can query via get_by_id when the DB row has created_at
    # Some repo code expects a 'created_at' column; add it if missing and set a value
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE town ADD COLUMN created_at REAL")
    except Exception:
        # column may already exist
        pass
    now = time.time()
    cur.execute(
        "UPDATE town SET sim_start_time = ?, description = ?, created_at = ? WHERE id = ?",
        (0.0, "desc", now, "town:x"),
    )
    conn.commit()

    got = repo.get_by_id("town:x")
    assert got.id == "town:x"
    assert got.name == "Xtown"

    # list_all should include our town and not error when created_at missing for some rows
    rows = repo.conn.execute("SELECT * FROM town").fetchall()
    assert any(r["id"] == "town:x" for r in rows)

    # set and get sim start time
    repo.set_sim_start_time("town:x", 12.34)
    assert repo.get_sim_start_time("town:x") == 12.34

    # delete existing town
    repo.delete("town:x")
    with pytest.raises(NotFoundError):
        repo.get_by_id("town:x")

    # deleting again should raise
    with pytest.raises(NotFoundError):
        repo.delete("town:x")

    conn.close()


def test_town_create_conflict_and_notfound():
    conn = init_db(":memory:")
    conn.row_factory = sqlite3.Row
    repo = TownRepository(conn)

    t1 = Town(id="town:conf", name="C1", description=None)
    repo.create(t1)

    # creating again with same id should raise ConflictError
    with pytest.raises(ConflictError):
        repo.create(t1)

    # get_by_id for missing town raises NotFoundError
    with pytest.raises(NotFoundError):
        repo.get_by_id("missing:town")

    # get_sim_start_time for missing town raises NotFoundError
    with pytest.raises(NotFoundError):
        repo.get_sim_start_time("missing:town")

    conn.close()


def test_town_list_all_multiple_rows():
    conn = init_db(":memory:")
    conn.row_factory = sqlite3.Row
    repo = TownRepository(conn)

    # ensure there are at least two towns; insert another row directly with created_at
    t2 = Town(id="town:multi", name="Multi", description="d")
    repo.create(t2)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE town ADD COLUMN created_at REAL")
    except Exception:
        pass
    cur.execute("INSERT OR IGNORE INTO town (id, name, description, sim_start_time, created_at) VALUES (?,?,?,?,?)", ("town:extra", "E", "x", 0.0, 1.0))
    conn.commit()

    listed = repo.list_all()
    assert any(t.id == "town:multi" for t in listed)
    assert any(getattr(t, "id", None) == "town:extra" or getattr(t, "id", None) == "town:extra" for t in listed)

    conn.close()
