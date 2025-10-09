title: "Retrospective — Epic A (Step 2): Next Epic Preview & Dependency Analysis"
date: 2025-10-08
epic: A
next_epic: B
next_epic_title: "Simulation Engine & Behavior"
facilitator: "Bob (Scrum Master)"

---

# 回顾草稿 — 第 2 步：预览下一个史诗与依赖评估

此文档基于 `docs/tech-spec-epic-B.md` 与已完成的 Epic A 实现（见 `docs/stories/`），评估 Epic B 对 Epic A 的依赖并给出准备任务建议。

## 1) 下一个史诗简介
- 史诗 ID: B
- 标题: Simulation Engine & Behavior
- 关键目标: 实现仿真循环、LLM Adapter、事件总线、state_update 广播与事件/快照持久化

## 2) Epic B 的关键需求（摘自 `tech-spec-epic-B.md`）
- 仿真时钟与日结机制（36 分钟 = 1 天）
- 周期性决策/调度（默认 90 秒）
- LLM Adapter（含 mock）与 5s 超时回退策略
- 结构化事件模型与持久化（事件日志 + 快照写入）
- `state_update` WebSocket 广播规范（timestamp, npc_id, delta_changes, new_state_snapshot, version）
- 性能目标：10 个 NPC 决策在可接受时间内完成，回退策略可用

## 3) 对 Epic A 的依赖映射（B -> A）
1. NPC 数据模型与 API（POST/GET/GET/{id}/PATCH/DELETE）
   - 依赖原因: 仿真引擎需要读取/写入 NPC 基本数据（hunger, energy, mood, inventory, money, location, prompt 等）。
   - Epic A 状态: 已实现基础 CRUD 与 prompt 更新 / 删除 行为（stories A-01..A-05）。

2. 事件日志与内存快照接口（append-only events + snapshot write）
   - 依赖原因: 仿真动作必须以事件形式写入日志并触发快照写入，保证回放/审计与一致性。
   - Epic A 状态: Stories 提及 `memoryRepo.events` 与事件记录（npc_created, prompt_updated, npc_deleted 等）。当前实现为内存事件记录，需确认快照/版本号与持久化策略是否满足 B 的要求。

3. WebSocket 广播基础设施（ws/broadcaster）
   - 依赖原因: 仿真要通过 `state_update` 广播将决策结果发送给客户端。
   - Epic A 状态: 已实现 `npc_created` 和 `npc_deleted` 广播（story notes）。但 `state_update` 的格式与性能尚归属于 Epic B 实现范围。

4. 身份与权限（player_id middleware）
   - 依赖原因: 操作所有权（创建/更新/删除）必须可靠，仿真与事件必须关联 actor/owner。
   - Epic A 状态: 使用 `x-player-id` 简易中间件 / req.player_id，覆盖测试场景；生产需替换为 JWT/session。

5. Prompt 更新可见性约定
   - 依赖原因: 仿真在行为生成时需要使用最新 prompt（可能在下一个仿真步生效），需有一致的数据可见策略。
   - Epic A 状态: PATCH prompt 已实现为仅对请求者可见且记录事件（prompt_updated）——满足 B 的可用性假设。

## 4) 已满足 vs 需补强（快速结论）
- 已满足 / 可复用：
  1. NPC CRUD 与 prompt 更新、删除行为（A-01..A-05）。
  2. 基础事件记录（内存级别）与 `memoryRepo.events` 概念存在。
  3. WebSocket 广播基础设施（用于 npc_created/npc_deleted）。
  4. 测试覆盖（每 story 描述有对应单元/集成测试）。

- 需补强 / 风险项：
  1. 事件模型规范化与版本（IEvent 结构、source、version、related_event_id）需与 B 的 `state_update` schema 对齐并文档化。
  2. 快照写入保证：B 要求“行为生成后 5s 内写入快照并记录版本号”，需要验证当前 `memoryRepo` 是否支持 snapshot/versioning 与并发写入约束，或需实现。
  3. `state_update` 格式实现（timestamp, npc_id, delta_changes, new_state_snapshot, version）当前未在 A 中全面定义——归属 B，需要接口契约并在 A 的 broadcaster 中预留兼容点。
  4. 性能与并发：A 的内存实现需评估在 10+ NPC 与仿真周期下的表现（尤其事件写入与广播延迟）。建议运行性能 smoke tests。
  5. LLM Adapter（mock + 超时回退）为 B 的范围，但 A 的行为记录/事件应能记录 `source`（例如 `llm` 或 `local-fallback`）。确认事件模型支持该字段。

## 5) 推荐准备任务（Short actionable items）
以下任务建议在开始 Epic B 之前完成或并行同步实施，已按优先级排序并提供建议所有者：

1) 定义并验证事件模型与 `state_update` schema（高，Owner: Winston (architect), Collaborators: Amelia (dev), Murat (tea)) — Est: 1-2 days
   - 产出: `docs/schema/event.md`（IEvent 定义）与 `docs/schema/state_update.md`（字段说明与示例 payload）。
   - 验证: 单元测试覆盖序列化/反序列化与版本兼容性。

2) 实现快照/versioning 最低限度支持（高，Owner: Amelia (dev), Architect review: Winston） — Est: 2-3 days
   - 要求: `memoryRepo` 提供写快照 API（写入时返回 version/timestamp），并在事件写入后触发快照写入路径。
   - 验证: 集成测试确保行为生成 -> 事件写入 -> 快照写入在 5s 窗口内完成。

3) 扩展 broadcaster 以支持 `state_update` 格式（中高，Owner: Amelia (dev), QA: Murat） — Est: 1-2 days
   - 要求: 广播模块支持按房间/订阅过滤，且可处理高频 `state_update` 消息（性能考量）。

4) 定义回退源标记与事件 `source` 字段（中，Owner: Mary (analyst) + Dev） — Est: 0.5-1 day
   - 要求: 事件中包含 `source: llm|local-fallback|system`，并在事件日志中记录回退原因。

5) 性能 smoke test（跑 10 NPC 的仿真循环与广播，测 90s 节奏下延迟/吞吐）（高，Owner: Murat (tea), Collaborators: game-dev） — Est: 1-2 days
   - 目标: 确认在默认环境下 10 个 NPC 的决策/写快照/广播在目标时间窗内完成；若不满足，记录瓶颈并提出优化（批量广播、限速或分区）。

6) 权限与 player_id 中间件硬化（中，Owner: Sarah (po) + Amelia (dev)) — Est: 1 day
   - 要求: 确保中间件可在生产环境替换为 JWT/session，且事件/快照中包含 actor 信息。

7) 会议准备（Scrum Master）: 排定准备冲刺（如果需要）并在下次计划会议中列入 action items（Owner: Bob (sm)) — Est: 0.5 day

## 6) 优先级与建议时间线
- 建议在下一次准备冲刺（Preparation Sprint）中完成任务 1、2 与 3（总估计 4-7 天，可并行部分工作）。
- 同步进行性能 smoke test（任务 5）以决定是否需要架构调优（例如广播分区或事件队列）。

## 7) 输出与下步
- 本草稿已保存为： `docs/retrospectives/epic-A-retro-step2.md`（请在仓库中查看）
- 建议下一步：执行 Step 3（初始化回顾并生成回顾头版摘要），我将在 Step 3 中组合度量/质量/行动项并请求你的交互式确认。

请回复（中文可）：
1) 执行 Step 3（回复“继续”或“1”）
2) 需要先修改/补充本 Step2 内容（回复“编辑”并指出）
3) 停止并保存当前结果（回复“停”或“2”）
