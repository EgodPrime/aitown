from aitown.helpers.init_db import init_db
from aitown.repos import item_repo


def test_item_repo_crud():
    conn = init_db(":memory:")
    Item = item_repo.Item
    Repo = item_repo.ItemRepository

    item = Item(id="item:1", name="Coin", description="A shiny coin")
    repo = Repo(conn)
    created = repo.create(item)
    assert created.id == "item:1"

    fetched = repo.get_by_id("item:1")
    assert fetched.name == "Coin"

    all_items = repo.list_all()
    assert any(i.id == "item:1" for i in all_items)

    repo.delete("item:1")
    try:
        repo.get_by_id("item:1")
        assert False, "Expected NotFoundError"
    except Exception:
        pass

    conn.close()


def test_create_item_without_id_generates_uuid():
    conn = init_db(":memory:")
    repo = item_repo.ItemRepository(conn)
    item = item_repo.Item(id=None, name="Generated", description=None)
    created = repo.create(item)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "Generated"
    conn.close()


def test_item_conflict_and_notfound_additional():
    conn = init_db(":memory:")
    Repo = item_repo.ItemRepository
    Item = item_repo.Item
    repo = Repo(conn)

    it = Item(id="item:dup", name="X", description=None)
    repo.create(it)
    import pytest

    with pytest.raises(Exception):
        repo.create(it)
    with pytest.raises(Exception):
        repo.get_by_id("missing:item")
    with pytest.raises(Exception):
        repo.delete("missing:item")
    conn.close()
