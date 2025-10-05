import json
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient
import importlib
import sys


def test_sqlite_persistence(tmp_path, monkeypatch):
    # create temp sqlite path
    db_path = tmp_path / 'test_aitown.db'
    monkeypatch.setenv('SQLITE_DB_PATH', str(db_path))

    # reload storage and services modules to pick up env var
    import aitown.server.storage as storage
    importlib.reload(storage)
    import aitown.server.services as services
    importlib.reload(services)

    from aitown.server.main import app
    client = TestClient(app)

    # create an NPC via services.create_npc and ensure it's persisted
    from aitown.server.models import NPCCreate
    npc = services.create_npc(NPCCreate(player_id='p_sql', name='Persist', prompt='wander'))
    nid = npc['id']

    # check sqlite directly
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute('SELECT data FROM npcs WHERE npc_id = ?', (nid,))
    row = cur.fetchone()
    conn.close()
    assert row is not None
    data = json.loads(row[0])
    assert data['id'] == nid

    # update npc and ensure save
    npc2 = services.npc_buy(nid, services.NPCBuy(item_id='food_apple'), 'p_sql')
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute('SELECT data FROM npcs WHERE npc_id = ?', (nid,))
    row2 = cur.fetchone()
    conn.close()
    assert row2 is not None
    data2 = json.loads(row2[0])
    assert any(it['item_id'] == 'food_apple' for it in data2.get('inventory', []))

    # test player config persistence
    cfg = {'api_name': 'custom', 'token': 'abc123'}
    storage.save_config('p_sql', cfg)
    # reload storage layer
    importlib.reload(storage)
    loaded = storage.load_all_configs()
    assert loaded.get('p_sql', {}).get('api_name') == 'custom'
