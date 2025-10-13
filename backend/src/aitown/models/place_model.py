"""Place model extracted from repos/place_repo.py"""
from typing import List, Optional
from pydantic import BaseModel, Field
import enum


class PlaceTag(enum.StrEnum):
    SHOP = "SHOP"
    HOUSE = "HOUSE"
    ENTERTAINMENT = "ENTERTAINMENT"
    WORKABLE = "WORKABLE"


class Place(BaseModel):
    id: Optional[int] = None
    name: str
    tags: List[str] = Field(default_factory=list)
    shop_inventory: List[str] = Field(default_factory=list)
