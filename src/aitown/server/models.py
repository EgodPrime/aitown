from pydantic import BaseModel
from typing import Dict, Any


class NPCCreate(BaseModel):
    player_id: str
    name: str
    prompt: str = "wander around"
    x: float = 0.0
    y: float = 0.0
    metadata: Dict[str, Any] = {}


class NPCUpdatePrompt(BaseModel):
    prompt: str


class NPCBuy(BaseModel):
    item_id: str
    place_id: str | None = None


class NPCUseItem(BaseModel):
    item_id: str


class PlayerAPIConfig(BaseModel):
    api_name: str | None = None
    token: str | None = None


class PlaceIn(BaseModel):
    name: str
    items: Dict[str, int] = {}


# Simple in-memory places/catalog: place_id -> items -> price
# Each place now includes coordinates (x,y) to support the textual map.
PLACES: Dict[str, Dict[str, Any]] = {
    'market': {'name': 'Market', 'items': {'food_apple': 5, 'tool_hammer': 20}, 'x': 12, 'y': 5},
    'p1': {'name': 'Market', 'items': {'food_apple': 5, 'tool_hammer': 20}, 'x': 12, 'y': 5},
    'plaza': {'name': 'Plaza', 'items': {}, 'x': 13, 'y': 5},
    'bakery': {'name': 'Bakery', 'items': {'food_apple': 4}, 'x': 11, 'y': 5},
    'inn': {'name': 'Inn', 'items': {}, 'x': 12, 'y': 6},
    'shop': {'name': 'Shop', 'items': {'water': 2}, 'x': 14, 'y': 5},
    'p2': {'name': 'Shop', 'items': {'water': 2}, 'x': 14, 'y': 5},
    'park': {'name': 'Park', 'items': {}, 'x': 12, 'y': 4}
}

# Canonical item catalog for validation
ITEM_CATALOG = {
    'food_apple': {'type': 'food', 'base_price': 5},
    'tool_hammer': {'type': 'tool', 'base_price': 20}
}
