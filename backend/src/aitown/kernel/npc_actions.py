import datetime
from aitown.repos.event_repo import Event
from aitown.repos.npc_repo import NPC, NpcRepository, NPCStatus
from aitown.repos.item_repo import Item, ItemRepository, ItemType
from aitown.repos.effect_repo import Effect, EffectRepository
from aitown.repos.place_repo import Place, PlaceRepository, PlaceTag
from aitown.repos.memory_repo import MemoryEntry, MemoryEntryRepository
from aitown.helpers.db_helper import load_db

class ActionExecutor:
    """
    move, eat, sleep, work, buy, sell, idle

    所有动作的流程都是：
    1. 检查前置条件（如位置、物品、状态等）
    2. 生成事件描述消息
    3. 广播消息（TODO）
    4. 生成记忆条目
    5. 更新NPC状态（位置、属性、物品等）
    6. 保存记忆条目到数据库
    7. 标记事件为已处理
    """
    conn = load_db()
    npc_repo: NpcRepository = NpcRepository(conn)
    item_repo: ItemRepository = ItemRepository(conn)
    effect_repo: EffectRepository = EffectRepository(conn)
    place_repo: PlaceRepository = PlaceRepository(conn)
    memory_repo: MemoryEntryRepository = MemoryEntryRepository(conn)



    @staticmethod
    def move(npc_id: str, place_id: str):
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        from_place = PlaceRepository().get_by_id(npc.location_id)
        to_place = PlaceRepository().get_by_id(place_id)

        # TODO: 检查两地是否相邻

        msg = f"{npc.name} 从 {from_place.name} 移动到 {to_place.name}"

        # TODO: 广播事件 

        me = MemoryEntry(npc_id=npc.id, content=msg, created_at=datetime.datetime.now().isoformat())
        
        ActionExecutor.npc_repo.update(npc_id, {"location_id": place_id})

        ActionExecutor.memory_repo.create(me)

    @staticmethod
    def eat(npc_id: str, item_id: str, item_amount: int):
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        inventory = npc.inventory
        item = ActionExecutor.item_repo.get_by_id(item_id)

        if item_id not in inventory or inventory[item_id] < item_amount or item.type != ItemType.CONSUMABLE:
            # TODO : 退回闲逛
            msg = f"{npc.name} 想吃 {item.name} x{item_amount}，这显然是在做梦"
            pass
        
        msg = f"{npc.name} 吃了 {item.name} x{item_amount}"

        # TODO : 广播事件

        me = MemoryEntry(npc_id=npc.id, content=msg, created_at=datetime.datetime.now().isoformat())
        
        for eff_id in item.effect_ids:
            eff = ActionExecutor.effect_repo.get_by_id(eff_id)
            eff.apply_to_npc(npc_id, item_amount)

        ActionExecutor.memory_repo.create(me)

    @staticmethod
    def sleep(npc_id: str, duration_hours: int):
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

        me = MemoryEntry(npc_id=npc.id, content=msg, created_at=datetime.datetime.now().isoformat())

        ActionExecutor.npc_repo.update(npc_id, {
            "energy": min(npc.energy + int(energy_recovered), 100),
            "mood": min(npc.mood + int(mood_recovered), 100),
            "status": NPCStatus.SLEEPING
        })

        ActionExecutor.memory_repo.create(me)

    @staticmethod
    def work(npc_id: str, duration_hours: int):
        """
        在有WORKABLE标签的地点工作，消耗energy和mood，获得金钱
        """
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)
        inventory = npc.inventory


        energy_cost = 10 * duration_hours
        mood_cost = 5 * duration_hours
        money_earned = 20 * duration_hours

        platinum_coins = money_earned // 1000
        gold_coins = (money_earned % 1000) // 100
        silver_coins = (money_earned % 100) // 10
        bronze_coins = money_earned % 10

        add_to_inventory = [
            {"item_id": "item_platinum_coin", "amount": platinum_coins},
            {"item_id": "item_gold_coin", "amount": gold_coins},
            {"item_id": "item_silver_coin", "amount": silver_coins},
            {"item_id": "item_bronze_coin", "amount": bronze_coins},
        ]

        for entry in add_to_inventory:
            if entry["amount"] <= 0:
                continue
            if entry["item_id"] in inventory:
                inventory[entry["item_id"]] += entry["amount"]
            else:
                inventory[entry["item_id"]] = entry["amount"]

        

        if PlaceTag.WORKABLE not in place.tags:
            # TODO : 退回闲逛
            msg = f"{npc.name} 想在 {place.name} 工作 {duration_hours} 小时，可惜这里没有工作岗位"
            pass

        if npc.energy < energy_cost or npc.mood < mood_cost:
            # TODO : 退回闲逛
            msg = f"{npc.name} 想在 {place.name} 工作 {duration_hours} 小时，但精力或心情不足"
            pass
        
        msg = f"{npc.name} 在 {place.name} 开始了 {duration_hours} 小时的工作，预计赚取 {money_earned} 金币"
        # TODO : 广播事件

        me = MemoryEntry(npc_id=npc.id, content=msg, created_at=datetime.datetime.now().isoformat())

        ActionExecutor.npc_repo.update(npc_id, {
            "energy": max(npc.energy - energy_cost, 0),
            "mood": max(npc.mood - mood_cost, 0),
            "inventory": inventory,
        })

        ActionExecutor.memory_repo.create(me)
        

    @staticmethod
    def buy(npc_id: str, item_id: str, item_amount: int):
        pass

    @staticmethod
    def sell(npc_id: str, item_id: str, item_amount: int):
        pass

    @staticmethod
    def idle(npc_id: str):
        npc = ActionExecutor.npc_repo.get_by_id(npc_id)
        place = ActionExecutor.place_repo.get_by_id(npc.location_id)

        msg = f"{npc.name} 在 {place.name} 放松了一下， 心情变好了"

        me = MemoryEntry(npc_id=npc.id, content=msg, created_at=datetime.datetime.now().isoformat())

        ActionExecutor.npc_repo.update(npc_id, {"mood": min(npc.mood + 10, 100)})
        ActionExecutor.memory_repo.create(me)

    @staticmethod
    def event_listener(event: Event):
        payload = event.payload
        action_type = payload.get("action_type")
        match action_type:
            case "move":
                ActionExecutor.move(payload["npc_id"], payload["place_id"])
            case "eat":
                ActionExecutor.eat(payload["npc_id"], payload["item_id"], payload["item_amount"])
            case "sleep":
                ActionExecutor.sleep(payload["npc_id"], payload["duration_hours"])
            case "work":
                ActionExecutor.work(payload["npc_id"], payload["duration_hours"])
            case "buy":
                ActionExecutor.buy(payload["npc_id"], payload["item_id"], payload["item_amount"])
            case "sell":
                ActionExecutor.sell(payload["npc_id"], payload["item_id"], payload["item_amount"])
            case "idle":
                ActionExecutor.idle(payload["npc_id"])
            case _:
                pass
        event.processed = 1
        event.processed_at = datetime.datetime.now().isoformat()
                

