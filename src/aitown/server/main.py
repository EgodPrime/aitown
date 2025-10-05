"""Thin FastAPI routing layer.

This module delegates data models to `models` and business logic + state
to `services`. The goal is to keep routing and app configuration here while
the core behavior lives in `services.py` to make testing and maintenance
easier.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Header
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import json
import os
from typing import Dict, Any, List

from aitown.server import models, services
from loguru import logger
from fastapi import Request


app = FastAPI()


@app.middleware('http')
async def log_requests(request: Request, call_next):
	try:
		body = await request.body()
		if body:
			try:
				logger.info('Incoming request {} {} - body={}', request.method, request.url.path, body.decode('utf-8'))
			except Exception:
				logger.info('Incoming request {} {} - body(binary)', request.method, request.url.path)
	except Exception:
		# best-effort logging
		pass
	return await call_next(request)


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


# expose service state under the old names for tests/compatibility
NPCS = services.NPCS
PLAYER_API_CONFIGS = services.PLAYER_API_CONFIGS
PLACES = models.PLACES


@app.get('/places')
async def get_places():
	return services.get_places()


@app.post('/places/{place_id}')
async def create_or_update_place(place_id: str, payload: models.PlaceIn, x_admin_token: str = Header(None)):
	# simplistic admin protection via ADMIN_TOKEN env var
	admin_token = os.environ.get('ADMIN_TOKEN')
	if admin_token and x_admin_token != admin_token:
		raise HTTPException(status_code=403, detail='admin token required')
	return services.create_or_update_place(place_id, payload)


# Lifespan: start the simulation loop from services
simulation_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
	global simulation_task
	simulation_task = asyncio.create_task(services.simulation_loop())
	try:
		yield
	finally:
		if simulation_task:
			simulation_task.cancel()


app.router.lifespan_context = lifespan


@app.post('/simulate/step')
async def simulate_step():
	"""Run one simulation step synchronously for testing."""
	return await services.simulate_step()


@app.post('/npc')
async def create_npc(npc_in: models.NPCCreate):
	npc = services.create_npc(npc_in)
	await services.manager.broadcast({'type': 'npc_created', 'payload': npc})
	return npc


@app.get('/npc')
async def list_npcs():
	return list(NPCS.values())


@app.get('/npc/{npc_id}')
async def get_npc(npc_id: str):
	npc = NPCS.get(npc_id)
	if not npc:
		raise HTTPException(status_code=404, detail='NPC not found')
	return npc


@app.post('/npc/{npc_id}/prompt')
async def update_prompt(npc_id: str, upd: models.NPCUpdatePrompt, x_player_id: str = Header(None)):
	npc = services.update_prompt(npc_id, upd.prompt, x_player_id)
	await services.manager.broadcast({'type': 'npc_updated', 'payload': npc})
	return npc


@app.patch('/npc/{npc_id}')
async def patch_npc(npc_id: str, patch: dict, x_player_id: str = Header(None), x_admin_token: str = Header(None)):
	npc = services.update_npc(npc_id, patch, x_player_id, x_admin_token)
	await services.manager.broadcast({'type': 'npc_updated', 'payload': npc})
	return npc


@app.post('/npc/{npc_id}/buy')
async def npc_buy(npc_id: str, body: models.NPCBuy, x_player_id: str = Header(None)):
	npc = services.npc_buy(npc_id, body, x_player_id)
	await services.manager.broadcast({'type': 'npc_updated', 'payload': npc})
	return {'status': 'ok', 'npc': npc}


@app.delete('/npc/{npc_id}')
async def delete_npc(npc_id: str, x_player_id: str = Header(None), x_admin_token: str = Header(None)):
	res = services.delete_npc(npc_id, x_player_id, x_admin_token)
	if res.get('status') == 'deleted':
		await services.manager.broadcast({'type': 'npc_deleted', 'payload': {'id': npc_id}})
	return res


@app.post('/npc/{npc_id}/use-item')
async def npc_use_item(npc_id: str, body: models.NPCUseItem, x_player_id: str = Header(None)):
	npc = services.use_item(npc_id, body.item_id, x_player_id)
	# broadcast death or updated
	if npc.get('status') == 'dead':
		await services.manager.broadcast({'type': 'npc_died', 'payload': {'id': npc_id}})
	else:
		await services.manager.broadcast({'type': 'npc_updated', 'payload': npc})
	return {'status': 'ok', 'npc': npc}


@app.get('/npc/{npc_id}/memory')
async def get_npc_memory(npc_id: str):
	return services.get_memory(npc_id)


@app.post('/npc/{npc_id}/move')
async def post_npc_move(npc_id: str, body: dict, x_player_id: str = Header(None)):
	# body can be {place_id} or {x,y}
	place_id = body.get('place_id')
	x = body.get('x')
	y = body.get('y')
	return services.force_move(npc_id, place_id=place_id, x=x, y=y, x_player_id=x_player_id)


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket):
	await services.manager.connect(websocket)
	try:
		# send initial full state
		await websocket.send_text(json.dumps({'type': 'full_state', 'payload': list(NPCS.values())}))
		while True:
			msg = await websocket.receive_text()
			try:
				data = json.loads(msg)
				# handle control messages (pause/start)
				if data.get('type') == 'control':
					# control messages must include admin_token matching ADMIN_TOKEN env var
					admin_token = os.environ.get('ADMIN_TOKEN')
					provided = data.get('admin_token')
					if not admin_token or provided != admin_token:
						# ignore and optionally inform sender
						await websocket.send_text(json.dumps({'type': 'error', 'detail': 'admin token required for control'}))
						continue
					action = data.get('action')
					if action == 'pause':
						services.simulation_running = False
						await services.manager.broadcast({'type': 'simulation_paused'})
					if action == 'start':
						services.simulation_running = True
						await services.manager.broadcast({'type': 'simulation_started'})
			except Exception:
				# ignore non-json messages
				pass
	except WebSocketDisconnect:
		services.manager.disconnect(websocket)


# Simple index for quick manual test
@app.get('/')
async def index():
	# serve the simple static frontend if available
	try:
		path = os.path.join(os.path.dirname(__file__), '..', 'web', 'index.html')
		with open(path, 'r', encoding='utf-8') as fh:
			return HTMLResponse(fh.read())
	except Exception:
		return HTMLResponse('<h1>AI Town Simulation Backend</h1>')


@app.post('/player/{player_id}/api-config')
async def set_player_api_config(player_id: str, cfg: models.PlayerAPIConfig):
	services.set_player_api_config(player_id, cfg)
	return {'status': 'ok', 'player_id': player_id}


@app.post('/admin/simulation/pause')
async def admin_pause(x_admin_token: str = Header(None)):
	admin_token = os.environ.get('ADMIN_TOKEN')
	if not admin_token or x_admin_token != admin_token:
		raise HTTPException(status_code=403, detail='admin token required')
	services.simulation_running = False
	await services.manager.broadcast({'type': 'simulation_paused'})
	return {'status': 'paused'}


@app.post('/admin/simulation/start')
async def admin_start(x_admin_token: str = Header(None)):
	admin_token = os.environ.get('ADMIN_TOKEN')
	if not admin_token or x_admin_token != admin_token:
		raise HTTPException(status_code=403, detail='admin token required')
	services.simulation_running = True
	await services.manager.broadcast({'type': 'simulation_started'})
	return {'status': 'started'}


@app.post('/admin/summarize-memory')
async def admin_summarize_memory(body: dict, x_admin_token: str = Header(None)):
	"""Admin endpoint to trigger memory summarization for an NPC.

	Body should be: { "npc_id": "<id>" }
	"""
	admin_token = os.environ.get('ADMIN_TOKEN')
	if not admin_token or x_admin_token != admin_token:
		raise HTTPException(status_code=403, detail='admin token required')
	npc_id = body.get('npc_id')
	if not npc_id:
		raise HTTPException(status_code=400, detail='npc_id required')
	res = services.summarize_memory(npc_id)
	# broadcast updated npc if summarization succeeded
	if res.get('status') == 'summarized':
		npc = services.NPCS.get(npc_id)
		if npc:
			await services.manager.broadcast({'type': 'npc_updated', 'payload': npc})
	return res


__all__ = ["app", "NPCS"]
