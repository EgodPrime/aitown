# Epic Stories for aitown

**Author:** Egod
**Date:** 2025-10-09

This file expands the four primary Epics into actionable stories with brief acceptance criteria and test notes.

## Epic A: 数据模型与仓储（Data Models & Repos）

- A.1 Schema design and review
  - Acceptance: Schema document with table definitions and example rows reviewed by devs
  - Test notes: Run migration script on SQLite memory and verify tables exist

- A.2 Migration and seed scripts
  - Acceptance: `backend/scripts/init_db.py` creates schema and inserts seed data
  - Test notes: Integration test runs script and asserts counts

- A.3 Repository interfaces and implementations
  - Acceptance: Repo interfaces (PlayerRepo, NPCRepo, EventRepo, MemoryRepo) with SQLite implementation
  - Test notes: Unit tests mock DB for repo interface; integration tests use SQLite file

- A.4 Repository unit tests
  - Acceptance: >=80% coverage for repository methods; common CRUD tested
  - Test notes: Use pytest and tempfile DB

- A.5 DB access docs
  - Acceptance: docs/db.md created with fields and JSON conventions
  - Test notes: Manual review

## Epic B: 核心业务逻辑与服务（Domain Logic & Services）

- B.1 SimClock
  - Acceptance: SimClock supports start/stop/step/scale and emits tick events
  - Test notes: Unit tests for tick sequencing and speed adjustments

- B.2 Event Bus and persistence
  - Acceptance: Events are published to in-memory bus and persisted to `event` table
  - Test notes: Integration test that triggers actions and asserts event rows

- B.3 Action Executors
  - Acceptance: move/eat/sleep/work/buy/sell/idle implemented and update entities
  - Test notes: Unit tests for each action; integration test for a simple scenario

- B.4 Memory Manager
  - Acceptance: Recent memory kept for 7 days; summaries generated and stored in long memory table
  - Test notes: Mock LLM adapter to verify summarize calls and storage

- B.5 Service layer
  - Acceptance: npc_service, player_service, simulation_service with documented APIs
  - Test notes: Service unit tests and light integration tests

## Epic C: 前端与 API（Frontend & API）

- C.1 API design
  - Acceptance: OpenAPI spec generated; endpoints for player, npc, place, event
  - Test notes: Use FastAPI test client for integration tests

- C.2 WebSocket events
  - Acceptance: `/ws/events` streams simulation events; supports subscribe/unsubscribe
  - Test notes: WS integration tests using test client

- C.3 Frontend SPA
  - Acceptance: Minimal UI for register/create NPC/observe; connects to WS
  - Test notes: Manual smoke test plus e2e test using Playwright or Cypress (optional)

- C.4 API and WS integration tests
  - Acceptance: Automated tests covering major flows
  - Test notes: Run in CI against test DB

## Epic D: 系统联调与质量保证（Integration & QA）

- D.1 E2E tests
  - Acceptance: Core user journey covered by at least one automated E2E
  - Test notes: Use Playwright or pytest + requests + websockets

- D.2 CI configuration
  - Acceptance: `.github/workflows/ci.yml` or similar runs tests on PRs
  - Test notes: Ensure secrets and env-vars are stubbed for CI

- D.3 Performance & concurrency
  - Acceptance: Basic benchmark scripts and reports
  - Test notes: Run simple concurrent writers and measure failure modes

- D.4 Runbook / deployment docs
  - Acceptance: `docs/runbook.md` with steps to run locally on LAN and reproduce tests
  - Test notes: Manual verification

---