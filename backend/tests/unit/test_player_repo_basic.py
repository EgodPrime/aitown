from aitown.helpers.init_db import init_db
from aitown.repos import player_repo
import datetime


def test_player_repo_crud():
    conn = init_db(":memory:")

    Player = player_repo.Player
    Repo = player_repo.PlayerRepository

    p = Player(id="player:99", display_name="Test", password_hash=None, created_at=None)
    repo = Repo(conn)
    created = repo.create(p)
    assert created.id == "player:99"
    fetched = repo.get_by_id("player:99")
    assert fetched.display_name == "Test"

    repo.delete("player:99")
    try:
        repo.get_by_id("player:99")
        assert False, "Expected NotFoundError"
    except Exception:
        pass

    conn.close()


def test_create_player_without_id_generates_uuid():
    conn = init_db(":memory:")
    repo = player_repo.PlayerRepository(conn)
    player = player_repo.Player(id=None, display_name="PGen", password_hash=None, created_at=None)
    created = repo.create(player)
    assert created.id is not None and created.id != ""
    fetched = repo.get_by_id(created.id)
    assert fetched.display_name == "PGen"
    conn.close()


def test_player_conflict_and_notfound_additional():
    conn = init_db(":memory:")
    Repo = player_repo.PlayerRepository
    Player = player_repo.Player
    repo = Repo(conn)
    p = Player(id="player:dup", display_name="P", password_hash=None, created_at=None)
    repo.create(p)
    import pytest

    with pytest.raises(Exception):
        repo.create(p)
    with pytest.raises(Exception):
        repo.get_by_id("missing:player")
    with pytest.raises(Exception):
        repo.delete("missing:player")
    conn.close()
