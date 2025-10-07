# Cohesion Report — Solutioning Quality Gate

## Scope
This report checks basic cohesion between `docs/prd.md`, `docs/tech-spec.md`, `docs/solution-architecture.md`, and per-epic tech-specs (A..D).

## Summary
- Overall: Good alignment for Level 2 MVP. PRD requirements map cleanly to epics and per-epic tech-specs.
- Outstanding gaps (recommended follow-ups listed):
  1. Persistence contract: PRD mentions optional SQLite for durability; tech-spec lists it as optional but no migration or schema file exists. Recommend adding a minimal `schema.sql` or Prisma schema and a short persistence README.
  2. LLM credentials & security: PRD/tech-spec note config-driven LLM adapter, but there's no explicit note about secrets management or required environment variables (e.g., OPENAI_API_KEY). Recommend adding `docs/ops/README-llm.md` and `.env.example`.
  3. Testing matrix: tech-spec suggests tests but no `tests/` scaffolding exists. Recommend adding a `tests/` folder with one smoke test (create NPC -> get NPC -> receive websocket event).
  4. API contract: Need an OpenAPI or JSON Schema artifact to hand to frontend devs. Recommend adding `docs/api/openapi.yaml` (minimal) or generating from TypeScript types.
  5. Observability/metrics: No mention of logging/metrics endpoints. Recommend adding basic metrics (request latency, LLM latency, event write time) to tech-spec.

## Quick Wins (low risk)
- Add `.env.example` with LLM_ADAPTER=mock, SIM_INTERVAL=90, SNAPSHOT_PATH=./snapshots
- Add `docs/ops/README-llm.md` describing adapter selection and secrets handling
- Add a minimal `tests/smoke/` with a single integration test harness (uses mock adapter)

## Next Steps
1. Implement Quick Wins above.  
2. Re-run cohesion check.  
3. After addressing gaps, mark cohesion-check todo completed.
