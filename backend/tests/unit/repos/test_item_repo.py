import pytest

import aitown.repos.item_repo as item_mod


def test_item_repo_crud(db_conn):
    Item = item_mod.Item
    Repo = item_mod.ItemRepository

    item = Item(id="item:1", name="Coin", description="A shiny coin")
    repo = Repo(db_conn)
    created = repo.create(item)
    assert created.id == "item:1"

    fetched = repo.get_by_id("item:1")
    assert fetched.name == "Coin"

    all_items = repo.list_all()
    assert any(i.id == "item:1" for i in all_items)

    repo.delete("item:1")
    with pytest.raises(Exception):
        repo.get_by_id("item:1")


def test_create_item_without_id_generates_uuid(db_conn):
    repo = item_mod.ItemRepository(db_conn)
    item = item_mod.Item(id=None, name="Generated", description=None)
    created = repo.create(item)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.name == "Generated"


def test_item_conflict_and_notfound_additional(db_conn):
    Repo = item_mod.ItemRepository
    Item = item_mod.Item
    repo = Repo(db_conn)

    it = Item(id="item:dup", name="X", description=None)
    repo.create(it)

    with pytest.raises(Exception):
        repo.create(it)
    with pytest.raises(Exception):
        repo.get_by_id("missing:item")
    with pytest.raises(Exception):
        repo.delete("missing:item")
