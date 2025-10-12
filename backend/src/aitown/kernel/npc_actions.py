"""NPC action implementations.

Contains the ActionExecutor which implements NPC actions like move/eat/work/buy/sell.
"""

import datetime
import time

from aitown.helpers.db_helper import load_db
from aitown.repos.effect_repo import EffectRepository
from aitown.repos.event_repo import Event
from aitown.repos.item_repo import ItemRepository, ItemType
from aitown.repos.memory_repo import MemoryEntry, MemoryEntryRepository
from aitown.repos.npc_repo import NpcRepository, NPCStatus
from aitown.repos.place_repo import PlaceRepository, PlaceTag
from aitown.repos.road_repo import RoadRepository
from aitown.helpers.currency_helper import total_value, deduct_cost_low_first, split_amount_to_coins


class ActionExecutor:
    """
    move, eat, sleep, work, buy, sell, idle

    所有动作的流程都是：
    1. 检查前置条件（如位置、物品、状态等）
    2. 生成事件描述消息
    3. 广播消息（TODO）
    4. 更新NPC状态（位置、属性、物品等）
    5. 生成记忆条目
    6. 保存记忆条目到数据库
    7. 标记事件为已处理
    """

    conn = load_db()
    npc_repo: NpcRepository = NpcRepository(conn)
    item_repo: ItemRepository = ItemRepository(conn)
    effect_repo: EffectRepository = EffectRepository(conn)
    place_repo: PlaceRepository = PlaceRepository(conn)
    memory_repo: MemoryEntryRepository = MemoryEntryRepository(conn)
    road_repo: RoadRepository = RoadRepository(conn)

    @staticmethod
    def move(npc_id: str, place_id: str) -> bool:
        """Move NPC to a target place if a connecting road exists.

        Args:
            npc_id: id of the NPC to move
            place_id: destination place id

        Returns:
            True if move succeeded and state was updated, False otherwise.
        """
        success = True
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        # use shared repository instances from the class to avoid re-creating connections
        from_place = ActionExecutor.place_repo.get_by_id(npc.location_id)
        to_place = ActionExecutor.place_repo.get_by_id(place_id)

        available_roads = ActionExecutor.road_repo.list_nearby(npc.location_id)
        road = next(
            (
                r
                for r in available_roads
                if r.from_place == place_id or r.to_place == place_id
            ),
            None,
        )
        if not road:
            msg = (
                f"{npc.name} 想从 {from_place.name} 移动到 {to_place.name}，但无路可走"
            )
            success = False

        msg = f"{npc.name} 从 {from_place.name} 移动到 {to_place.name}"

        # TODO: 广播事件

        if not success:
            return False

        ActionExecutor.npc_repo.update(npc_id, {"location_id": place_id})

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def eat(npc_id: str, item_id: str, item_amount: int) -> bool:
        """Consume an item from NPC inventory and apply its effects.

        Args:
            npc_id: id of the NPC eating
            item_id: id of the item to consume
            item_amount: amount to consume

        Returns:
            True on success, False if inventory or item type invalid.
        """
        success = True
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        inventory = npc.inventory
        item = ActionExecutor.item_repo.get_by_id(item_id)

        if (
            item_id not in inventory
            or inventory[item_id] < item_amount
            or item.type != ItemType.CONSUMABLE
        ):
            msg = f"{npc.name} 想吃 {item.name} x{item_amount}，这显然是在做梦"
            success = False

        msg = f"{npc.name} 吃了 {item.name} x{item_amount}"

        # TODO : 广播事件

        if not success:
            return False

        for eff_id in item.effect_ids:
            eff = ActionExecutor.effect_repo.get_by_id(eff_id)
            eff.apply_to_npc(npc_id, item_amount)
        inventory[item_id] -= item_amount
        if inventory[item_id] <= 0:
            del inventory[item_id]
        ActionExecutor.npc_repo.update(npc_id, {"inventory": inventory})

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def sleep(npc_id: str, duration_hours: int) -> bool:
        """
        在有HOUSE标签的地点睡觉，恢复更多的energy和mood，并获得形容描述“美美地睡了一觉”
        NPC会进入NPCStatus.SLEEPING状态，期间不能执行其他动作
        """
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)

        energy_recovered = 10 * duration_hours
        mood_recovered = 5 * duration_hours

        msg = ""
        if PlaceTag.HOUSE in place.tags:
            energy_recovered *= 1.2
            mood_recovered *= 1.2
            msg = f"{npc.name} 在 {place.name} 美美地睡了一觉"
        else:
            msg = f"{npc.name} 在 {place.name} 睡了一觉"

        # TODO: 广播事件

        ActionExecutor.npc_repo.update(
            npc_id,
            {
                "energy": min(npc.energy + int(energy_recovered), 100),
                "mood": min(npc.mood + int(mood_recovered), 100),
                "status": NPCStatus.SLEEPING,
            },
        )

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def work(npc_id: str, duration_hours: int) -> bool:
        """
        在有WORKABLE标签的地点工作，消耗energy和mood，获得金钱
        """
        """Perform work action for an NPC, adjusting stats and awarding currency.

        Args:
            npc_id: id of the NPC
            duration_hours: number of hours to work

        Returns:
            True if the work was performed, False otherwise.
        """
        success = True
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)
        inventory = npc.inventory

        energy_cost = 10 * duration_hours
        mood_cost = 5 * duration_hours
        money_earned = 20 * duration_hours

        if PlaceTag.WORKABLE not in place.tags:
            msg = f"{npc.name} 想在 {place.name} 工作 {duration_hours} 小时，可惜这里没有工作岗位"
            success = False

        if success and (npc.energy < energy_cost or npc.mood < mood_cost):
            msg = f"{npc.name} 想在 {place.name} 工作 {duration_hours} 小时，但精力或心情不足"
            success = False

        msg = f"{npc.name} 在 {place.name} 开始了 {duration_hours} 小时的工作，预计赚取 {money_earned} 金币"
        # TODO : 广播事件

        if not success:
            return False

        # 将赚取的金额拆分为硬币并加入库存
        coin_adds = split_amount_to_coins(money_earned)
        for cid, cnt in coin_adds.items():
            if cnt <= 0:
                continue
            inventory[cid] = inventory.get(cid, 0) + cnt

        ActionExecutor.npc_repo.update(
            npc_id,
            {
                "energy": max(npc.energy - energy_cost, 0),
                "mood": max(npc.mood - mood_cost, 0),
                "inventory": inventory,
            },
        )

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def buy(npc_id: str, item_id: str, item_amount: int) -> bool:
        """Buy an item from the current place's shop inventory.

        This function checks stock, computes total cost, deducts coins from the NPC
        (using smaller denominations first per tests), updates inventory and records memory.

        Returns:
            True on success, False on failure (insufficient stock or funds).
        """
        success = True
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        inventory = npc.inventory
        item = ActionExecutor.item_repo.get_by_id(item_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)

        if (
            item_id not in place.shop_inventory
            or place.shop_inventory[item_id] < item_amount
        ):
            msg = f"{npc.name} 想买 {item.name} x{item_amount}，但 {place.name} 没有足够的库存"
            success = False

        # 计算NPC现有的金币总额
        total_money = total_value(inventory)

        total_cost = item.value * item_amount
        if success and total_money < total_cost:
            msg = f"{npc.name} 想买 {item.name} x{item_amount}，但没有足够的金币"
            success = False

        msg = f"{npc.name} 在 {place.name} 买了 {item.name} x{item_amount}"
        # TODO : 广播事件

        if not success:
            return False

        # 扣除金币，使用 currency helper（低面值优先以匹配测试行为）
        inventory, deducted_ok = deduct_cost_low_first(inventory, total_cost)
        if not deducted_ok:
            # unexpected: not enough funds (should have been caught above)
            return False

        # 添加购买的物品到NPC库存
        if item_id in inventory:
            inventory[item_id] += item_amount
        else:
            inventory[item_id] = item_amount

        ActionExecutor.npc_repo.update(
            npc_id,
            {
                "inventory": inventory,
            },
        )

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def sell(npc_id: str, item_id: str, item_amount: int) -> bool:
        """Sell an item from NPC inventory at a shop, converting value to coins.

        Args:
            npc_id: id of the NPC selling
            item_id: id of the item to sell
            item_amount: quantity to sell

        Returns:
            True on success, False if place not a shop or insufficient inventory.
        """
        success = True
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        inventory = npc.inventory
        item = ActionExecutor.item_repo.get_by_id(item_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)

        if PlaceTag.SHOP not in place.tags:
            msg = (
                f"{npc.name} 想卖 {item.name} x{item_amount}，但 {place.name} 不是商店"
            )
            success = False

        if success and (item_id not in inventory or inventory[item_id] < item_amount):
            msg = f"{npc.name} 想卖 {item.name} x{item_amount}，但没有足够的库存"
            success = False

        # TODO : 广播事件

        if not success:
            return False

        total_earnings = item.value * item_amount
        msg = f"{npc.name} 在 {place.name} 卖了 {item.name} x{item_amount}，赚了 {total_earnings}"
        platinum_coins = total_earnings // 1000
        gold_coins = (total_earnings % 1000) // 100
        silver_coins = (total_earnings % 100) // 10
        bronze_coins = total_earnings % 10

        mod_to_inventory = [
            {"item_id": "item_platinum_coin", "amount": platinum_coins},
            {"item_id": "item_gold_coin", "amount": gold_coins},
            {"item_id": "item_silver_coin", "amount": silver_coins},
            {"item_id": "item_bronze_coin", "amount": bronze_coins},
            {"item_id": item_id, "amount": -item_amount},
        ]

        for item in mod_to_inventory:
            inventory[item["item_id"]] = (
                inventory.get(item["item_id"], 0) + item["amount"]
            )

        ActionExecutor.npc_repo.update(npc_id, {"inventory": inventory})

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def idle(npc_id: str) -> bool:
        """Make the NPC idle: small mood increase and energy decrease.

        Args:
            npc_id: id of the NPC to idle

        Returns:
            True after updating NPC state and recording memory.
        """
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)

        msg = f"{npc.name} 在 {place.name} 放松了一下， 心情变好了"
        # TODO : 广播事件

        ActionExecutor.npc_repo.update(
            npc_id,
            {
                "mood": min(npc.mood + 10, 100),
                "energy": max(npc.energy - 5, 0),
            },
        )

        npc.remember(ActionExecutor.memory_repo, msg)

        return True

    @staticmethod
    def event_listener(event: Event):
        """Dispatch an incoming event to the corresponding ActionExecutor method.

        The listener interprets the event payload and calls the matching action.
        If the action fails, falls back to idle.
        """
        payload = event.payload
        action_type = payload.get("action_type")
        res = True
        match action_type:
            case "move":
                res = ActionExecutor.move(payload["npc_id"], payload["place_id"])
            case "eat":
                res = ActionExecutor.eat(
                    payload["npc_id"], payload["item_id"], payload["item_amount"]
                )
            case "sleep":
                res = ActionExecutor.sleep(payload["npc_id"], payload["duration_hours"])
            case "work":
                res = ActionExecutor.work(payload["npc_id"], payload["duration_hours"])
            case "buy":
                res = ActionExecutor.buy(
                    payload["npc_id"], payload["item_id"], payload["item_amount"]
                )
            case "sell":
                res = ActionExecutor.sell(
                    payload["npc_id"], payload["item_id"], payload["item_amount"]
                )
            case "idle":
                res = ActionExecutor.idle(payload["npc_id"])
            case _:
                pass

        if not res:
            ActionExecutor.idle(payload["npc_id"])

        event.processed = 1
        event.processed_at = time.time()
