from aitown.helpers.db_helper import init_db
from aitown.repos import road_repo


def test_road_repo_crud_and_list_nearby():
    conn = init_db(":memory:")
    Road = road_repo.Road
    Repo = road_repo.RoadRepository

    # create two places to reference
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO place (id, name) VALUES (?, ?)",
        ("place:A", "A"),
    )
    cur.execute(
        "INSERT INTO place (id, name) VALUES (?, ?)",
        ("place:B", "B"),
    )
    conn.commit()

    repo = Repo(conn)
    r = Road(id="road:1", from_place="place:A", to_place="place:B", direction="north")
    created = repo.create(r)
    assert created.id == "road:1"

    fetched = repo.get_by_id("road:1")
    assert fetched.direction == "north"

    nearby = repo.list_nearby("place:A")
    assert any(rr.id == "road:1" for rr in nearby)

    repo.delete("road:1")
    try:
        repo.get_by_id("road:1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass

    conn.close()


def test_road_autogen_and_delete_notfound_additional():
    conn = init_db(":memory:")
    # create referenced places
    cur = conn.cursor()
    cur.execute("INSERT INTO place (id, name) VALUES (?, ?)", ("p1", "P1"))
    cur.execute("INSERT INTO place (id, name) VALUES (?, ?)", ("p2", "P2"))
    conn.commit()
    Repo = road_repo.RoadRepository
    Road = road_repo.Road
    repo = Repo(conn)
    r = Road(id="", from_place="p1", to_place="p2", direction="east")
    created = repo.create(r)
    assert created.id != ""
    import pytest

    with pytest.raises(Exception):
        repo.delete("missing:road")
    conn.close()
