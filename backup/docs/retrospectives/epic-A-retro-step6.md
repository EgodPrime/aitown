title: "Retrospective — Epic A (Step 6): Synthesize Action Items & Preparation Plan"
date: 2025-10-08
epic: A
next_epic: B
facilitator: "Bob (Scrum Master)"

---

# 回顾输出 — 第 6 步：合成行动项与准备冲刺计划

此文件将之前步骤（Step1-5）中识别的高优先级行动项，转为可直接放入准备冲刺（Preparation Sprint）的任务卡。每一项封装为：目标、输入、输出、验收准则、Owner、估时、依赖与风险。请核准后我将生成对应的任务板条目（例如 GitHub Issues / project board）若你需要。

## 快速概览
- 建议准备冲刺长度：4 工作日（可扩展至 7 天，视并行度）
- 主要目标：完成事件 schema、memoryRepo 快照接口、broadcaster 的 state_update 支持，并在 CI 中运行 10-NPC 性能 smoke test
- 关键验收门：所有 High Priority 任务完成且 smoke test 通过 → 准备就绪启动 Epic B

---

## Action Items (Preparation Sprint Tasks)

1) TASK: 定义 IEvent 与 `state_update` schema
- Owner: Winston (Architect)
- Collaborators: Amelia (Dev), Mary (Analyst), Murat (QA)
- Est: 1-2 days
- Inputs: `docs/tech-spec-epic-B.md`, current event samples in `memoryRepo.events`, expected `state_update` fields from Epic B
- Outputs: `docs/schema/event.md` (IEvent JSON Schema), `docs/schema/state_update.md` (JSON Schema + examples), example payloads for common actions
- Acceptance Criteria:
  - JSON Schema 文件存在并列出所有必需字段（timestamp, npc_id, action, delta_changes, new_state_snapshot, version, source, related_event_id）
  - 提供至少 3 个示例 payload（move, work, trade）并通过 schema 验证脚本
  - 开发/QA 达成一致并签署 schema 文档（PR 注释或 merge approval）
- Dependencies: none (but coordinate with Dev/QA for examples)
- Risks: schema 设计不当会导致后续多次变更；缓解：先定义 v1 且确保向后兼容字段策略

2) TASK: 实现 `memoryRepo` snapshot/write API
- Owner: Amelia (Dev)
- Collaborators: Winston (Architect), Murat (QA)
- Est: 2-3 days
- Inputs: current `src/repos/memoryRepo.ts`, event schema, snapshot/version requirements
- Outputs: `memoryRepo.writeSnapshot(npc_id): { version, timestamp }` API + unit tests + integration test that asserts snapshot write after event
- Acceptance Criteria:
  - API 能在事件写入后被调用并返回 deterministic `version` 与 ISO timestamp
  - 集成测试证明：在模拟行为生成后，事件写入并在 <=5s 内写入快照且快照 version 与事件相关联
  - 并发写入受到保护（basic lock 或序列化策略），测试覆盖常见并发场景
- Dependencies: IEvent schema (Task 1)
- Risks: 实现细节可能影响性能；缓解：先实现简单、健壮的策略（例如 per-npc mutex）并在后续优化

3) TASK: 扩展 `ws/broadcaster` 支持 `state_update` 格式与房间订阅
- Owner: Amelia (Dev)
- Collaborators: game-dev, Murat (QA)
- Est: 1-2 days
- Inputs: `docs/schema/state_update.md` (Task 1), existing broadcaster implementation (`src/ws/broadcaster.ts`)
- Outputs: broadcaster 支持新消息类型 `state_update`、按 room/topic 过滤、示例广播脚本、集成测试
- Acceptance Criteria:
  - broadcaster 能发送 `state_update` messages 验证通过 JSON Schema
  - 支持按 room/topic 订阅，且示例集成测试验证仅订阅者收到消息
  - 基本压力测试：在本地模拟 10 NPC 的短周期广播无致命异常（详见 Task 4）
- Dependencies: Task 1, Task 2
- Risks: 广播实现可能成为性能瓶颈；缓解：实现基础过滤并在 Task 4 中验证

4) TASK: 在 CI 中增加 10-NPC 性能 smoke test（自动化）
- Owner: Murat (Test Architect)
- Collaborators: Amelia (Dev), game-dev
- Est: 1-2 days
- Inputs: mock LLM adapter, broadcaster, memoryRepo snapshot API, small harness script to create 10 NPCs and run N cycles (e.g., 3 cycles)
- Outputs: CI job (e.g., vitest/mocha script) that runs smoke test and reports latency metrics; documented baseline阈值
- Acceptance Criteria:
  - Test 能在 CI 环境可重复运行并输出统计数据（平均决策时延、snapshot 写入延迟、broadcast 延迟）
  - 基线目标：平均单个决策生成+snapshot+广播耗时 < 10s（在本地 dev machine 基准）
  - 若超过阈值，CI 应标记为 warning/failure并产出瓶颈日志
- Dependencies: Tasks 1-3
- Risks: CI 资源差异导致基线波动；缓解：在本地与 CI 双向验证并记录环境规格

5) TASK: 定义 action contract（动作类型与 delta 字段）
- Owner: game-architect + game-dev
- Collaborators: Winston, Amelia
- Est: 1-2 days
- Inputs: typical LLM outputs、game design notes、state_update schema
- Outputs: `docs/schema/action_contract.md`（action types 列表及字段说明）、示例 mapping
- Acceptance Criteria:
  - 列出核心 action types（move, work, eat, social_interact, trade 等）并给出 delta 字段示例
  - 提供至少 3 个 LLM->action mapping 示例并通过简单验证脚本
- Dependencies: Task 1
- Risks: contract 过度复杂导致实现困难；缓解：优先定义最小可行 action 集合

6) TASK: 准备 mock LLM adapter 与 local-fallback hook
- Owner: Dev
- Collaborators: game-dev, Murat
- Est: 1 day
- Inputs: adapter interface template, sample LLM responses
- Outputs: mock adapter 实现 + local-fallback 模式 + 测试脚本
- Acceptance Criteria:
  - mock adapter 能在超时/失败场景下返回 deterministic fallback actions
  - 在 smoke test 中可切换到 mock adapter 以稳定基线
- Dependencies: Task 3, Task 4

7) TASK: 定义 metrics/KPIs 与采集点
- Owner: John (PM)
- Collaborators: Mary (Analyst), Murat (QA)
- Est: 1 day
- Inputs: delivery metrics需求、state_update schema
- Outputs: metrics list（e.g., state_update_latency_ms, snapshot_write_latency_ms, decisions_per_minute, fallback_rate）和采集计划（where/how）
- Acceptance Criteria:
  - 提供明确的指标定义与阈值，且已在 CI smoke test 输出中包含至少 2 项关键指标
- Dependencies: Task 1, Task 4

8) TASK: 硬化 player_id 中间件（可切换为 JWT/session）
- Owner: Sarah + Amelia
- Collaborators: Dev
- Est: 1 day
- Inputs: current auth middleware (x-player-id mock), basic JWT plan or session approach
- Outputs: middleware 抽象层，文档说明如何替换为 production auth（示例配置）
- Acceptance Criteria:
  - 中间件以抽象方式实现，测试通过并在集成测试中可被替换为简单 JWT 验证器
- Dependencies: none

9) TASK: 增强 prompt template metadata（id, locale, description）
- Owner: Sally (UX)
- Collaborators: Dev
- Est: 0.5-1 day
- Inputs: `docs/prompt-templates.json` 当前内容
- Outputs: 更新后的 `docs/prompt-templates.json`（含 id/locale/short_description 字段），并示例前端呈现建议
- Acceptance Criteria:
  - 新字段存在且前端示例可以正确显示
- Dependencies: none

10) TASK: 文档化事件回放与审计流程
- Owner: Mary + Winston
- Collaborators: QA
- Est: 1 day
- Inputs: event schema, snapshot API
- Outputs: `docs/processes/event-replay.md`（包含回放步骤、示例命令与审计查询示例）
- Acceptance Criteria:
  - 文档能指导技术人员完成一次从事件日志到状态回放的完整流程

---

## Suggested Preparation Sprint Plan (4-day example)

Day 1:
- Morning: Task 1 (schema) kickoff + Task 5 (action contract) start
- Afternoon: Task 2 (snapshot API) design + Task 8 (auth middleware) start

Day 2:
- Morning: Task 2 implementation + Task 3 (broadcaster) design
- Afternoon: Task 3 implementation + Task 6 (mock adapter)

Day 3:
- Morning: Task 4 (CI smoke test) scripting + Task 9 (prompt metadata)
- Afternoon: Run preliminary smoke test locally; iterate on Task 2/3 if needed

Day 4:
- Morning: Run CI smoke test; collect metrics
- Afternoon: Task 10 (event replay docs) + finalize metrics (Task 7)

If smoke test passes and owners confirm, Epic B can be started.

---

## Approval & Next Steps
1. 请确认本准备冲刺计划与任务卡是否可以作为正式准备冲刺（回复“批准”或“approve”）
2. 若需修改请回复“编辑”并指出具体任务编号与更改内容
3. 如果批准，我已经完成了以下初步工件（供你审阅）：
  a) Issue 草稿已生成在 `docs/retrospectives/issues/` （文件名以 `00X-*.md` 排列）
  b) CI workflow 草案已添加： `.github/workflows/prep-smoke-test.yml`
  c) Smoke test 脚本（最小 harness）已添加： `scripts/ci/smoke-10npc.js`

如需我把这些 Issue 转为真实的 GitHub Issues 或者把 CI workflow 调整细化，请回复授权（例如 “create issues” 或 “enable CI”）。

已保存为： `docs/retrospectives/epic-A-retro-step6.md`
