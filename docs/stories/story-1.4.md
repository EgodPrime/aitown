title: "Story 1.4: 更新单个 NPC 的 prompt"
status: Done
author: Egod
epic: A
story_id: A-04
story_points: 3
priority: Medium

---

# Story 1.4: 更新单个 NPC 的 prompt

Status: Done

## Story

As a player,
I want to update my NPC's prompt via PATCH /npc/{id}/prompt,
so that I can modify the NPC's behavior without affecting other players' views immediately.

## Acceptance Criteria

1. 仅资源所有者可成功调用，成功返回 200 与更新后的对象；非所有者返回 403。
2. 更新后，调用者的会话或随后 GET /npc/{id} 能立即看到最新 prompt，但系统不会广播该 prompt 给其他玩家。
3. 更新操作在事件日志中记录一条 `prompt_updated` 记录（包含 actor、timestamp、diff 可选）。

## Tasks / Subtasks

- [x] Implement PATCH /npc/{id}/prompt endpoint with ownership check
  - [x] Add ownership validation in `npcService`
  - [x] Return 403 for non-owners
  - [x] Return 200 with updated NPC for owners
- [x] Record `prompt_updated` event in event log
  - [x] `memoryRepo.appendEvent` appends event entries (actor, timestamp, diff)
- [x] Update `npcService` to handle prompt update
- [x] Add unit tests for service and routes
- [x] Add integration tests for PATCH /npc/{id}/prompt

## Dev Notes

- Relevant architecture patterns and constraints: Follow event-driven state updates, use memoryRepo for data access and event logging.
- Source tree components to touch: src/routes/npc.ts, src/services/npcService.ts, src/repos/memoryRepo.ts
- Testing standards summary: Unit tests for service, integration for routes.

### Implementation Notes

- Ownership verification: `player_id` is derived from `req.player_id` set by auth/session middleware; tests use an `x-player-id` header for convenience. The route enforces presence of `req.player_id` for the PATCH endpoint and returns 401 if missing. For production, replace the simple header approach with real auth (JWT/session).
- Prompt length validation: both route handlers and the service enforce a configurable `PROMPT_MAX_LENGTH` (default 5000). Oversized prompts return 400 (`prompt_too_long`) at the route layer and service throws `PROMPT_TOO_LONG` defensively.
- Events: `prompt_updated` events are appended to `memoryRepo.events` with `actor`, `npc_id`, `timestamp`, and `diff` (from/to) for auditing.
- Tests: Unit tests cover service behavior (ownership, event logging, prompt validation). Integration tests assert end-to-end behavior including that prompt updates are visible to the owner and that no broadcast is emitted for prompt updates.

### Project Structure Notes

- Align with existing API contract and types in src/types (INPC interface)
- Ensure ownership check using playerId

### References

- docs/epic-stories.md#A-04
- docs/tech-spec-epic-A.md
- docs/solution-architecture.md
- docs/tech-spec.md

## Dev Agent Record

### Context Reference

- docs/story-context-A-04.xml

### Agent Model Used

BMAD create-story workflow v6

### Debug Log References

### Completion Notes List

### File List

### Change Log

- 2025-10-08: Initial draft created by create-story workflow
- 2025-10-08: Senior Developer Review (AI) appended by reviewer Egod
- 2025-10-08: Implemented ownership-from-middleware for PATCH and prompt length config; added unit and integration tests. (Egod)
- 2025-10-08: Status set to Done after implementation and verification (Egod)


## Senior Developer Review (AI) — Post-implementation Update

- Reviewer: Egod
- Date: 2025-10-08
- Outcome: Approved (Implementation Verified)

### Validation Summary

- Story file and context reviewed.
- Tech spec for Epic A updated to reflect middleware-based ownership and prompt configuration.
- Backlog items related to this story updated; high-priority items implemented and closed.
- Automated test suite executed: all tests passed (22/22) including new integration and validation tests.

### Findings and Confirmation

- Ownership: Implemented. `player_id` is now derived from middleware (`req.player_id`). PATCH enforces middleware presence and `npcService` validates ownership. Non-owners receive 403; missing middleware yields 401.
- Prompt Visibility & Non-Broadcast: Implemented and tested. PATCH returns updated NPC; subsequent GET returns updated prompt for the owner. No broadcast is emitted for prompt updates (verified in integration test).
- Event Logging: Implemented. `prompt_updated` events are appended to `memoryRepo.events` with actor, npc_id, timestamp, and diff.
- Input Validation: Implemented. `PROMPT_MAX_LENGTH` (default 5000) introduced in `src/config.ts`; enforced at route and service layers. Tests added to cover oversized prompts.

### Action Items (Status)

- [x] Ownership-from-middleware implemented (Closed)
- [x] Integration test for visibility/no-broadcast added (Closed)
- [x] Prompt length validation and config added (Closed)

### Notes

- The current auth middleware is minimal and intended for tests/demo (`x-player-id` header). For production, replace with a proper auth/session system that populates `req.player_id` from a verified token/session.

### Change Log

- 2025-10-08: Implementation verified; Senior Developer Review (AI) updated with post-implementation validation. (Egod)

