import pytest
from aitown.helpers.db_helper import init_db
from aitown.repos.npc_repo import NpcRepository
from aitown.repos.item_repo import ItemRepository
from aitown.repos.effect_repo import EffectRepository
from aitown.repos.place_repo import PlaceRepository
from aitown.repos.memory_repo import MemoryEntryRepository
from aitown.repos.road_repo import RoadRepository


@pytest.fixture
def db_conn():
    conn = init_db(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def npc_repo(db_conn) -> NpcRepository:
    return NpcRepository(db_conn)


@pytest.fixture
def item_repo(db_conn):
    return ItemRepository(db_conn)


@pytest.fixture
def effect_repo(db_conn) -> EffectRepository:
    return EffectRepository(db_conn)


@pytest.fixture
def place_repo(db_conn):
    return PlaceRepository(db_conn)


@pytest.fixture
def memory_repo(db_conn):
    return MemoryEntryRepository(db_conn)


@pytest.fixture
def road_repo(db_conn):
    return RoadRepository(db_conn)


@pytest.fixture
def action_env(monkeypatch, db_conn, npc_repo, item_repo, effect_repo, place_repo, memory_repo, road_repo):
    """Provide a pre-wired environment similar to previous tests, but shared.
    This sets ActionExecutor class-level repos and connection, and monkeypatches any
    required imports to use the in-memory repos.
    """
    import aitown.kernel.npc_actions as npc_actions
    import aitown.repos.effect_repo as effect_repo_module
    from aitown.kernel.npc_actions import ActionExecutor

    # Save originals
    orig_conn = ActionExecutor.conn
    orig_npc_repo = ActionExecutor.npc_repo
    orig_item_repo = ActionExecutor.item_repo
    orig_effect_repo = ActionExecutor.effect_repo
    orig_place_repo = ActionExecutor.place_repo
    orig_memory_repo = ActionExecutor.memory_repo
    orig_road_repo = ActionExecutor.road_repo

    # Assign test repos
    ActionExecutor.conn = db_conn
    ActionExecutor.npc_repo = npc_repo
    ActionExecutor.item_repo = item_repo
    ActionExecutor.effect_repo = effect_repo
    ActionExecutor.place_repo = place_repo
    ActionExecutor.memory_repo = memory_repo
    ActionExecutor.road_repo = road_repo

    class StubPlaceRepository:
        def __init__(self, *args, **kwargs):
            self._repo = place_repo

        def get_by_id(self, place_id):
            return place_repo.get_by_id(place_id)

    monkeypatch.setattr(npc_actions, "PlaceRepository", StubPlaceRepository)
    monkeypatch.setattr(effect_repo_module, "NpcRepository", lambda: npc_repo)

    yield {
        "conn": db_conn,
        "npc_repo": npc_repo,
        "item_repo": item_repo,
        "effect_repo": effect_repo,
        "place_repo": place_repo,
        "memory_repo": memory_repo,
        "road_repo": road_repo,
    }

    # Restore
    ActionExecutor.conn = orig_conn
    ActionExecutor.npc_repo = orig_npc_repo
    ActionExecutor.item_repo = orig_item_repo
    ActionExecutor.effect_repo = orig_effect_repo
    ActionExecutor.place_repo = orig_place_repo
    ActionExecutor.memory_repo = orig_memory_repo
    ActionExecutor.road_repo = orig_road_repo
