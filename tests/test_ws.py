import json
from fastapi.testclient import TestClient
from aitown.server import app, NPCS


def test_ws_broadcast_on_create():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        data = ws.receive_text()
        msg = json.loads(data)
        assert msg["type"] == "full_state"

        # create npc
        resp = client.post("/npc", json={"player_id": "p1", "name": "TestNPC", "prompt": "wander"})
        assert resp.status_code == 200
        created = resp.json()

        # receive broadcast about creation
        data2 = ws.receive_text()
        msg2 = json.loads(data2)
        assert msg2["type"] == "npc_created"
        assert msg2["payload"]["id"] == created["id"]


def test_ws_state_update_on_simulate_step():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        _ = json.loads(ws.receive_text())

        # create npc
        resp = client.post("/npc", json={"player_id": "p2", "name": "Walker", "prompt": "wander"})
        assert resp.status_code == 200
        created = resp.json()

        # consume npc_created broadcast
        _ = json.loads(ws.receive_text())

        # run one simulation step
        resp2 = client.post("/simulate/step")
        assert resp2.status_code == 200

        # receive state_update broadcast
        data = ws.receive_text()
        msg = json.loads(data)
        assert msg["type"] == "state_update"
        ids = [u["id"] for u in msg["payload"]]
        assert created["id"] in ids
