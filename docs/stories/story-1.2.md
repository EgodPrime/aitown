title: "Story 1.2: 查看 NPC 列表"
status: Completed
author: Egod
epic: A
story_id: A-02
story_points: 3
priority: High

---

# Story 1.2: 查看 NPC 列表

Status: Completed

## Story

As a player,
I want to view NPC list via GET /npc,
so that I can see the list with pagination and status snapshots.

## Acceptance Criteria

1. GET /npc 返回 200 与列表结果，包含 pagination 元数据（limit/offset/total 或 cursor）。
2. 列表项包含简要状态字段（hunger, energy, mood, location）以供快速渲染。
3. 当无数据时返回空数组并正确展示 pagination 元信息。

## Tasks / Subtasks

- [x] Implement GET /npc endpoint with pagination support
  - [x] Add query parameters for limit/offset or cursor
  - [x] Return list of NPCs with status fields
- [x] Handle empty list case
- [x] Add unit tests for service and routes

## Review Follow-ups (AI)

- [x] [AI-Review][Low] Add input validation for limit (max 100) and offset (non-negative) in GET /npc route.

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Project Structure Notes

- Follow existing API contract and types in src/types
- Ensure pagination follows REST API spec

### References

- docs/epic-stories.md#A-02

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML/JSON will be added here by context workflow if run -->

 - `docs/story-context-A-02.xml`

### Agent Model Used

BMAD create-story workflow v6

### Debug Log References

### Completion Notes List
- Implemented GET /npc endpoint with pagination (limit/offset), returning active NPCs with status fields (hunger, energy, mood, location).
- Added unit tests for npcService.list with pagination and empty cases.
- Added integration tests for GET /npc route with pagination and empty response.
- All tests pass, no regressions.

### File List
- src/repos/memoryRepo.ts
- src/services/npcService.ts
- src/routes/npc.ts
- tests/unit/npcService.test.ts
- tests/routes/npc.routes.test.ts

### Change Log
- 2025-10-08: Implemented GET /npc endpoint with pagination and status fields for NPC list view.
- 2025-10-08: Senior Developer Review notes appended.
- 2025-10-08: Status updated to Completed after implementing Action Items and passing tests.

## Senior Developer Review (AI)

### Reviewer
Egod

### Date
2025-10-08

### Outcome
Approve

### Summary
The implementation successfully delivers the GET /npc endpoint with pagination support, returning active NPCs with required status fields. All acceptance criteria are met, and comprehensive tests have been added. Code quality is good, with proper separation of concerns and no major issues identified.

### Key Findings
- **High Severity**: None
- **Medium Severity**: None
- **Low Severity**: Consider adding input validation for limit and offset query parameters to prevent potential abuse (e.g., very large limits).

### Acceptance Criteria Coverage
1. ✅ GET /npc 返回 200 与列表结果，包含 pagination 元数据（limit/offset/total 或 cursor）。 - Implemented with limit/offset/total.
2. ✅ 列表项包含简要状态字段（hunger, energy, mood, location）以供快速渲染。 - INPC includes all fields.
3. ✅ 当无数据时返回空数组并正确展示 pagination 元信息。 - Handled in service and tests.

### Test Coverage and Gaps
- Unit tests added for npcService.list with pagination and empty cases.
- Integration tests added for GET /npc route with pagination parameters and empty response.
- All tests pass. No gaps identified.

### Architectural Alignment
- Follows existing patterns: service layer calls repo, routes handle HTTP.
- Pagination implemented in repo.findAll, consistent with REST API spec.
- Filters active NPCs as per constraints.

### Security Notes
- No authentication/authorization implemented, consistent with current API design.
- No input validation on query params; consider adding to prevent DoS via large limits.
- Dependencies in package.json appear standard; no known vulnerabilities.

### Best-Practices and References
- Node.js/Express best practices: Proper error handling, separation of concerns.
- REST API pagination: Using limit/offset is standard; cursor-based could be considered for large datasets.
- Testing: Vitest usage is appropriate; tests are isolated with beforeEach clearing store.

### Action Items
- [Low] Add input validation for limit (max 100) and offset (non-negative) in GET /npc route.