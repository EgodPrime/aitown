```markdown
# 01 - 概述：用户故事草案

1. 作为一名玩家，我希望在浏览器中创建并配置一个 NPC（每位玩家仅限 1 个），以便我可以观察它在小镇中的行为。
   - 验收标准：能通过 `POST /npc` 创建 NPC（包含 player_id）；响应包含 NPC 对象；所有客户端收到 `npc_created` 广播。

2. 作为一名演示者，我希望系统在单机环境下能稳定运行并展示 LLM 驱动的行为多样性，以便用于教学或演示。
   - 验收标准：在本地部署下运行 10-50 个 NPC，服务不崩溃并能定期广播 `state_update` 消息；可观察到由 prompt 引起的行为差异（手动验收）。


## QA Review

- Reviewer: qa
- Date: 2025-10-05
- Verdict: PASS
- Tests: `uv run pytest -q` → 16 passed
- Notes:
   - `POST /npc` creates NPCs and broadcasts `npc_created` (verified by tests and WS integration).
   - Simulation loop produces `state_update` messages; added a smoke test that creates 20 NPCs and runs multiple steps to validate stability.

Recommended follow-ups:
- Add runtime metrics and a longer-running stress test if you plan to demo with heavy LLM workloads.
```
