import asyncio
import json
import os
import uuid
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List
from loguru import logger

from aitown.server.models import NPCCreate, NPCBuy, PlayerAPIConfig, PlaceIn, PLACES
from aitown.server import storage
import logging

logger = logging.getLogger(__name__)
_RAISE_ON_ERROR = os.environ.get('RAISE_ON_PERSISTENCE_ERROR') == '1'
from fastapi import HTTPException, WebSocket


# WebSocket manager (centralized here so services can broadcast)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        data = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(data)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()

# In-memory storage
NPCS: Dict[str, Dict[str, Any]] = {}
PLAYER_API_CONFIGS: Dict[str, Dict[str, Any]] = storage.load_all_configs()

# Attempt to load persisted NPCs from sqlite if configured
try:
    loaded = storage.load_all_npcs()
    if loaded:
        NPCS.update(loaded)
except Exception:
    pass

SIMULATION_INTERVAL = 2.0
simulation_running = True


async def mock_generate_action(npc: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # prevent actions for dead NPCs
    if npc.get('status') == 'dead':
        return {'action': 'noop', 'text': f"{npc.get('name','npc')} is dead", 'skipped': True}

    prompt = npc.get('prompt', '')
    player_id = npc.get('player_id')
    if player_id and PLAYER_API_CONFIGS.get(player_id):
        cfg = PLAYER_API_CONFIGS[player_id]
        return {'action': 'api_preference', 'text': f"{npc['name']} used player API ({cfg.get('api_name','custom')})", 'used_player_api': True}
    if 'work' in prompt:
        return {'action': 'work', 'text': f"{npc['name']} is working."}
    if 'talk' in prompt or 'social' in prompt:
        return {'action': 'talk', 'text': f"{npc['name']} says hello to nearby townsfolk."}
    npc['x'] += 0.5
    npc['y'] += 0.2
    # simple movement
    return {'action': 'move', 'dx': 0.5, 'dy': 0.2, 'text': f"{npc['name']} wanders."}


async def simulation_loop():
    global simulation_running
    while True:
        if not simulation_running:
            await asyncio.sleep(1)
            continue
        updates = []
        for npc_id, npc in list(NPCS.items()):
            # skip dead NPCs
            if npc.get('status') == 'dead':
                continue
            try:
                    # prioritize any forced_move recorded by owner actions
                    fm = npc.get('forced_move')
                    if fm:
                        # apply forced move: either to place coordinates or explicit x/y
                        if fm.get('place_id'):
                            place = PLACES.get(fm.get('place_id'))
                            if place and 'x' in place and 'y' in place:
                                npc['x'] = place['x']
                                npc['y'] = place['y']
                                npc['state'] = {'action': 'forced_move', 'text': f"moved to {place.get('name')}"}
                            else:
                                # unknown place: ignore forced move
                                npc['state'] = {'action': 'forced_move', 'text': 'invalid_place'}
                        elif fm.get('x') is not None and fm.get('y') is not None:
                            npc['x'] = fm.get('x')
                            npc['y'] = fm.get('y')
                            npc['state'] = {'action': 'forced_move', 'text': 'moved to coordinates'}
                        else:
                            npc['state'] = {'action': 'forced_move', 'text': 'no-op'}
                        # clear forced move and persist
                        npc.pop('forced_move', None)
                        try:
                            storage.save_npc(npc_id, npc)
                        except Exception:
                            pass
                        updates.append({'id': npc_id, 'x': npc.get('x'), 'y': npc.get('y'), 'state': npc.get('state')})
                        continue

                    action = await mock_generate_action(npc, {})
                    if action.get('action') == 'move':
                        npc['x'] = npc.get('x', 0) + action.get('dx', 0)
                        npc['y'] = npc.get('y', 0) + action.get('dy', 0)
                        npc['state'] = {'action': 'move', 'text': action.get('text')}
                    else:
                        npc['state'] = {'action': action.get('action'), 'text': action.get('text')}
                    updates.append({'id': npc_id, 'x': npc['x'], 'y': npc['y'], 'state': npc['state']})
            except Exception as e:
                print('Error in NPC action:', e)
        if updates:
            await manager.broadcast({'type': 'state_update', 'payload': updates})
        await asyncio.sleep(SIMULATION_INTERVAL)


async def simulate_step():
    updates = []
    for npc_id, npc in list(NPCS.items()):
        # skip dead NPCs
        if npc.get('status') == 'dead':
            continue
        try:
            # process any forced move first
            fm = npc.get('forced_move')
            if fm:
                if fm.get('place_id'):
                    place = PLACES.get(fm.get('place_id'))
                    if place and 'x' in place and 'y' in place:
                        npc['x'] = place['x']
                        npc['y'] = place['y']
                        npc['state'] = {'action': 'forced_move', 'text': f"moved to {place.get('name')}"}
                    else:
                        npc['state'] = {'action': 'forced_move', 'text': 'invalid_place'}
                elif fm.get('x') is not None and fm.get('y') is not None:
                    npc['x'] = fm.get('x')
                    npc['y'] = fm.get('y')
                    npc['state'] = {'action': 'forced_move', 'text': 'moved to coordinates'}
                else:
                    npc['state'] = {'action': 'forced_move', 'text': 'no-op'}
                npc.pop('forced_move', None)
                try:
                    storage.save_npc(npc_id, npc)
                except Exception:
                    pass
                updates.append({'id': npc_id, 'x': npc.get('x'), 'y': npc.get('y'), 'state': npc.get('state')})
                continue

            action = await mock_generate_action(npc, {})
            if action.get('action') == 'move':
                npc['x'] = npc.get('x', 0) + action.get('dx', 0)
                npc['y'] = npc.get('y', 0) + action.get('dy', 0)
                npc['state'] = {'action': 'move', 'text': action.get('text')}
            else:
                npc['state'] = {'action': action.get('action'), 'text': action.get('text')}
            updates.append({'id': npc_id, 'x': npc['x'], 'y': npc['y'], 'state': npc['state'], 'used_player_api': action.get('used_player_api', False)})
        except Exception as e:
            print('Error in simulate_step:', e)
    if updates:
        await manager.broadcast({'type': 'state_update', 'payload': updates})
    return {'updates': updates}


def create_npc(npc_in: NPCCreate) -> Dict[str, Any]:
    payload = npc_in.model_dump()
    player_id = payload.get('player_id')
    for existing in NPCS.values():
        if existing.get('player_id') == player_id:
            raise HTTPException(status_code=409, detail='player already has an NPC')
    npc_id = str(uuid.uuid4())
    npc = payload
    npc['id'] = npc_id
    npc['state'] = {'action': 'idle', 'text': 'created'}
    # survival and econ defaults
    npc.setdefault('money', 100)
    npc.setdefault('inventory', [])
    npc.setdefault('hunger', 100)
    npc.setdefault('energy', 100)
    npc.setdefault('mood', 100)
    npc.setdefault('status', 'alive')
    NPCS[npc_id] = npc
    try:
        storage.save_npc(npc_id, npc)
    except Exception as e:
        logger.exception('Failed to persist npc on create: {}', e)
        if _RAISE_ON_ERROR:
            raise
    return npc


def update_npc(npc_id: str, patch: Dict[str, Any], x_player_id: str | None, x_admin_token: str | None = None) -> Dict[str, Any]:
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    owner = npc.get('player_id')
    admin_token = os.environ.get('ADMIN_TOKEN')
    if x_player_id and x_player_id == owner:
        # allowed
        pass
    elif x_admin_token and admin_token and x_admin_token == admin_token:
        # admin override
        pass
    else:
        raise HTTPException(status_code=403, detail='not owner')

    # allow partial updates for allowed fields only
    allowed = {'name', 'prompt', 'x', 'y', 'metadata'}
    for k, v in patch.items():
        if k in allowed:
            npc[k] = v

    try:
        storage.save_npc(npc_id, npc)
    except Exception as e:
        logger.exception('Failed to persist npc after update_npc: {}', e)
        if _RAISE_ON_ERROR:
            raise
    return npc


def get_memory(npc_id: str) -> Dict[str, Any]:
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    # Return memory_log and optional long_term summary if present
    return {
        'memory_log': npc.get('memory_log', []),
        'long_term_summary': npc.get('long_term_summary')
    }


def summarize_memory(npc_id: str) -> Dict[str, Any]:
    """Compress memory entries older than 7 days into a long_term_summary entry.

    This is a simple, deterministic summarizer for MVP/testing that concatenates
    older entries' text into a short summary string and records the source range
    (start_date, end_date) for auditability. It persists the updated NPC.
    """
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')

    mem = npc.get('memory_log', []) or []
    if not mem:
        return {'status': 'no_memory'}

    # determine cutoff (7 days ago)
    now = int(time.time())
    seven_days = 7 * 24 * 3600
    cutoff = now - seven_days

    # entries are expected to be dicts with either 'ts' (epoch) or 'date' (ISO)
    older = []
    newer = []
    for entry in mem:
        ts = None
        if isinstance(entry, dict):
            if 'ts' in entry and isinstance(entry.get('ts'), (int, float)):
                ts = int(entry.get('ts'))
            elif 'date' in entry:
                # try to parse YYYY-MM-DD -> approximate as midnight UTC
                try:
                    parts = entry.get('date').split('-')
                    if len(parts) >= 3:
                        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
                        # crude conversion to epoch
                        ts = int(time.mktime((y, m, d, 0, 0, 0, 0, 0, 0)))
                except Exception:
                    ts = None
        if ts is None:
            # if we cannot determine a timestamp, treat as recent
            newer.append(entry)
        elif ts < cutoff:
            older.append(entry)
        else:
            newer.append(entry)

    if not older:
        # nothing to summarize
        return {'status': 'nothing_to_summarize'}

    # Build a concise summary from older entries
    texts = []
    dates = []
    for e in older:
        if isinstance(e, dict):
            dates.append(e.get('date') or e.get('ts'))
            if isinstance(e.get('events'), list):
                texts.append('; '.join(str(x) for x in e.get('events')))
            else:
                # fallback to summary or raw text
                texts.append(str(e.get('summary') or e.get('text') or ''))
        else:
            texts.append(str(e))

    summary_text = ' | '.join([t for t in texts if t])
    start = dates[0] if dates else None
    end = dates[-1] if dates else None

    summary_entry = {
        'id': str(uuid.uuid4()),
        'date': time.strftime('%Y-%m-%d', time.gmtime(cutoff)),
        'summary': summary_text,
        'source_range': {'start': start, 'end': end},
        'ts': now
    }

    # new memory log: keep newer entries then append the summary entry
    new_mem = newer + [summary_entry]
    npc['memory_log'] = new_mem
    # also set a top-level long_term_summary for quick access
    npc['long_term_summary'] = summary_entry

    try:
        storage.save_npc(npc_id, npc)
    except Exception:
        # best-effort persistence for MVP
        pass

    return {'status': 'summarized', 'summary_entry': summary_entry}


def force_move(npc_id: str, place_id: str | None = None, x: float | None = None, y: float | None = None, x_player_id: str | None = None):
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    owner = npc.get('player_id')
    if x_player_id is None or x_player_id != owner:
        raise HTTPException(status_code=403, detail='not owner')
    # record a forced move request on the npc; simulation loop can pick it up
    npc['forced_move'] = {}
    if place_id:
        npc['forced_move']['place_id'] = place_id
    if x is not None and y is not None:
        npc['forced_move']['x'] = x
        npc['forced_move']['y'] = y
    try:
        storage.save_npc(npc_id, npc)
    except Exception as e:
        logger.exception('Failed to persist npc after force_move: {}', e)
        if _RAISE_ON_ERROR:
            raise
    return {'status': 'ok', 'forced_move': npc.get('forced_move')}


def _apply_item_effect(npc: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    # simple item effects mapping
    effects = {
        'food_apple': {'hunger': +20},
        'tool_hammer': {'mood': +5}
    }
    eff = effects.get(item_id, {})
    for k, v in eff.items():
        npc[k] = max(0, min(100, npc.get(k, 0) + v))
    # after applying effects check for death
    if npc.get('hunger', 1) <= 0 or npc.get('energy', 1) <= 0:
        # mark death and record metadata
        npc['status'] = 'dead'
        npc['death'] = {'ts': time.time(), 'cause': f'attributes_depleted_after_using_{item_id}'}
    return npc


def use_item(npc_id: str, body_item_id: str, x_player_id: str | None):
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    if npc.get('status') == 'dead':
        raise HTTPException(status_code=400, detail='npc is dead')
    owner = npc.get('player_id')
    if x_player_id is None or x_player_id != owner:
        raise HTTPException(status_code=403, detail='not owner')
    # validate item id
    from aitown.server.models import ITEM_CATALOG
    if body_item_id not in ITEM_CATALOG:
        raise HTTPException(status_code=400, detail='invalid item_id')
    inv = npc.get('inventory') or []
    # find item in inventory
    idx = next((i for i, it in enumerate(inv) if it.get('item_id') == body_item_id), None)
    if idx is None:
        raise HTTPException(status_code=400, detail='item not in inventory')
    # apply effects and remove item
    _ = inv.pop(idx)
    npc['inventory'] = inv
    npc = _apply_item_effect(npc, body_item_id)
    try:
        storage.save_npc(npc_id, npc)
    except Exception as e:
        logger.exception('Failed to persist npc after use_item: {}', e)
        if _RAISE_ON_ERROR:
            raise
    return npc


def update_prompt(npc_id: str, prompt: str, x_player_id: str | None):
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    if npc.get('status') == 'dead':
        raise HTTPException(status_code=400, detail='npc is dead')
    owner = npc.get('player_id')
    if x_player_id is None or x_player_id != owner:
        raise HTTPException(status_code=403, detail='not owner')
    npc['prompt'] = prompt
    try:
        storage.save_npc(npc_id, npc)
    except Exception as e:
        logger.exception('Failed to persist npc after update_prompt: {}', e)
        if _RAISE_ON_ERROR:
            raise
    return npc


def delete_npc(npc_id: str, x_player_id: str | None, x_admin_token: str | None):
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    if npc.get('status') == 'dead':
        # allow deletion of dead NPCs by owner or admin as normal
        pass
    owner = npc.get('player_id')
    admin_token = os.environ.get('ADMIN_TOKEN')
    if x_player_id and x_player_id == owner:
        del NPCS[npc_id]
        try:
            storage.delete_npc(npc_id)
        except Exception as e:
            logger.exception('Failed to delete npc from persistence: {}', e)
            if _RAISE_ON_ERROR:
                raise
        return {'status': 'deleted'}
    if admin_token and x_admin_token and x_admin_token == admin_token:
        del NPCS[npc_id]
        try:
            storage.delete_npc(npc_id)
        except Exception as e:
            logger.exception('Failed to delete npc from persistence (admin): {}', e)
            if _RAISE_ON_ERROR:
                raise
        return {'status': 'deleted'}
    raise HTTPException(status_code=403, detail='forbidden')


def npc_buy(npc_id: str, body: NPCBuy, x_player_id: str | None):
    npc = NPCS.get(npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail='NPC not found')
    if npc.get('status') == 'dead':
        raise HTTPException(status_code=400, detail='npc is dead')
    owner = npc.get('player_id')
    if x_player_id is None or x_player_id != owner:
        raise HTTPException(status_code=403, detail='not owner')
    # validate item id
    from aitown.server.models import ITEM_CATALOG
    if body.item_id not in ITEM_CATALOG:
        raise HTTPException(status_code=400, detail='invalid item_id')
    price = None
    if body.place_id:
        place = PLACES.get(body.place_id)
        if not place:
            raise HTTPException(status_code=400, detail='invalid place_id')
        price = place.get('items', {}).get(body.item_id)
    if price is None:
        price_map = {'food_apple': 5, 'tool_hammer': 20}
        price = price_map.get(body.item_id, 1)
    if npc.get('money', 0) < price:
        raise HTTPException(status_code=400, detail='insufficient funds')
    npc['money'] = npc.get('money', 0) - price
    inv = npc.get('inventory') or []
    inv.append({'item_id': body.item_id, 'place_id': body.place_id})
    npc['inventory'] = inv
    try:
        storage.save_npc(npc_id, npc)
    except Exception:
        pass
    return npc


def set_player_api_config(player_id: str, cfg: PlayerAPIConfig):
    PLAYER_API_CONFIGS[player_id] = cfg.model_dump()
    try:
        storage.save_config(player_id, PLAYER_API_CONFIGS[player_id])
    except Exception:
        pass
    return PLAYER_API_CONFIGS[player_id]


def get_places():
    return [{'id': pid, 'name': p['name'], 'items': p.get('items', {}), 'x': p.get('x'), 'y': p.get('y')} for pid, p in PLACES.items()]


def create_or_update_place(place_id: str, payload: PlaceIn):
    PLACES[place_id] = {'name': payload.name, 'items': payload.items}
    return {'status': 'ok', 'place_id': place_id}
