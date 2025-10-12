import pytest

import aitown.repos.place_repo as place_mod


def test_place_repo_crud_and_json(db_conn):
    Place = place_mod.Place
    Repo = place_mod.PlaceRepository

    p = Place(
        id="place:1",
        name="Market",
        tags=["shop", "market"],
        shop_inventory=["apple", "bread"],
    )
    repo = Repo(db_conn)
    created = repo.create(p)
    assert created.id == "place:1"

    fetched = repo.get_by_id("place:1")
    assert fetched.name == "Market"
    assert isinstance(fetched.tags, list)
    assert "apple" in fetched.shop_inventory

    all_places = repo.list_all()
    assert any(pl.id == "place:1" for pl in all_places)

    repo.delete("place:1")
    with pytest.raises(Exception):
        repo.get_by_id("place:1")


def test_create_place_without_id_generates_uuid(db_conn):
    repo = place_mod.PlaceRepository(db_conn)
    place = place_mod.Place(id=None, name="PlGen", tags=[], shop_inventory=[])
    created = repo.create(place)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "PlGen"


def test_place_conflict_and_notfound_additional(db_conn):
    Repo = place_mod.PlaceRepository
    Place = place_mod.Place
    repo = Repo(db_conn)
    pl = Place(id="place:dup", name="X", tags=["a"], shop_inventory=[])
    repo.create(pl)

    with pytest.raises(Exception):
        repo.create(pl)
    with pytest.raises(Exception):
        repo.get_by_id("missing:place")
    with pytest.raises(Exception):
        repo.delete("missing:place")
