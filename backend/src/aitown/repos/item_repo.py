from typing import Optional, List
import sqlite3
import uuid
from pydantic import BaseModel
from aitown.repos.base import NotFoundError
from aitown.repos.interfaces import ItemRepositoryInterface
from aitown.helpers.db_helper import load_db
import enum

class ItemType(str, enum.StrEnum):
    CONSUMABLE = "CONSUMABLE"
    EQUIPMENT = "EQUIPMENT"
    MONETARY = "MONETARY"
    MISC = "MISC"

class Item(BaseModel):
    id: Optional[str] = None
    name: str
    value: int = 0
    type: str
    effect_ids: list[str] = []
    description: Optional[str] = None


class ItemRepository(ItemRepositoryInterface):
    def create(self, item: Item) -> Item:
        if not item.id:
            item.id = str(uuid.uuid4())
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO item (id, name, description) VALUES (?, ?, ?)",
                (item.id, item.name, item.description),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return item

    def get_by_id(self, id: str) -> Item:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Item not found: {id}")
        return Item(id=row["id"], name=row["name"], description=row["description"])

    def list_all(self) -> List[Item]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM item")
        rows = cur.fetchall()
        return [Item(id=r["id"], name=r["name"], description=r["description"]) for r in rows]

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM item WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Item not found: {id}")
        self.conn.commit()

ITEM_LIST = [
    # 货币
    Item(id="item_bronze_coin", name="铜币", value=1, type=ItemType.MONETARY, effect_ids=[], description="A bronze coin."),
    Item(id="item_silver_coin", name="银币", value=10, type=ItemType.MONETARY, effect_ids=[], description="A silver coin."),
    Item(id="item_gold_coin", name="金币", value=100, type=ItemType.MONETARY, effect_ids=[], description="A gold coin."),
    Item(id="item_platinum_coin", name="白金币", value=1000, type=ItemType.MONETARY, effect_ids=[], description="A platinum coin."),
    # 食物
    Item(id="item_apple", name="苹果", value=5, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_10"], description="A juicy red apple."),
    Item(id="item_bread", name="面包", value=10, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_30"], description="A loaf of fresh bread."),
    Item(id="item_hamburger", name="汉堡", value=20, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_50"], description="A piece of hamburger."),
    Item(id="item_energy_bar", name="超级能量棒", value=60, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_100"], description="A super energy bar."),
    # 饮料
    Item(id="item_water", name="水", value=2, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_5", "effect_energy_plus_5"], description="A bottle of water."),
    Item(id="item_tea", name="茶", value=5, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_10", "effect_energy_plus_10"], description="A cup of tea."),
    Item(id="item_coffee", name="咖啡", value=10, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_5", "effect_energy_plus_20"], description="A cup of coffee."),
    # 特殊食物
    Item(id="item_magic_mushroom", name="魔法蘑菇", value=100, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_50", "effect_mood_plus_50"], description="A mysterious magic mushroom."),
    Item(id="item_ambrosia", name="仙丹", value=500, type=ItemType.CONSUMABLE, 
         effect_ids=["effect_hunger_plus_100", "effect_energy_plus_100", "effect_mood_plus_100"], description="A divine ambrosia."),
]