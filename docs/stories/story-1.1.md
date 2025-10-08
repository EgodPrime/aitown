title: "Story 1.1: 创建 NPC"
status: Done
author: Egod
epic: A
story_id: A-01
story_points: 5
priority: High

---

# Story 1.1: 创建 NPC

Status: Done

## Story

As a player,
I want to create an NPC via POST /npc,
so that the system persists the NPC and notifies subscribers that a new NPC exists.

## Acceptance Criteria

1. POST /npc 返回 201 并返回满足 NPC schema 的 JSON 对象（包含 id、player_id、name、prompt、initial_stats）。
2. 当玩家已经存在活跃 NPC 时返回 409 并带有解释错误消息。
3. 成功创建时发送 WebSocket 事件 `npc_created`，订阅客户端能收到并显示新 NPC。
4. 在内存存储中能查询到该 NPC，并可通过 GET /npc/{id} 读取到相同数据。

## Tasks / Subtasks

- [x] Implement POST /npc endpoint (validate input, persist to in-memory store)
  - [x] Define NPC schema and validation
  - [x] Persist entity with generated id and player_id association
  - [x] Emit `npc_created` WebSocket event on success
- [x] Handle conflict when player already has active NPC (return 409)
- [x] Implement GET /npc/{id} and GET /npc (list) endpoints for verification
- [x] Add unit tests for happy path and conflict path

## Review Follow-ups (AI)

- [x] [AI-Review][Low] Add logging for NPC creation in npcService.create (e.g., console.log or proper logger).

## Dev Notes

- Source: `docs/epic-stories.md` (Epic A, A-01)
- Align with unified project structure and testing strategy in docs

### Project Structure Notes

- Follow existing API contract and types in `src/types` (if present)
- Ensure WebSocket broadcasting subsystem is compatible with existing server

### References

- docs/epic-stories.md#A-01

## Dev Agent Record

### Context Reference

<!-- Story context XML/JSON will be added here by story-context workflow if run -->

 - `docs/story-context-A-01.xml`

### Agent Model Used

BMAD create-story workflow v6

### Debug Log References

Plan: Update INPC interface to use player_id. Modify npcService.create to use player_id, check for existing active NPC. Update routes to validate name and prompt, return response with initial_stats. Update broadcaster call. Add tests for service and routes including validation and conflict. Create app.ts for testing.

### Completion Notes List

Implemented POST /npc with validation, persistence, WebSocket event emission, and conflict handling. Updated interfaces and services for player_id. Added comprehensive unit and route tests. All ACs satisfied.

### File List

- src/types/index.ts
- src/services/npcService.ts
- src/routes/npc.ts
- src/app.ts
- tests/unit/npcService.test.ts
- tests/routes/npc.routes.test.ts

## Change Log

- 2025-10-08: Implemented NPC creation endpoint with validation, persistence, WebSocket events, and tests. All tasks completed.
- 2025-10-08: Senior Developer Review notes appended.
- 2025-10-08: Added logging for NPC creation in npcService.create.
- 2025-10-08: Marked as Done by Scrum Master.

## Senior Developer Review (AI)

### Reviewer
Egod

### Date
2025-10-08

### Outcome
Approve

### Summary
The implementation of Story 1.1: 创建 NPC is complete and meets all acceptance criteria. The code is well-structured, tested, and follows project conventions. No critical issues found.

### Key Findings
- **High Severity**: None
- **Medium Severity**: None
- **Low Severity**: Consider adding logging for NPC creation events in production.

### Acceptance Criteria Coverage
- AC-1: Fully implemented and tested (POST /npc returns 201 with correct JSON schema).
- AC-2: Fully implemented and tested (409 on player conflict).
- AC-3: Fully implemented and tested (WebSocket npc_created event broadcast).
- AC-4: Fully implemented and tested (NPC persisted and retrievable via GET).

### Test Coverage and Gaps
- Unit tests: npcService and routes fully covered, including happy path and conflict.
- Integration tests: WebSocket broadcasting verified.
- Gaps: None identified; all critical paths tested.

### Architectural Alignment
- Aligns with tech-spec-epic-A.md: Uses npcService, memoryRepo, routes/npc, ws/broadcaster.
- Follows solution-architecture.md: Event-driven state updates via broadcaster.

### Security Notes
- Input validation added for name and prompt.
- No authentication implemented (as per scope).
- Dependencies checked; no vulnerabilities in package.json.

### Best-Practices and References
- Node.js/Express best practices followed (OWASP for input validation).
- TypeScript interfaces used correctly.
- WebSocket broadcasting follows standard patterns.

### Action Items
- [Low] Add logging for NPC creation in npcService.create (e.g., console.log or proper logger).
