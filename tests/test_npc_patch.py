from fastapi.testclient import TestClient
from aitown.server import app, NPCS


def test_patch_npc_owner_can_update():
    client = TestClient(app)
    NPCS.clear()
    resp = client.post('/npc', json={'player_id': 'patcher', 'name': 'Patcher'})
    assert resp.status_code == 200
    npc = resp.json()
    npc_id = npc['id']

    # non-owner cannot patch
    resp2 = client.patch(f'/npc/{npc_id}', json={'name': 'Hacker'})
    assert resp2.status_code == 403

    # owner can patch
    resp3 = client.patch(f'/npc/{npc_id}', json={'name': 'Renamed'}, headers={'X-Player-Id': 'patcher'})
    assert resp3.status_code == 200
    assert resp3.json()['name'] == 'Renamed'


def test_patch_npc_admin_can_update():
    client = TestClient(app)
    NPCS.clear()
    resp = client.post('/npc', json={'player_id': 'owner1', 'name': 'OwnerOne'})
    npc = resp.json()
    npc_id = npc['id']

    old = None
    import os
    old = os.environ.get('ADMIN_TOKEN')
    os.environ['ADMIN_TOKEN'] = 'adm'
    try:
        resp2 = client.patch(f'/npc/{npc_id}', json={'prompt': 'work'}, headers={'X-Admin-Token': 'adm'})
        assert resp2.status_code == 200
        assert resp2.json()['prompt'] == 'work'
    finally:
        if old is None:
            del os.environ['ADMIN_TOKEN']
        else:
            os.environ['ADMIN_TOKEN'] = old
