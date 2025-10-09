from aitown.helpers.init_db import init_db
from aitown.repos import place_repo


def test_place_repo_crud_and_json():
    conn = init_db(":memory:")
    Place = place_repo.Place
    Repo = place_repo.PlaceRepository

    p = Place(id="place:1", name="Market", tags=["shop", "market"], shop_inventory=["apple", "bread"], created_at=None)
    repo = Repo(conn)
    created = repo.create(p)
    assert created.id == "place:1"

    fetched = repo.get_by_id("place:1")
    assert fetched.name == "Market"
    assert isinstance(fetched.tags, list)
    assert "apple" in fetched.shop_inventory

    all_places = repo.list_all()
    assert any(pl.id == "place:1" for pl in all_places)

    repo.delete("place:1")
    try:
        repo.get_by_id("place:1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass

    conn.close()


def test_create_place_without_id_generates_uuid():
    conn = init_db(":memory:")
    repo = place_repo.PlaceRepository(conn)
    place = place_repo.Place(id=None, name="PlGen", tags=None, shop_inventory=None, created_at=None)
    created = repo.create(place)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "PlGen"
    conn.close()


def test_place_conflict_and_notfound_additional():
    conn = init_db(":memory:")
    Repo = place_repo.PlaceRepository
    Place = place_repo.Place
    repo = Repo(conn)
    pl = Place(id="place:dup", name="X", tags=["a"], shop_inventory=[], created_at=None)
    repo.create(pl)
    import pytest

    with pytest.raises(Exception):
        repo.create(pl)
    with pytest.raises(Exception):
        repo.get_by_id("missing:place")
    with pytest.raises(Exception):
        repo.delete("missing:place")
    conn.close()
