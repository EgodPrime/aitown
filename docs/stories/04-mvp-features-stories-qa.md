## QA Results

Reviewer: qa

Summary:
- I executed the project's automated tests and reviewed the implementation for NPC CRUD, survival/death rules, and economy/item flows described in this story.

Test run:
- Command: uv run pytest -q
- Result: 11 passed (full-suite run during review)

Findings:
- NPC CRUD: `POST /npc`, `GET /npc`, and `GET /npc/{id}` exist and return the expected fields including `hunger`, `energy`, `mood`, `money`, and `inventory`.
- Survival & Death: When `hunger` or `energy` reach 0 the NPC is marked `status: 'dead'` and the code broadcasts `npc_died` (tests cover death-related flows). Death metadata (`death.ts`, `death.cause`) is recorded and included in state payloads.
- Economy & Items: `POST /npc/{id}/buy` deducts money and appends items to inventory. `POST /npc/{id}/use-item` removes items, applies simple item effects (e.g., `food_apple` restores hunger), and can trigger death if attributes are depleted.
- Persistence: Optional SQLite persistence was added and exercised by tests that create a temporary DB. Player API configs and NPCs are saved to the DB when `SQLITE_DB_PATH` is set; code also falls back to JSON file persistence and does not crash when DB is unavailable.

Risks / Concerns:
- Persistence is best-effort: storage calls swallow exceptions to avoid crashing the in-memory dev/test flow. For production, I recommend surfacing errors or adding retries/alerts.
- Validation: Item IDs and place IDs are validated against in-memory PLACES only in a limited fashion. Consider stronger input validation and clearer error messages.
- Concurrency & Deploy: Current in-memory state + sqlite file access is not safe for multi-process production (use a networked DB or shared cache for scaled deployments).

Gate Decision: PASS (with concerns)

Rationale:
- All automated tests for this story and the full suite passed during the review run. The implemented behavior matches the acceptance criteria for NPC CRUD, death handling, and economy/item flows. The concerns listed are non-blocking for merging to a development branch but should be addressed before production.

Recommended Next Steps:
1. Harden persistence: add robust DB error handling, migrations, and an option for a networked DB (Postgres/Redis) for multi-process safety.
2. Improve validation for item/place IDs and add clearer error responses.
3. Add integration tests that validate WebSocket broadcasts in a realistic client scenario and across process restarts.
4. Consider a `resurrect` admin endpoint or a lifecycle policy for dead NPCs if required by product.

QA Status: PASS (with concerns)
