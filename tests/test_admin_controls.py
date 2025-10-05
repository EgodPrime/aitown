import os
import json
from fastapi.testclient import TestClient
from aitown.server import app, services


def test_ws_control_requires_admin_token():
    client = TestClient(app)
    # ensure sim running
    services.simulation_running = True
    with client.websocket_connect('/ws') as ws:
        _ = json.loads(ws.receive_text())
        # send control without admin token
        ws.send_text(json.dumps({'type': 'control', 'action': 'pause'}))
        msg = json.loads(ws.receive_text())
        assert msg.get('type') == 'error'
        assert 'admin token required' in msg.get('detail')
        # simulation should still be running
        assert services.simulation_running is True


def test_admin_http_pause_start():
    client = TestClient(app)
    old = os.environ.get('ADMIN_TOKEN')
    os.environ['ADMIN_TOKEN'] = 'admintok'
    try:
        # pause without header should fail
        resp = client.post('/admin/simulation/pause')
        assert resp.status_code == 403

        # pause with header should succeed
        resp2 = client.post('/admin/simulation/pause', headers={'X-Admin-Token': 'admintok'})
        assert resp2.status_code == 200
        assert resp2.json()['status'] == 'paused'
        assert services.simulation_running is False

        # start with header
        resp3 = client.post('/admin/simulation/start', headers={'X-Admin-Token': 'admintok'})
        assert resp3.status_code == 200
        assert resp3.json()['status'] == 'started'
        assert services.simulation_running is True
    finally:
        if old is None:
            del os.environ['ADMIN_TOKEN']
        else:
            os.environ['ADMIN_TOKEN'] = old
