import time
import json
from fastapi.testclient import TestClient
from aitown.server import app, NPCS


def test_smoke_20_npcs_simulation_steps():
    client = TestClient(app)
    NPCS.clear()

    # create 20 NPCs
    for i in range(20):
        resp = client.post('/npc', json={'player_id': f'p{i}', 'name': f'NPC{i}', 'prompt': 'wander'})
        assert resp.status_code == 200

    # connect websocket and consume initial full_state
    with client.websocket_connect('/ws') as ws:
        data = json.loads(ws.receive_text())
        assert data['type'] == 'full_state'
        assert len(data['payload']) >= 20

        # perform several simulation steps and ensure state_update broadcasts are received
        for _ in range(3):
            resp = client.post('/simulate/step')
            assert resp.status_code == 200
            # wait for broadcast
            msg = json.loads(ws.receive_text())
            assert msg['type'] == 'state_update'
            # ensure payload contains updates for many NPCs (not necessarily all)
            assert isinstance(msg['payload'], list)
            assert len(msg['payload']) > 0
