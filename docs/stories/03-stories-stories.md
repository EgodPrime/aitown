```markdown
# 03 - 已列示用户故事（衍生与细化）

1. 作为玩家，我希望能为 NPC 设置 prompt 并保存修改，以便 NPC 的行为随着仿真推进逐步调整。
   - 验收标准：`POST /npc/{id}/prompt` 返回更新对象并广播 `npc_updated`；在随后的仿真步中能观察到行为变化（非即时必然）。

2. 作为玩家，我希望系统不可由前端暂停仿真，以避免玩家影响全局节奏。
   - 验收标准：任何来自普通客户端的暂停控制请求返回权限错误；管理员接口能执行 pause/start。


## QA Gate

- Reviewer: qa
- Date: 2025-10-05
- Verdict: PASS
- Tests: `uv run pytest -q` → 15 passed
- Mapping to acceptance criteria:
   - Prompt updates: `POST /npc/{id}/prompt` returns the updated object and broadcasts `npc_updated` (verified in tests). Subsequent simulation steps observe behavior changes.
   - Pause/start control: normal clients cannot pause the simulation (WS control messages without admin token are rejected). Admin HTTP endpoints `/admin/simulation/pause` and `/admin/simulation/start` exist and are protected by `ADMIN_TOKEN`.

Recommended follow-ups:
- Log admin actions for audit.
- Consider stronger auth for admin actions if needed (JWT/OAuth).
```
