```markdown
# 02 - 范围：用户故事草案

1. 作为玩家，我可以创建、编辑和删除我的 NPC（受每玩家 1 个约束），以便管理我的观察对象。
   - 验收标准：`POST /npc` 成功创建；当同一 player_id 再次创建时返回 400/冲突；`PATCH/PUT /npc/{id}` 更新仅允许 NPC 所有者；`DELETE /npc/{id}` 仅允许所有者或管理员。

2. 作为产品负责人，我要明确 MVP 不包含用户登录或多机部署，以便优先交付本地可运行的体验。
   - 验收标准：文档中声明无登录需求；示例部署说明以本地会话或短期 token 为鉴别方式。
      - Implementation note: MVP uses simple header tokens (X-Player-Id / X-Admin-Token) for owner/admin actions and does not implement user login or multi-node persistence by default.

## QA Review

- Reviewer: qa
- Date: 2025-10-05
- Verdict: PASS
- Tests: `uv run pytest -q` → 18 passed
- Mapping to acceptance criteria:
   - Create/edit/delete with per-player 1 NPC constraint: `POST /npc` rejects duplicate player_id (409), `PATCH /npc/{id}` enforces owner-only updates, `DELETE /npc/{id}` allows owner or admin — verified by tests.
   - MVP scope (no login/multi-node): documented and implemented as header-token based owner/admin checks; no login flows or multi-node persistence included.

Recommended follow-ups:
- Add user auth if production/user accounts are required (JWT/OAuth).
- Add multi-node persistence adapter (Postgres/Redis) and integration tests for cross-process ownership enforcement.

```
