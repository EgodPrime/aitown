title: "RETROSPECTIVE - Epic A: NPC Management & Display"
date: 2025-10-08
epic: A
epic_title: "NPC Management & Display"
facilitator: "Bob (Scrum Master)"

---

🔄 TEAM RETROSPECTIVE - Epic A: NPC Management & Display

Scrum Master facilitating: Bob

════════════════════════════════════════════════════════════════════════

EPIC A SUMMARY:

Delivery Metrics:
- Completed: 5/5 stories (100%)
- Velocity: 19 story points delivered (planned: 19)
- Duration: planning artifacts indicate a 3-sprint candidate plan; actual sprint tracking not present in docs (recommend capture in next steps)
- Average velocity per sprint (estimated): N/A (no sprint execution records in repo)

Quality and Technical:
- Blockers encountered: 未在 story 文档中记录重大阻塞（建议在回顾中确认是否存在隐性阻塞）
- Technical debt items: 若干 stories 提及后续 refactor/backlog（详见 stories change logs）
- Test coverage: 各 story 文档均声明已添加 unit/integration tests 且“所有测试通过”；建议在 CI 中运行全套测试以验证
- Production incidents: 无生产部署记录（MVP 面向局域网/本地演示），无已记录生产事件

Business Outcomes:
- 主要功能交付：创建、查看（列表/单体）、更新 prompt、删除 NPC、示例 prompt 库端点均实现
- Stakeholder acceptance: 未在 repo 中找到显式的 PO 验收记录（建议在回顾中由 PO / PM 确认）

════════════════════════════════════════════════════════════════════════

NEXT EPIC PREVIEW: Epic B — Simulation Engine & Behavior

Dependencies on Epic A:
See `docs/retrospectives/epic-A-retro-step2.md` for full dependency mapping. Short summary:
- NPC data model and CRUD: 已实现并可被仿真引擎消费
- Event model & memoryRepo: 基础内存事件存在，但需规范化事件 schema 与实现 snapshot/version 支持
- WebSocket broadcaster: 已支持 `npc_created`/`npc_deleted`，需扩展到高频 `state_update` 格式并考虑分区/房间

════════════════════════════════════════════════════════════════════════

TEAM assembled for reflection:
- Bob (Scrum Master)
- Sarah (Product Owner)
- John (Product Manager)
- Amelia (Dev)
- Winston (Architect)
- Mary (Analyst)
- Murat (Test Architect)
- Sally (UX Expert)
- game-dev / game-architect / game-designer as needed

Focus Areas for the Retrospective:
1. Learning from Epic A execution (what went well, what could improve)
2. Preparing for Epic B (dependencies, gaps, performance readiness)

Suggested Action Items (synthesized):
1. 定义并发布事件模型与 `state_update` schema（Owner: Winston; Est: 1-2 days）
2. 为 `memoryRepo` 增加快照/versioning 支持并验证 5s 写入窗口（Owner: Amelia; Est: 2-3 days）
3. 扩展 broadcaster 以支持 `state_update`（Owner: Amelia; Est: 1-2 days）
4. 执行 10-NPC 性能 smoke test（Owner: Murat; Est: 1-2 days）
5. 硬化 player_id 中间件为 JWT/session 可替换方案（Owner: Sarah+Amelia; Est: 1 day）

Critical Path:
- 未解决的快照/版本与高频广播问题将阻碍 Epic B 的顺利展开。优先完成事件 schema、快照接口与基础性能 smoke test。

════════════════════════════════════════════════════════════════════════

Next steps (interactive):
1) Confirm and run the retrospective facilitation (Part 1: Epic Review) — 回复 “继续” 或 “1”
2) Modify this summary before facilitation — 回复 “编辑” 并说明变更点
3) Abort/Save and stop here — 回复 “停” 或 “2”

Action artifacts will be saved to: `docs/retrospectives/epic-A-retro-2025-10-08.md`

---
