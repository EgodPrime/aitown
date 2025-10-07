Implementation notes for Story 08 (flows):

- `POST /npc` is implemented in `src/aitown/server/main.py` and broadcasts `npc_created` via WebSocket `/ws` after creating the NPC.
- The simulation loop lives in `src/aitown/server/services.py` and broadcasts `state_update` messages.
- Simulation interval is configurable via environment variable `AITOWN_SIMULATION_INTERVAL`. During development/tests the default is 2.0s to keep tests fast; recommended production value is 90.0s.

How to set production interval example:

```bash
export AITOWN_SIMULATION_INTERVAL=90
uvicorn aitown.server.main:app --host 0.0.0.0 --port 8000
```
