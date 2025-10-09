# Story 2.1: 核心业务逻辑与服务（Domain Logic & Services）

Status: Approved

## Story

As a developer of the simulation platform,
I want a cohesive core services module that implements the simulation clock, event bus and persistence, action executors, memory manager, and service layer,
so that NPCs and players can be simulated reliably, events persisted, and services exposed for API/WS consumption.

## Acceptance Criteria

1. SimClock supports start/stop/step/scale and emits tick events that subscribers can consume (B.1)
2. Event Bus allows publishing and subscribing to events; events are persisted to an `event` table for replay and inspection (B.2)
3. Action Executors for move, eat, sleep, work, buy, sell, idle are implemented and update entity state correctly (B.3)
4. Memory Manager retains recent memory for 7 days, produces summaries for long-term storage, and stores summaries in a long memory table (B.4)
5. Service layer exposes `npc_service` and `player_service` with documented method signatures and behaviors; the simulation kernel (runtime) is the system core and exposes a clear runtime interface rather than being implemented as a service (B.5)

## Tasks / Subtasks

- [x] Implement `SimClock` with controls: start(), stop(), step(), and emit tick events (用户修改了部分实现细节)
  - [x] Unit tests for tick sequencing and speed adjustments
- [x] Implement in-memory Event Bus with persistence adapter to `event` table
  - [x] Integration test that publishes events and asserts rows in `event` table
- [ ] Implement Action Executors: move, eat, sleep, work, buy, sell, idle
  - [ ] Unit tests for each executor verifying state changes
  - [ ] Integration scenario test: simple NPC performs a sequence of actions producing expected outcomes
- [ ] Implement Memory Manager with retention policy and summarization hook
  - [ ] Mock LLM adapter in tests to verify summarize calls
  - [ ] Integration test to verify summaries written to long memory table
- [ ] Implement service layer APIs: `npc_service`, `player_service`
  - [ ] Document APIs and add lightweight integration tests using framework test client
- [ ] Define and implement the simulation kernel (runtime core) API and runtime components (SimClock lives in the kernel, not as a user-facing service)
  - [ ] Unit and integration tests for kernel runtime behaviors and lifecycle

## Dev Notes

- Relevant architecture patterns and constraints:
  - Keep core components modular and testable. Prefer dependency injection for persistence adapters.
  - The simulation kernel is the runtime core (not a high-level service): SimClock and runtime loop should live inside the kernel; services (npc/player) interact with the kernel via a documented runtime interface.
  - Ensure Event Bus and kernel tick loop are decoupled: kernel emits ticks; Event Bus handles domain events and persistence.
  - Memory Manager must support configurable retention (default 7 days) and pluggable summarizer for LLMs.
- Source tree components to touch:
  - `backend/src/` services and simulation modules
  - `backend/src/aitown/` repositories and services
  - Database migration and `event` table schema (`backend/migrations/0001_init.sql`)
- Testing standards summary:
  - Use pytest for unit and integration tests
  - Use temporary SQLite DB or memory DB for integration tests

### Project Structure Notes

-- Alignment with unified project structure (paths, modules, naming): services under `backend/src/aitown/services/`, simulation kernel/runtime under `backend/src/aitown/kernel/` or `backend/src/aitown/runtime/` (SimClock and core loop belong here).
- Detected conflicts or variances: None detected automatically; review required when implementing to map existing repos.

### References

- Source: `docs/epic-stories.md#epic-b` (Epic B section)
- Source: `backend/migrations/0001_init.sql` (event table schema)

## Dev Agent Record

### Context Reference

- `docs/story-context-2.1.xml` — generated story context (BMAD workflow)

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
