import pytest

import aitown.repos.road_repo as road_mod


def test_road_repo_crud_and_list_nearby(db_conn):
    Road = road_mod.Road
    Repo = road_mod.RoadRepository

    # create two places to reference
    cur = db_conn.cursor()
    cur.execute(
        "INSERT INTO place (id, name) VALUES (?, ?)",
        ("place:A", "A"),
    )
    cur.execute(
        "INSERT INTO place (id, name) VALUES (?, ?)",
        ("place:B", "B"),
    )
    db_conn.commit()

    repo = Repo(db_conn)
    r = Road(id="road:1", from_place="place:A", to_place="place:B", direction="north")
    created = repo.create(r)
    assert created.id == "road:1"

    fetched = repo.get_by_id("road:1")
    assert fetched.direction == "north"

    nearby = repo.list_nearby("place:A")
    assert any(rr.id == "road:1" for rr in nearby)

    repo.delete("road:1")
    with pytest.raises(Exception):
        repo.get_by_id("road:1")


def test_road_autogen_and_delete_notfound_additional(db_conn):
    # create referenced places
    cur = db_conn.cursor()
    cur.execute("INSERT INTO place (id, name) VALUES (?, ?)", ("p1", "P1"))
    cur.execute("INSERT INTO place (id, name) VALUES (?, ?)", ("p2", "P2"))
    db_conn.commit()
    Repo = road_mod.RoadRepository
    Road = road_mod.Road
    repo = Repo(db_conn)
    r = Road(id="", from_place="p1", to_place="p2", direction="east")
    created = repo.create(r)
    assert created.id != ""

    with pytest.raises(Exception):
        repo.delete("missing:road")
