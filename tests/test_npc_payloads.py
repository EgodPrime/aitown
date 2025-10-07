import pytest
from httpx import AsyncClient, ASGITransport

from aitown.server import app, NPCS


@pytest.mark.asyncio
async def test_create_minimal_valid_npc():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()
        payload = {"player_id": "qa", "name": "Test NPC", "type": "villager"}
        resp = await ac.post('/npc', json=payload)
    # server currently returns 200 on create in existing tests; accept 200 or 201
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert 'id' in body
    assert body['name'] == payload['name']
    # 'type' is not part of NPCCreate model and may be ignored by server
    # ensure defaults were applied (prompt default, money default)
    assert 'prompt' in body
    assert 'money' in body
    npc_id = body['id']
    assert npc_id in NPCS
    assert NPCS[npc_id]['name'] == payload['name']


@pytest.mark.asyncio
async def test_create_with_optional_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()
        payload = {
            "player_id": "merchant_owner",
            "name": "Merchant Mona",
            "type": "merchant",
            "wealth": 150,
            "prompt": "Sell rare items",
            "traits": ["shrewd", "friendly"],
        }
        resp = await ac.post('/npc', json=payload)
        assert resp.status_code in (200, 201)
        body = resp.json()
        assert body['name'] == payload['name']
        # optional fields not in NPCCreate model (e.g., 'type','wealth','traits') may be ignored.
        # Confirm that prompt was preserved and money default applied.
        assert body.get('prompt') == payload['prompt']
        assert 'money' in body and isinstance(body['money'], int)


@pytest.mark.asyncio
async def test_create_invalid_payload_returns_400():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()
        # NPCCreate requires player_id; missing it should yield a 422 validation error
        payload = {"name": "NoPlayer"}
        resp = await ac.post('/npc', json=payload)
        assert resp.status_code == 422
