title: "Retrospective — Epic A (Step 5): Next Epic Preparation Discussion"
date: 2025-10-08
epic: A
next_epic: B
facilitator: "Bob (Scrum Master)"

---

# 回顾输出 — 第 5 步：为下一个史诗做准备（逐角色前瞻分析）

此文档基于 Step 2 的依赖评估与 Step 4 的 Agent 反馈，面向 Epic B（Simulation Engine & Behavior），提供逐角色的准备建议、风险评估与可直接放入准备冲刺的任务清单。

每个角色包含：Dependencies Check / Preparation Needs / Risk Assessment（供会议中分配与确认）。

1) Bob — Scrum Master
- Dependencies Check:
  - 需要确认各 action item 的 owner 已接受并将其纳入下次计划会议。
- Preparation Needs:
  - 安排准备冲刺与明确时间窗；组织 PO/PM 的验收会议。
- Risk Assessment:
  - 风险：若 Owners 未就时间/优先级达成一致，将影响 Epic B 的启动节奏。

2) Sarah — Product Owner
- Dependencies Check:
  - 确认业务验收标准（PO 签名）与 KPI 指标；优先清单应与 PM 协同定义。
- Preparation Needs:
  - 定义关键业务验证点（功能如何被视为成功）并准备 stakeholder review 模板。
- Risk Assessment:
  - 风险：若业务验证标准不明确，开发可能实现错误优先级的功能。

3) John — Product Manager
- Dependencies Check:
  - 需要 KPI 定义（例如：state_update 到达延迟、每 90s 决策平均耗时、事件写入窗口）。
- Preparation Needs:
  - 制定监控/度量方案与数据采集点（事件/metrics naming），并把采集任务列入准备冲刺。
- Risk Assessment:
  - 风险：无度量会导致无法在未来判断仿真质量和业务成功度。

4) Amelia — Dev
- Dependencies Check:
  - 需要 memoryRepo 快照 API、事件 schema 定义、broadcaster 扩展接口与房间/分区支持。
- Preparation Needs:
  - 实现最小可用的 snapshot/write API（返回 version/timestamp）；为 broadcaster 设计 state_update 消息格式接口。
  - 提前准备 mock LLM adapters 与本地回退 hook 以便并行开发。
- Risk Assessment:
  - 风险：若 fast-path 快照实现不稳定，仿真在并发场景下将出现状态不一致或回放失败。

5) Winston — Architect
- Dependencies Check:
  - 负责定义事件 schema（IEvent）与 state_update contract，包括 version/source/related_event_id。
- Preparation Needs:
  - 输出可机读 schema 文档（JSON Schema / OpenAPI examples）并与 Dev/QA 讨论边界条件。
- Risk Assessment:
  - 风险：若 schema 不兼容历史事件或缺少版本策略，会导致回放/审计难以实现。

6) Mary — Analyst
- Dependencies Check:
  - 需要为 analytics/LLM Adapter 提供事件字段说明与 sample payloads。
- Preparation Needs:
  - 准备事件字段映射文档与示例数据，协助 QA 定义验证规则。
- Risk Assessment:
  - 风险：字段不一致或字段缺失会导致 downstream consumers 崩溃或数据不可用。

7) Murat — Test Architect
- Dependencies Check:
  - 需要 CI 集成的性能 smoke test 脚本与数据生成器（10 NPC 场景）。
- Preparation Needs:
  - 编写并在 CI 中配置 performance smoke tests，定义基线与警报阈值。
- Risk Assessment:
  - 风险：若未提前验证性能，Epic B 进入后期才发现瓶颈会导致大型返工。

8) Sally — UX Expert
- Dependencies Check:
  - 需要 prompt template metadata（id/locale/description）与前端展示设计约束以便展示用例。
- Preparation Needs:
  - 设计模板展示与选择交互、并提供可复制示例文本与短说明供前端渲染。
- Risk Assessment:
  - 风险：若模板信息不够清晰，玩家会创建低质量 prompt 导致仿真行为单一或不可预期。

9) game-dev / game-architect / game-designer
- Dependencies Check:
  - 需要明确 action contract（动作类型、参数、执行后果）以便将 LLM 输出映射为系统动作函数。
- Preparation Needs:
  - 定义核心 action types（move, work, eat, social_interact, trade 等）及其 delta 字段。
- Risk Assessment:
  - 风险：缺少 action contract 会使 LLM 输出与执行逻辑需要大量 glue code，延长开发时间。

---

## 优先级与准备冲刺任务清单（可直接放入 Sprint Backlog）

优先级划分说明：High = 必须在准备冲刺完成以支持 Epic B 启动；Med = 可并行完成但应在第1周内完成；Low = 可后续执行。

High Priority
1. 定义 IEvent 与 `state_update` schema（Owner: Winston; Collaborators: Amelia, Mary; Est: 1-2 days）
2. 实现 memoryRepo 的 snapshot/write API（Owner: Amelia; Est: 2-3 days）
3. 实现 broadcaster 对 `state_update` 的基础支持（Owner: Amelia; Est: 1-2 days）
4. 在 CI 添加 10-NPC 性能 smoke test（Owner: Murat; Est: 1-2 days）

Medium Priority
5. 定义 action contract（Owner: game-architect + game-dev; Est: 1-2 days）
6. 准备 mock LLM adapter 与 local-fallback 测试 hook（Owner: dev; Est: 1 day）
7. 定义 metrics/KPIs 并计划采集点（Owner: John; Est: 1 day）
8. 硬化 player_id 中间件（JWT/session 可替换方案）（Owner: Sarah+Amelia; Est: 1 day）

Low Priority
9. 增强 prompt template metadata（id, locale, description）并扩展前端展示建议（Owner: Sally; Est: 0.5-1 day）
10. 文档化事件回放与审计流程（Owner: Mary + Winston; Est: 1 day）

## 时间线建议
- 准备冲刺（Preparation Sprint）建议：4-7 天并行完成 High Priority 任务（视团队并行能力分配）。
- 若准备冲刺完成且 smoke test 通过，即可正式启动 Epic B。

---

## 已保存输出
- 本步骤输出已保存为： `docs/retrospectives/epic-A-retro-step5.md`

下一步为 Step 6（Synthesize Action Items & Preparation Plan）。请选择：
1) 继续到 Step 6（回复“继续”或“1”）
2) 编辑/调整本步骤内容（回复“编辑”并说明）
3) 停止并保存当前结果（回复“停”或“2”）
