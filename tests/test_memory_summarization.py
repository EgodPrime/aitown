import time
import os
import json
from aitown.server import services
from aitown.server import storage
from fastapi.testclient import TestClient
from aitown.server.main import app

client = TestClient(app)


def make_npc_with_memory(n_days_newer=3, n_days_older=10):
    """Create an NPC dict with memory entries: some recent, some older than 7 days."""
    npc_id = 'test-npc-' + str(int(time.time()))
    now = int(time.time())
    mem = []
    # newer entries (within 7 days)
    for i in range(n_days_newer):
        ts = now - i * 24 * 3600
        mem.append({'date': time.strftime('%Y-%m-%d', time.gmtime(ts)), 'events': [f'event recent {i}'], 'ts': ts})
    # older entries (older than 7 days)
    for i in range(n_days_older):
        ts = now - (7 + i + 1) * 24 * 3600
        mem.append({'date': time.strftime('%Y-%m-%d', time.gmtime(ts)), 'events': [f'event old {i}'], 'ts': ts})
    npc = {'id': npc_id, 'player_id': 'p1', 'name': 'tester', 'memory_log': mem}
    services.NPCS[npc_id] = npc
    return npc_id


def test_summarize_memory_no_memory():
    npc_id = 'nm-' + str(int(time.time()))
    services.NPCS[npc_id] = {'id': npc_id, 'player_id': 'p1', 'name': 'no_mem'}
    res = services.summarize_memory(npc_id)
    assert res.get('status') in ('no_memory', 'nothing_to_summarize')


def test_summarize_memory_happy_path():
    npc_id = make_npc_with_memory(n_days_newer=2, n_days_older=5)
    before = services.get_memory(npc_id)
    # ensure older entries exist
    mem_before = before.get('memory_log', [])
    assert any(e for e in mem_before if e.get('events') and 'old' in e.get('events')[0])

    res = services.summarize_memory(npc_id)
    assert res.get('status') == 'summarized'
    summary = res.get('summary_entry')
    assert isinstance(summary, dict)
    after = services.get_memory(npc_id)
    # memory_log should now contain the summary entry
    mem_after = after.get('memory_log', [])
    assert any(e for e in mem_after if e.get('id') == summary.get('id'))
    # long_term_summary should be present
    assert after.get('long_term_summary') and after.get('long_term_summary').get('id') == summary.get('id')


def test_admin_summarize_endpoint_requires_token():
    npc_id = make_npc_with_memory(n_days_newer=1, n_days_older=3)
    # without token
    resp = client.post('/admin/summarize-memory', json={'npc_id': npc_id})
    assert resp.status_code == 403


def test_admin_summarize_endpoint_with_token():
    npc_id = make_npc_with_memory(n_days_newer=1, n_days_older=3)
    # set ADMIN_TOKEN in env for this test
    token = 'admintok' + str(int(time.time()))
    os.environ['ADMIN_TOKEN'] = token
    headers = {'X-Admin-Token': token}
    resp = client.post('/admin/summarize-memory', json={'npc_id': npc_id}, headers=headers)
    # cleanup env var
    os.environ.pop('ADMIN_TOKEN', None)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get('status') in ('summarized', 'nothing_to_summarize', 'no_memory')
