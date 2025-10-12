import pytest

import aitown.kernel.npc_actions as npc_actions
import aitown.repos.effect_repo as effect_repo_module
from aitown.kernel.npc_actions import ActionExecutor
from aitown.repos.effect_repo import Effect, EffectRepository
from aitown.repos.event_repo import Event
from aitown.repos.item_repo import Item, ItemRepository, ItemType
from aitown.repos.npc_repo import NPC, NPCStatus
from aitown.repos.place_repo import Place, PlaceTag
from aitown.repos.road_repo import Road

# `action_env` fixture is provided by tests/unit/conftest.py


def test_move_success_updates_location_and_memory(action_env):
    place_repo = action_env["place_repo"]
    road_repo = action_env["road_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:home", name="Home", tags=[PlaceTag.HOUSE.value]))
    place_repo.create(
        Place(id="place:market", name="Market", tags=[PlaceTag.WORKABLE.value])
    )
    road_repo.create(
        Road(
            id="road:1",
            from_place="place:home",
            to_place="place:market",
            direction="two-way",
        )
    )
    npc_repo.create(
        NPC(
            id="npc:1",
            name="Alice",
            location_id="place:home",
            inventory={"item_marker": 0},
        )
    )

    assert ActionExecutor.move("npc:1", "place:market") is True

    updated = npc_repo.get_by_id("npc:1")
    assert updated.location_id == "place:market"
    memories = memory_repo.list_by_npc("npc:1")
    assert len(memories) == 1
    assert "移动" in memories[0].content


def test_move_failure_without_route(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:home", name="Home", tags=[]))
    place_repo.create(Place(id="place:forest", name="Forest", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:2",
            name="Bob",
            location_id="place:home",
            inventory={"item_marker": 0},
        )
    )

    assert ActionExecutor.move("npc:2", "place:forest") is False

    updated = npc_repo.get_by_id("npc:2")
    assert updated.location_id == "place:home"
    assert memory_repo.list_by_npc("npc:2") == []


def test_eat_consumes_item_and_applies_effect(action_env):
    item_repo = action_env["item_repo"]
    effect_repo = action_env["effect_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    effect_repo.create(
        Effect(id="effect:energy", name="Energy", attribute="energy", change=5)
    )
    item_repo.create(
        Item(
            id="item:snack",
            name="Snack",
            value=2,
            type=ItemType.CONSUMABLE,
            effect_ids=["effect:energy"],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:3",
            name="Caro",
            inventory={"item:snack": 2},
            energy=70,
            hunger=60,
            mood=50,
        )
    )

    assert ActionExecutor.eat("npc:3", "item:snack", 1) is True

    updated = npc_repo.get_by_id("npc:3")
    assert updated.energy == 75
    assert updated.inventory["item:snack"] == 1
    memories = memory_repo.list_by_npc("npc:3")
    assert len(memories) == 1
    assert "吃了" in memories[0].content


def test_eat_removes_item_when_stock_used_up(action_env):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    item_repo.create(
        Item(
            id="item:berry",
            name="Berry",
            value=1,
            type=ItemType.CONSUMABLE,
            effect_ids=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:12",
            name="Ned",
            inventory={"item:berry": 1},
            energy=50,
            hunger=50,
            mood=50,
        )
    )

    assert ActionExecutor.eat("npc:12", "item:berry", 1) is True

    updated = npc_repo.get_by_id("npc:12")
    assert "item:berry" not in updated.inventory
    memories = memory_repo.list_by_npc("npc:12")
    assert memories and "吃了" in memories[0].content


def test_sleep_in_house_restores_stats_and_sets_status(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:home", name="Home", tags=[PlaceTag.HOUSE.value]))
    npc_repo.create(
        NPC(
            id="npc:4",
            name="Dana",
            location_id="place:home",
            energy=60,
            mood=50,
            inventory={"item_marker": 0},
        )
    )

    assert ActionExecutor.sleep("npc:4", 1) is True

    updated = npc_repo.get_by_id("npc:4")
    assert updated.energy == 72
    assert updated.mood == 56
    assert updated.status == NPCStatus.SLEEPING
    memories = memory_repo.list_by_npc("npc:4")
    assert len(memories) == 1
    assert "美美地睡了一觉" in memories[0].content


def test_work_rewards_currency_and_consumes_stats(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(
        Place(id="place:office", name="Office", tags=[PlaceTag.WORKABLE.value])
    )
    npc_repo.create(
        NPC(
            id="npc:5",
            name="Eli",
            location_id="place:office",
            energy=80,
            mood=70,
            inventory={"item_marker": 0},
        )
    )

    assert ActionExecutor.work("npc:5", 2) is True

    updated = npc_repo.get_by_id("npc:5")
    assert updated.energy == 60
    assert updated.mood == 60
    assert updated.inventory["item_silver_coin"] == 4
    memories = memory_repo.list_by_npc("npc:5")
    assert len(memories) == 1
    assert "工作" in memories[0].content


def test_work_increments_existing_coin_stack(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]

    place_repo.create(
        Place(id="place:factory2", name="Factory 2", tags=[PlaceTag.WORKABLE.value])
    )
    npc_repo.create(
        NPC(
            id="npc:11",
            name="Lem",
            location_id="place:factory2",
            energy=70,
            mood=70,
            inventory={
                "item_silver_coin": 1,
            },
        )
    )

    assert ActionExecutor.work("npc:11", 1) is True
    updated = npc_repo.get_by_id("npc:11")
    assert updated.inventory["item_silver_coin"] == 3


def test_event_listener_falls_back_to_idle_on_failure(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:start", name="Start", tags=[]))
    place_repo.create(Place(id="place:target", name="Target", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:6",
            name="Fae",
            location_id="place:start",
            energy=50,
            mood=40,
            inventory={"item_marker": 0},
        )
    )

    event = Event(
        event_type="npc_action",
        payload={"action_type": "move", "npc_id": "npc:6", "place_id": "place:target"},
    )
    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:6")
    assert updated.energy == 45
    assert updated.mood == 50
    memories = memory_repo.list_by_npc("npc:6")
    assert len(memories) == 1
    assert "放松" in memories[0].content
    assert event.processed == 1
    assert event.processed_at is not None


def test_sleep_outside_house_uses_generic_message(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:camp", name="Camp", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:7",
            name="Gail",
            location_id="place:camp",
            energy=40,
            mood=35,
            inventory={"marker": 0},
        )
    )

    assert ActionExecutor.sleep("npc:7", 2) is True

    updated = npc_repo.get_by_id("npc:7")
    assert updated.energy == 60
    assert updated.mood == 45
    memories = memory_repo.list_by_npc("npc:7")
    assert len(memories) == 1
    assert "睡了一觉" in memories[0].content and "美美" not in memories[0].content


def test_eat_fails_when_inventory_missing(action_env):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    item_repo.create(
        Item(
            id="item:soup",
            name="Soup",
            value=3,
            type=ItemType.CONSUMABLE,
            effect_ids=[],
        )
    )
    npc_repo.create(
        NPC(id="npc:8", name="Hank", inventory={}, energy=50, hunger=20, mood=30)
    )

    assert ActionExecutor.eat("npc:8", "item:soup", 1) is False
    assert npc_repo.get_by_id("npc:8").inventory == {}
    assert memory_repo.list_by_npc("npc:8") == []


def test_work_fails_when_place_not_workable(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]

    place_repo.create(Place(id="place:park", name="Park", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:9",
            name="Ivan",
            location_id="place:park",
            energy=90,
            mood=80,
            inventory={"marker": 0},
        )
    )

    assert ActionExecutor.work("npc:9", 1) is False
    assert npc_repo.get_by_id("npc:9").energy == 90


def test_work_fails_when_stats_low(action_env):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]

    place_repo.create(
        Place(id="place:factory", name="Factory", tags=[PlaceTag.WORKABLE.value])
    )
    npc_repo.create(
        NPC(
            id="npc:10",
            name="Jill",
            location_id="place:factory",
            energy=5,
            mood=5,
            inventory={"marker": 0},
        )
    )

    assert ActionExecutor.work("npc:10", 1) is False


def test_buy_success_updates_inventory_and_coins(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(
            id="item:potion",
            name="Potion",
            value=3,
            type=ItemType.CONSUMABLE,
            effect_ids=[],
        )
    )
    place_repo.create(
        Place(
            id="place:shop",
            name="Potion Shop",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:buyer",
            name="Kira",
            location_id="place:shop",
            inventory={
                "item_bronze_coin": 12,
                "item_silver_coin": 1,
                "item:potion": 1,
            },
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:shop"
            self.name = "Potion Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {"item:potion": 5}

    fake_place = FakeShop()
    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: fake_place)

    assert ActionExecutor.buy("npc:buyer", "item:potion", 4) is True

    updated = npc_repo.get_by_id("npc:buyer")
    assert updated.inventory.get("item:potion") == 5
    assert updated.inventory.get("item_bronze_coin", 0) == 0
    memories = memory_repo.list_by_npc("npc:buyer")
    assert memories and "买了" in memories[0].content


def test_buy_fails_when_stock_insufficient(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(
            id="item:elixir",
            name="Elixir",
            value=5,
            type=ItemType.CONSUMABLE,
            effect_ids=[],
        )
    )
    place_repo.create(
        Place(
            id="place:shop",
            name="Potion Shop",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:buyer2",
            name="Lia",
            location_id="place:shop",
            inventory={
                "item_bronze_coin": 30,
            },
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:shop"
            self.name = "Potion Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {"item:elixir": 1}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    assert ActionExecutor.buy("npc:buyer2", "item:elixir", 2) is False
    assert npc_repo.get_by_id("npc:buyer2").inventory.get("item:elixir") is None


def test_buy_fails_when_funds_insufficient(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(id="item:gem", name="Gem", value=20, type=ItemType.MISC, effect_ids=[])
    )
    place_repo.create(
        Place(
            id="place:shop",
            name="Gem Shop",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:buyer3",
            name="Max",
            location_id="place:shop",
            inventory={
                "item_bronze_coin": 10,
            },
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:shop"
            self.name = "Gem Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {"item:gem": 5}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    assert ActionExecutor.buy("npc:buyer3", "item:gem", 1) is False


def test_buy_handles_deduction_failure_gracefully(action_env, monkeypatch):
    """Simulate a deduction routine failure (deduct_cost_low_first returns False)
    and ensure ActionExecutor.buy returns False and does not modify inventory.
    """
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(id="item:toys", name="Toy", value=2, type=ItemType.MISC, effect_ids=[])
    )
    place_repo.create(
        Place(id="place:shop", name="Toy Shop", tags=[PlaceTag.SHOP.value], shop_inventory=[])
    )
    npc_repo.create(
        NPC(
            id="npc:buyer4",
            name="Tess",
            location_id="place:shop",
            inventory={"item_bronze_coin": 10},
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:shop"
            self.name = "Toy Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {"item:toys": 5}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    # Patch the deduct function to simulate unexpected failure despite adequate funds
    import aitown.kernel.npc_actions as npc_actions_module

    monkeypatch.setattr(npc_actions_module, "deduct_cost_low_first", lambda inv, cost: (inv, False))

    assert ActionExecutor.buy("npc:buyer4", "item:toys", 1) is False
    # inventory should remain unchanged
    assert npc_repo.get_by_id("npc:buyer4").inventory.get("item:toys") is None


def test_sell_success_distributes_coins(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(
            id="item:relic", name="Relic", value=617, type=ItemType.MISC, effect_ids=[]
        )
    )
    place_repo.create(
        Place(
            id="place:market",
            name="Grand Market",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:seller",
            name="Nia",
            location_id="place:market",
            inventory={
                "item:relic": 2,
            },
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:market"
            self.name = "Grand Market"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    assert ActionExecutor.sell("npc:seller", "item:relic", 2) is True

    updated = npc_repo.get_by_id("npc:seller")
    assert updated.inventory.get("item_platinum_coin") == 1
    assert updated.inventory.get("item_gold_coin") == 2
    assert updated.inventory.get("item_silver_coin") == 3
    assert updated.inventory.get("item_bronze_coin") == 4
    assert updated.inventory.get("item:relic") == 0
    memories = memory_repo.list_by_npc("npc:seller")
    assert memories and "卖了" in memories[0].content


def test_sell_fails_when_not_shop(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(id="item:stone", name="Stone", value=1, type=ItemType.MISC, effect_ids=[])
    )
    place_repo.create(Place(id="place:yard", name="Yard", tags=[], shop_inventory=[]))
    npc_repo.create(
        NPC(
            id="npc:seller2",
            name="Ona",
            location_id="place:yard",
            inventory={"item:stone": 1},
        )
    )

    class FakePlace:
        def __init__(self):
            self.id = "place:yard"
            self.name = "Yard"
            self.tags = []
            self.shop_inventory = {}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakePlace())

    assert ActionExecutor.sell("npc:seller2", "item:stone", 1) is False


def test_sell_fails_when_inventory_insufficient(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(id="item:herb", name="Herb", value=2, type=ItemType.MISC, effect_ids=[])
    )
    place_repo.create(
        Place(
            id="place:shop",
            name="Herb Shop",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(id="npc:seller3", name="Pia", location_id="place:shop", inventory={})
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:shop"
            self.name = "Herb Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    assert ActionExecutor.sell("npc:seller3", "item:herb", 1) is False


def test_idle_updates_mood_and_energy(action_env):
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]
    place_repo = action_env["place_repo"]

    place_repo.create(Place(id="place:plaza", name="Plaza", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:idle",
            name="Quin",
            location_id="place:plaza",
            energy=30,
            mood=95,
            inventory={"marker": 0},
        )
    )

    assert ActionExecutor.idle("npc:idle") is True

    updated = npc_repo.get_by_id("npc:idle")
    assert updated.energy == 25
    assert updated.mood == 100
    memories = memory_repo.list_by_npc("npc:idle")
    assert memories and "放松" in memories[0].content


def test_event_listener_success_path_without_fallback(action_env, monkeypatch):
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(Place(id="place:rest", name="Rest", tags=[]))
    npc_repo.create(
        NPC(
            id="npc:event",
            name="Rae",
            location_id="place:rest",
            mood=40,
            energy=50,
            inventory={"marker": 0},
        )
    )

    calls = []

    original_idle = ActionExecutor.idle

    def fake_idle(npc_id: str) -> bool:
        calls.append(npc_id)
        return original_idle(npc_id)

    monkeypatch.setattr(ActionExecutor, "idle", fake_idle)

    event = Event(
        event_type="npc_action", payload={"action_type": "idle", "npc_id": "npc:event"}
    )
    ActionExecutor.event_listener(None, event)

    assert event.processed == 1
    assert event.processed_at is not None
    assert calls == ["npc:event"]
    memories = memory_repo.list_by_npc("npc:event")
    assert memories and len(memories) == 1


def test_event_listener_handles_buy(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(
            id="item:event_buy",
            name="Ticket",
            value=2,
            type=ItemType.MISC,
            effect_ids=[],
        )
    )
    place_repo.create(
        Place(
            id="place:event_shop",
            name="Event Shop",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:event-buyer",
            name="Sam",
            location_id="place:event_shop",
            inventory={
                "item_bronze_coin": 10,
            },
        )
    )

    class FakeShop:
        def __init__(self):
            self.id = "place:event_shop"
            self.name = "Event Shop"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {"item:event_buy": 3}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeShop())

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "buy",
            "npc_id": "npc:event-buyer",
            "item_id": "item:event_buy",
            "item_amount": 2,
        },
    )

    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:event-buyer")
    assert updated.inventory.get("item:event_buy") == 2
    assert event.processed == 1
    assert memory_repo.list_by_npc("npc:event-buyer")


def test_event_listener_handles_sell(action_env, monkeypatch):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]
    place_repo = action_env["place_repo"]

    item_repo.create(
        Item(
            id="item:event_sell",
            name="Badge",
            value=50,
            type=ItemType.MISC,
            effect_ids=[],
        )
    )
    place_repo.create(
        Place(
            id="place:event_market",
            name="Event Market",
            tags=[PlaceTag.SHOP.value],
            shop_inventory=[],
        )
    )
    npc_repo.create(
        NPC(
            id="npc:event-seller",
            name="Uma",
            location_id="place:event_market",
            inventory={
                "item:event_sell": 1,
            },
        )
    )

    class FakeMarket:
        def __init__(self):
            self.id = "place:event_market"
            self.name = "Event Market"
            self.tags = [PlaceTag.SHOP.value]
            self.shop_inventory = {}

    monkeypatch.setattr(place_repo, "get_by_id", lambda _pid: FakeMarket())

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "sell",
            "npc_id": "npc:event-seller",
            "item_id": "item:event_sell",
            "item_amount": 1,
        },
    )

    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:event-seller")
    assert updated.inventory.get("item_platinum_coin", 0) == 0
    assert updated.inventory.get("item_gold_coin", 0) == 0
    assert updated.inventory.get("item_silver_coin", 0) == 5
    assert updated.inventory.get("item_bronze_coin", 0) == 0
    assert updated.inventory.get("item:event_sell", 0) == 0
    assert event.processed == 1
    assert memory_repo.list_by_npc("npc:event-seller")


def test_event_listener_handles_eat(action_env):
    item_repo = action_env["item_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    item_repo.create(
        Item(
            id="item:event_food",
            name="Snack",
            value=1,
            type=ItemType.CONSUMABLE,
            effect_ids=[],
        )
    )
    npc_repo.create(
        NPC(id="npc:event-eater", name="Wes", inventory={"item:event_food": 2})
    )

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "eat",
            "npc_id": "npc:event-eater",
            "item_id": "item:event_food",
            "item_amount": 2,
        },
    )

    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:event-eater")
    assert "item:event_food" not in updated.inventory
    assert memory_repo.list_by_npc("npc:event-eater")


def test_event_listener_handles_sleep(action_env, monkeypatch):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(
        Place(id="place:event-house", name="Inn", tags=[PlaceTag.HOUSE.value])
    )
    npc_repo.create(
        NPC(
            id="npc:event-sleeper",
            name="Yui",
            location_id="place:event-house",
            energy=40,
            mood=30,
            inventory={},
        )
    )

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "sleep",
            "npc_id": "npc:event-sleeper",
            "duration_hours": 1,
        },
    )

    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:event-sleeper")
    assert updated.status == NPCStatus.SLEEPING
    assert memory_repo.list_by_npc("npc:event-sleeper")


def test_event_listener_handles_work(action_env, monkeypatch):
    place_repo = action_env["place_repo"]
    npc_repo = action_env["npc_repo"]
    memory_repo = action_env["memory_repo"]

    place_repo.create(
        Place(id="place:event-office", name="Office", tags=[PlaceTag.WORKABLE.value])
    )
    npc_repo.create(
        NPC(
            id="npc:event-worker",
            name="Zed",
            location_id="place:event-office",
            energy=90,
            mood=90,
            inventory={},
        )
    )

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "work",
            "npc_id": "npc:event-worker",
            "duration_hours": 1,
        },
    )

    ActionExecutor.event_listener(None, event)

    updated = npc_repo.get_by_id("npc:event-worker")
    assert updated.inventory.get("item_silver_coin") == 2
    assert memory_repo.list_by_npc("npc:event-worker")


def test_event_listener_handles_unknown_action(action_env, monkeypatch):
    npc_repo = action_env["npc_repo"]
    place_repo = action_env["place_repo"]

    place_repo.create(
        Place(id="place:event", name="Event Field", tags=[], shop_inventory=[])
    )
    npc_repo.create(
        NPC(id="npc:unknown", name="Vic", location_id="place:event", inventory={})
    )

    calls: list[str] = []
    monkeypatch.setattr(ActionExecutor, "idle", lambda npc_id: calls.append(npc_id))

    event = Event(
        event_type="npc_action",
        payload={
            "action_type": "dance",
            "npc_id": "npc:unknown",
        },
    )

    ActionExecutor.event_listener(None, event)

    assert event.processed == 1
    assert calls == []
