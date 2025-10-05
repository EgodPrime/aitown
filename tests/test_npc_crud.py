import os
import sys
import pytest
from httpx import AsyncClient, ASGITransport

import asyncio

from aitown.server import app, NPCS
from aitown.server import PLAYER_API_CONFIGS


@pytest.mark.asyncio
async def test_npc_crud_and_owner_enforcement():

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # ensure clean state
        NPCS.clear()

        # create npc for player1
        resp = await ac.post('/npc', json={
            'player_id': 'player1', 'name': 'AliceBot', 'prompt': 'wander'
        })
        assert resp.status_code == 200
        npc = resp.json()
        npc_id = npc['id']

        # creating another npc for same player should 409
        resp2 = await ac.post('/npc', json={
            'player_id': 'player1', 'name': 'AliceBot2'
        })
        assert resp2.status_code == 409

        # non-owner cannot update prompt
        resp3 = await ac.post(f'/npc/{npc_id}/prompt', json={'prompt': 'work hard'})
        assert resp3.status_code == 403

        # owner can update prompt via header X-Player-Id
        resp4 = await ac.post(f'/npc/{npc_id}/prompt', json={'prompt': 'work hard'}, headers={'X-Player-Id': 'player1'})
        assert resp4.status_code == 200
        assert resp4.json()['prompt'] == 'work hard'

        # non-owner cannot delete
        resp5 = await ac.delete(f'/npc/{npc_id}', headers={'X-Player-Id': 'someoneelse'})
        assert resp5.status_code == 403

        # owner can delete
        resp6 = await ac.delete(f'/npc/{npc_id}', headers={'X-Player-Id': 'player1'})
        assert resp6.status_code == 200
        assert resp6.json()['status'] == 'deleted'


@pytest.mark.asyncio
async def test_player_api_config_storage():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # ensure clean state
        PLAYER_API_CONFIGS.clear()

        # set player api config
        resp = await ac.post('/player/player42/api-config', json={'api_name': 'mockplayer', 'token': 'sekret'})
        assert resp.status_code == 200
        assert resp.json()['status'] == 'ok'
        # the server in-memory map should be updated
        assert 'player42' in PLAYER_API_CONFIGS
        assert PLAYER_API_CONFIGS['player42']['api_name'] == 'mockplayer'


@pytest.mark.asyncio
async def test_simulation_uses_player_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # clean state
        NPCS.clear()
        PLAYER_API_CONFIGS.clear()

        # set player api config
        resp = await ac.post('/player/player9/api-config', json={'api_name': 'playerapi', 'token': 't'})
        assert resp.status_code == 200

        # create npc for player9
        resp2 = await ac.post('/npc', json={'player_id': 'player9', 'name': 'P9Bot', 'prompt': 'wander'})
        assert resp2.status_code == 200
        npc = resp2.json()
        npc_id = npc['id']

        # run one simulation step
        resp3 = await ac.post('/simulate/step')
        assert resp3.status_code == 200
        data = resp3.json()
        updates = data.get('updates', [])
        # find our npc update
        found = None
        for u in updates:
            if u.get('id') == npc_id:
                found = u
                break
        assert found is not None
        assert found.get('used_player_api') is True


@pytest.mark.asyncio
async def test_npc_buy_behavior():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()

        # create npc for buyer
        resp = await ac.post('/npc', json={'player_id': 'buyer', 'name': 'BuyerBot', 'prompt': 'wander'})
        assert resp.status_code == 200
        npc = resp.json()
        npc_id = npc['id']

        # non-owner cannot buy
        resp2 = await ac.post(f'/npc/{npc_id}/buy', json={'item_id': 'food_apple'})
        assert resp2.status_code == 403

        # owner can buy an affordable item
        resp3 = await ac.post(f'/npc/{npc_id}/buy', json={'item_id': 'food_apple'}, headers={'X-Player-Id': 'buyer'})
        assert resp3.status_code == 200
        body = resp3.json()
        assert body['status'] == 'ok'
        assert any(i['item_id'] == 'food_apple' for i in body['npc']['inventory'])
        # owner money should be deducted
        assert body['npc']['money'] == 95

        # attempt to buy expensive item with insufficient funds
        # drain funds
        body['npc']['money'] = 0
        NPCS[npc_id] = body['npc']
        resp4 = await ac.post(f'/npc/{npc_id}/buy', json={'item_id': 'tool_hammer'}, headers={'X-Player-Id': 'buyer'})
        assert resp4.status_code == 400
        assert resp4.json()['detail'] == 'insufficient funds'


@pytest.mark.asyncio
async def test_places_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        # get places
        resp = await ac.get('/places')
        assert resp.status_code == 200
        places = resp.json()
        assert any(p['id'] == 'p1' for p in places)

        # attempt to create a new place without admin token should fail if ADMIN_TOKEN is set
        old_admin = os.environ.get('ADMIN_TOKEN')
        os.environ['ADMIN_TOKEN'] = 'tok'
        resp2 = await ac.post('/places/p2', json={'name': 'Shop', 'items': {'water': 2}})
        assert resp2.status_code == 403
        # provide admin token
        resp3 = await ac.post('/places/p2', json={'name': 'Shop', 'items': {'water': 2}}, headers={'X-Admin-Token': 'tok'})
        assert resp3.status_code == 200
        # cleanup
        if old_admin is None:
            del os.environ['ADMIN_TOKEN']
        else:
            os.environ['ADMIN_TOKEN'] = old_admin

@pytest.mark.asyncio
async def test_npc_buy_with_place_pricing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        NPCS.clear()

        # create npc with default money 100
        resp = await ac.post('/npc', json={'player_id': 'shopper', 'name': 'ShopperBot', 'prompt': 'wander'})
        assert resp.status_code == 200
        npc = resp.json()
        npc_id = npc['id']

        # buy from place p1 where food_apple price is 5
        resp2 = await ac.post(f'/npc/{npc_id}/buy', json={'item_id': 'food_apple', 'place_id': 'p1'}, headers={'X-Player-Id': 'shopper'})
        assert resp2.status_code == 200
        body = resp2.json()
        assert body['npc']['money'] == 95
        assert any(i['item_id'] == 'food_apple' for i in body['npc']['inventory'])
