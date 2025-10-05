from fastapi.testclient import TestClient
from aitown.server import app


def test_use_item_restores_hunger():
    client = TestClient(app)
    # create npc and give it low hunger
    resp = client.post('/npc', json={'player_id': 'u1', 'name': 'Eater', 'prompt': 'wander'})
    assert resp.status_code == 200
    npc = resp.json()
    npc_id = npc['id']

    # set npc hunger low by direct mutation (tests run in same process)
    from aitown.server.services import NPCS
    NPCS[npc_id]['hunger'] = 10
    # add apple to inventory
    NPCS[npc_id]['inventory'].append({'item_id': 'food_apple', 'place_id': 'p1'})

    # use item
    resp2 = client.post(f'/npc/{npc_id}/use-item', json={'item_id': 'food_apple'}, headers={'X-Player-Id': 'u1'})
    assert resp2.status_code == 200
    new = resp2.json()['npc']
    assert new['hunger'] > 10
    assert new['status'] == 'alive'


def test_use_item_causes_death_if_zero():
    client = TestClient(app)
    resp = client.post('/npc', json={'player_id': 'u2', 'name': 'Tired', 'prompt': 'wander'})
    assert resp.status_code == 200
    npc = resp.json()
    npc_id = npc['id']

    from aitown.server.services import NPCS
    NPCS[npc_id]['hunger'] = 0
    NPCS[npc_id]['energy'] = 0
    NPCS[npc_id]['inventory'].append({'item_id': 'tool_hammer', 'place_id': 'p1'})

    # try to use non-food item; effects won't raise hunger/energy -> but since already 0, status should be dead after using
    resp2 = client.post(f'/npc/{npc_id}/use-item', json={'item_id': 'tool_hammer'}, headers={'X-Player-Id': 'u2'})
    assert resp2.status_code == 200
    new = resp2.json()['npc']
    assert new['status'] == 'dead'
