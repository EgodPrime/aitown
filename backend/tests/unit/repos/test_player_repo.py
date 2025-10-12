import pytest

import aitown.repos.player_repo as player_mod


def test_player_repo_crud(db_conn):
    Player = player_mod.Player
    Repo = player_mod.PlayerRepository

    p = Player(id="player:99", display_name="Test", password_hash=None)
    repo = Repo(db_conn)
    created = repo.create(p)
    assert created.id == "player:99"
    fetched = repo.get_by_id("player:99")
    assert fetched.display_name == "Test"

    repo.delete("player:99")
    with pytest.raises(Exception):
        repo.get_by_id("player:99")


def test_player_create_with_zero_created_at_sets_time(db_conn):
    repo = player_mod.PlayerRepository(db_conn)
    p = player_mod.Player(id="p0", display_name="P0", password_hash=None, created_at=0)
    created = repo.create(p)
    assert created.created_at != 0


def test_create_player_without_id_generates_uuid(db_conn):
    repo = player_mod.PlayerRepository(db_conn)
    player = player_mod.Player(id=None, display_name="PGen", password_hash=None)
    created = repo.create(player)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.display_name == "PGen"


def test_player_conflict_and_notfound_additional(db_conn):
    Repo = player_mod.PlayerRepository
    Player = player_mod.Player
    repo = Repo(db_conn)
    p = Player(id="player:dup", display_name="P", password_hash=None)
    repo.create(p)

    with pytest.raises(Exception):
        repo.create(p)
    with pytest.raises(Exception):
        repo.get_by_id("missing:player")
    with pytest.raises(Exception):
        repo.delete("missing:player")
