import pytest
from fastapi.testclient import TestClient
from aitown.server import app, NPCS


def test_buy_with_invalid_item_id():
    client = TestClient(app)
    NPCS.clear()
    resp = client.post('/npc', json={'player_id': 'v1', 'name': 'V1'})
    assert resp.status_code == 200
    npc = resp.json()
    npc_id = npc['id']

    # invalid item
    resp2 = client.post(f'/npc/{npc_id}/buy', json={'item_id': 'nonexistent'}, headers={'X-Player-Id': 'v1'})
    assert resp2.status_code == 400
    assert resp2.json()['detail'] == 'invalid item_id'


def test_buy_with_invalid_place_id():
    client = TestClient(app)
    NPCS.clear()
    resp = client.post('/npc', json={'player_id': 'v2', 'name': 'V2'})
    assert resp.status_code == 200
    npc = resp.json()
    npc_id = npc['id']

    # known item but unknown place
    resp2 = client.post(f'/npc/{npc_id}/buy', json={'item_id': 'food_apple', 'place_id': 'bad_place'}, headers={'X-Player-Id': 'v2'})
    assert resp2.status_code == 400
    assert resp2.json()['detail'] == 'invalid place_id'
