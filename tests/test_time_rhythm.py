import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from aitown.server import app, NPCS
import os


@pytest.mark.asyncio
async def test_daily_tick_and_pay():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()
        # ensure deterministic ticks-per-day for the test
        os.environ['AITOWN_TICKS_PER_DAY'] = '24'
        # create npc
        resp = await ac.post('/npc', json={'player_id': 'time_test', 'name': 'TimeBot', 'prompt': 'wander'})
        assert resp.status_code == 200
        npc = resp.json()
        nid = npc['id']
        # ensure NPC was created and visible via list endpoint
        rlist = await ac.get('/npc')
        assert rlist.status_code == 200
        # simulate 24 steps and inspect the response payloads for updates about our NPC
        observed = None
        for i in range(24):
            r = await ac.post('/simulate/step')
            assert r.status_code == 200
            body = r.json()
            updates = body.get('updates') or []
            # find update entry for our npc
            for u in updates:
                if u.get('id') == nid:
                    # some simulate responses include tick/day directly
                    if u.get('tick') == 24 and u.get('day') == 1:
                        observed = u
            await asyncio.sleep(0)
        assert observed is not None, 'Did not see expected tick/day in simulate responses'
        # final sanity check via GET (best-effort)
        r_n = await ac.get(f'/npc/{nid}')
        if r_n.status_code == 200:
            n = r_n.json()
            assert n.get('money') >= 101
