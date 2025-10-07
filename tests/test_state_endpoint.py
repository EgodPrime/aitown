import pytest
from httpx import AsyncClient, ASGITransport

from aitown.server import app, NPCS


@pytest.mark.asyncio
async def test_get_state_returns_full_state():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # clear and create two NPCs
        NPCS.clear()
        r1 = await ac.post('/npc', json={'player_id': 'state_p1', 'name': 'A'})
        assert r1.status_code in (200, 201)
        r2 = await ac.post('/npc', json={'player_id': 'state_p2', 'name': 'B'})
        assert r2.status_code in (200, 201)

        # call /state and verify response shape (type + payload list)
        rs = await ac.get('/state')
        assert rs.status_code == 200
        body = rs.json()
        assert body.get('type') == 'full_state'
        payload = body.get('payload')
        assert isinstance(payload, list)
        # cleanup to avoid interfering with other tests
        NPCS.clear()
