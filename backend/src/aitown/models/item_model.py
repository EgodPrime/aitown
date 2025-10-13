"""Item model extracted from repos/item_repo.py"""
import enum
from typing import Optional
from pydantic import BaseModel, Field


class ItemType(enum.StrEnum):
    CONSUMABLE = "CONSUMABLE"
    EQUIPMENT = "EQUIPMENT"
    MONETARY = "MONETARY"
    MISC = "MISC"


class Item(BaseModel):
    id: Optional[int] = None
    name: str
    value: int = 0
    type: str = ItemType.MISC
    effect_ids: list[str] = Field(default_factory=list)
    description: Optional[str] = None
