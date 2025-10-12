from __future__ import annotations

from typing import Any

import yaml

from aitown.helpers.path_helper import PROJECT_ROOT

STATIC_PATH = PROJECT_ROOT / "config" / "static_data.yaml"

RAW = {
    "town": [],
    "places": [], 
    "effects": [], 
    "items": []
    }


if STATIC_PATH.exists():
    with open(STATIC_PATH, "r", encoding="utf-8") as fh:
        RAW = yaml.safe_load(fh) or RAW

def get_towns() -> list[dict[str, Any]]:
    return RAW.get("town", [])

def get_places() -> list[dict[str, Any]]:
    return RAW.get("places", [])


def get_effects() -> list[dict[str, Any]]:
    return RAW.get("effects", [])


def get_items() -> list[dict[str, Any]]:
    return RAW.get("items", [])
