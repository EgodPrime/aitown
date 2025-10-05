```markdown
# 04 - MVP 功能：用户故事与验收

1. NPC 管理（CRUD）
   - 作为玩家，我能创建并查看 NPC 的基本属性（name, prompt, position, hunger, energy, mood, money, inventory）。
   - 验收标准：`GET /npc` 列表包含所有 NPC；单个 NPC 的 `GET /npc/{id}` 返回完整属性；属性字段与文档一致。

2. 生存与死亡规则
   - 作为系统，我要在属性降至 0 时将 NPC 标记为死亡并广播事件，以便前端与仿真逻辑一致。
   - 验收标准：当 `hunger` 或 `energy` 为 0 时，后端设置 `status: dead` 并广播 `npc_died`。

3. 经济与物品
   - 作为玩家，我希望 NPC 能购买物品并消费来恢复属性。
   - 验收标准：`POST /npc/{id}/buy` 扣减 money 并将商品加入 inventory；`POST /npc/{id}/use-item` 更新属性并移除/标记物品。


## QA Review

- QA Status: PASS (with concerns addressed)

- Summary of verification:
   - Ran automated test suite: `uv run pytest -q` → all tests passed (13 passed after updates).
   - Confirmed NPC CRUD, survival/death rules, economy/buy/use-item flows work and are covered by tests.

- Actions taken to address QA concerns:
   1. Persistence: added structured logging for persistence failures and an environment toggle `RAISE_ON_PERSISTENCE_ERROR=1` to make persistence errors raise in CI or higher environments. Also improved SQLite resilience (WAL mode, busy_timeout, check_same_thread=False).
 2. Validation: introduced a canonical `ITEM_CATALOG` and added validation for `item_id` and `place_id` with clear 400 responses. Added tests for invalid item/place ids.
 3. WebSocket & concurrency: made SQLite usage more resilient for local concurrent access; recommended networked DB for production.

- Recommended follow-ups (not blocking merge):
   - Add a migration and production DB adapter (Postgres with SQLAlchemy/Alembic).
   - Add more integration tests around WebSocket reconnects and multi-client scenarios.
   - Consider admin operations for dead NPC lifecycle (resurrect or TTL removal).

Notes: full details of the QA run and the file-level changes are recorded in `docs/stories/04-mvp-features-stories-qa.md`.

---

### QA Summary

- Reviewer: qa
- Date: 2025-10-05
- Verdict: PASS (with concerns addressed)
- Tests: `uv run pytest -q` → 13 passed
- Key checks: NPC CRUD, survival/death, buy/use-item flows, persistence & validation improvements
```
