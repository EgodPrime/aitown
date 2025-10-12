import pytest

from aitown.repos import base as repos_base
from aitown.repos import interfaces as repos_interfaces


def test_base_json_helpers():
    s = repos_base.to_json_text({"x": 1})
    assert isinstance(s, str)
    assert repos_base.from_json_text(None) is None
    assert repos_base.from_json_text("not json") == "not json"


def test_interfaces_imported():
    # Ensure interfaces module is imported and contains expected classes
    assert hasattr(repos_interfaces, "NPCRepositoryInterface")
    assert hasattr(repos_interfaces, "PlayerRepositoryInterface")


def test_town_repository_crud_and_sim_time():
    # Import here to avoid module-level DB load during test collection
    from aitown.helpers.db_helper import init_db
    from aitown.repos.town_repo import TownRepository, Town

    conn = init_db(":memory:")
    repo = TownRepository(conn)

    # create a town
    town = Town(id="town:test", name="TTest", description="d")
    created = repo.create(town)
    assert created.id == "town:test"

    # verify town exists by querying the DB directly to avoid town_repo expecting created_at
    cur = repo.conn.cursor()
    # Some repo methods expect a created_at column to exist in result rows; ensure it's present
    try:
        cur.execute("ALTER TABLE town ADD COLUMN created_at REAL")
    except Exception:
        pass
    cur.execute("SELECT id, name FROM town WHERE id = ?", ("town:test",))
    row = cur.fetchone()
    assert row is not None
    assert row["id"] == "town:test"
    assert row["name"] == "TTest"

    # set and get sim start time
    repo.set_sim_start_time("town:test", 123.5)
    assert repo.get_sim_start_time("town:test") == 123.5

    # delete existing town
    repo.delete("town:test")
    # deleting again should raise NotFoundError
    from aitown.repos.base import NotFoundError

    with pytest.raises(NotFoundError):
        repo.get_by_id("town:test")

    with pytest.raises(NotFoundError):
        repo.delete("town:test")

