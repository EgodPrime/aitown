"""Utility helpers for in-game currency operations.

This module provides helpers to compute total coin value, split amounts into
coin denominations, and deduct costs from an inventory preferring lower
denominations first (to keep behavior consistent with existing tests).
"""

COIN_VALUES = {
    "item_platinum_coin": 1000,
    "item_gold_coin": 100,
    "item_silver_coin": 10,
    "item_bronze_coin": 1,
}


def total_value(inventory: dict) -> int:
    """Return total monetary value represented by coin items in inventory."""
    total = 0
    for cid, val in COIN_VALUES.items():
        if cid in inventory:
            total += inventory[cid] * val
    return total


def split_amount_to_coins(amount: int) -> dict:
    """Split integer amount into coin denominations (largest-first).

    Returns a dict mapping coin_id -> count.
    """
    result = {}
    remaining = amount
    for cid, val in sorted(COIN_VALUES.items(), key=lambda x: -x[1]):
        if remaining <= 0:
            result[cid] = 0
            continue
        cnt = remaining // val
        result[cid] = cnt
        remaining -= cnt * val
    return result


def deduct_cost_low_first(inventory: dict, cost: int) -> tuple[dict, bool]:
    """Attempt to deduct `cost` from `inventory` using low-value-first coins.

    Returns (new_inventory, success). The original inventory dict is copied.
    """
    inv = dict(inventory or {})
    remaining = cost
    # iterate from smallest to largest denomination
    for cid, val in sorted(COIN_VALUES.items(), key=lambda x: x[1]):
        if cid not in inv or inv[cid] <= 0:
            continue
        needed = remaining // val
        if needed <= 0:
            continue
        use = min(needed, inv[cid])
        inv[cid] -= use
        remaining -= use * val
    success = remaining <= 0
    return inv, success
