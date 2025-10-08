# Backlog

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
|------|-------|------|------|----------|-------|--------|-------|
| 2025-10-08 | A-01 | A | Enhancement | Low | Egod | Closed | Add logging for NPC creation in npcService.create (e.g., console.log or proper logger). Related to story-1.1.md |
| 2025-10-08 | A-02 | A | Enhancement | Low | Egod | Closed | Add input validation for limit (max 100) and offset (non-negative) in GET /npc route. Related to story-1.2.md |
| 2025-10-08 | A-04 | A | Bug/TechDebt | High | Egod | Closed | Derive player_id from auth/session middleware and enforce on PATCH /npc/{id}/prompt. Implemented in src/app.ts and src/routes/npc.ts on 2025-10-08. See: docs/stories/story-1.4.md |
| 2025-10-08 | A-04 | A | Test | Medium | Egod | Closed | Integration test added: tests/routes/patch_prompt.integration.test.ts on 2025-10-08. See: docs/stories/story-1.4.md |
| 2025-10-08 | A-04 | A | Enhancement | Low | TBD | Closed | Add input size validation and sanitization for `prompt` (limit length, e.g., 5000 chars). See: src/routes/npc.ts, src/services/npcService.ts |
| 2025-10-08 | A-05-1 | A | Enhancement | Medium | Egod | Closed | Replace simple admin check with role-based middleware or config-driven admin list. Related to story-1.5.md |
| 2025-10-08 | A-05-2 | A | Enhancement | Low | Egod | Closed | Load prompt templates into memory at startup for performance; consider cache invalidation. Related to story-1.5.md |
| 2025-10-08 | A-05-3 | A | Enhancement | Low | Egod | Closed | Add localization and structured metadata for prompt templates. Related to story-1.5.md |