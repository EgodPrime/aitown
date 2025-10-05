```markdown
# 06 - 记忆与日志：用户故事

1. 记忆保留策略
   - 作为系统，我要保存最近 7 天的逐日记忆条目，并将更早记录压缩为长期摘要，以模拟长期记忆。
   - 验收标准：`GET /npc/{id}/memory` 在运行多日后返回最近 7 天的详细条目和少量摘要条目；手动触发摘要逻辑能生成长期摘要条目。

2. 玩家查看记忆
   - 作为玩家，我要查看自己的 NPC 的 memory_log 以调试或叙事。
   - 验收标准：前端调用 `GET /npc/{id}/memory` 并以时间序列展示条目。

## Implementation Note (dev)

- Implemented server-side manual summarization: POST `/admin/summarize-memory` with body `{ "npc_id": "<id>" }` (requires `ADMIN_TOKEN` header) compresses memory entries older than 7 days into a deterministic summary entry and persists it. The summarizer is deterministic and suitable for unit tests; a later iteration can call an LLM adapter for higher-quality summaries.

- The GET `/npc/{id}/memory` endpoint now returns `memory_log` (recent entries + any summary entries) and `long_term_summary` (the latest summary entry) for quick access.

## QA Results

- Reviewer: qa
- Date: 2025-10-06
- Story: 06 - 记忆与日志：用户故事 (story-06)
- Gate Decision: PASSED

Evidence:
- Automated tests: `pytest` ran successfully: 22 passed (includes new summarization unit and API tests).
- Manual verification: endpoint `POST /admin/summarize-memory` works with `ADMIN_TOKEN` and updates `GET /npc/{id}/memory` with a `long_term_summary` entry.

Notes & Recommendations:
- The summarizer is deterministic and suitable for MVP and testing. For higher-quality long-term summaries, plan an LLM adapter integration (see story-14).
- Consider adding a periodic background job for automatic summarization (nightly or per-simulation-rollover) and additional tests for malformed/missing timestamps.

Recommendation: Mark story-06 as Done in the tracker.
```
