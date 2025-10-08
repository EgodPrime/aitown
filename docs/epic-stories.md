# Epic Stories — AI 小镇

版本: 0.1
作者: 自动生成
日期: 2025-10-08

## 概要
本文件为 Level 2 项目的史诗与故事草案。目标将 PRD 中的功能拆分为可实施的 epic 与故事（含标题与简短描述）。后续将为每个故事补充验收准则与优先级。

---

## Epic A — NPC 管理与展示
目标：实现玩家创建/查看/编辑/删除 NPC 的核心用户流程与只读展示接口。

Stories:
1. A-01: 创建 NPC（POST /npc） — 表单提交，返回新 NPC 并广播 `npc_created`。
	Acceptance Criteria:
	- POST /npc 返回 201 并返回满足 NPC schema 的 JSON 对象（包含 id、player_id、name、prompt、initial_stats）。
	- 当玩家已经存在活跃 NPC 时返回 409 并带有解释错误消息。
	- 成功创建时发送 WebSocket 事件 `npc_created`，订阅客户端能收到并显示新 NPC。
	- 在内存存储中能查询到该 NPC，并可通过 GET /npc/{id} 读取到相同数据。
	Priority: High
	Story Points: 5
2. A-02: 查看 NPC 列表（GET /npc） — 支持分页与简要状态快照。
	Acceptance Criteria:
	- GET /npc 返回 200 与列表结果，包含 pagination 元数据（limit/offset/total 或 cursor）。
	- 列表项包含简要状态字段（hunger, energy, mood, location）以供快速渲染。
	- 当无数据时返回空数组并正确展示 pagination 元信息。
	Priority: High
	Story Points: 3
3. A-03: 查看单个 NPC（GET /npc/{id}） — 返回完整状态与 memory_log（recent/old）。
	Acceptance Criteria:
	- GET /npc/{id} 返回 200 与完整 NPC 对象，包括 memory_log、inventory、transactions 简要引用。
	- memory_log 中 recent_memory 包含最近 7 天条目（按时间倒序），old_memory 提供压缩摘要字段。
	- 非存在 id 返回 404；无权限访问（若存在权限模型）返回 403。
	Priority: High
	Story Points: 3
4. A-04: 更新 NPC prompt（PATCH /npc/{id}/prompt） — 仅允许资源所有者，前端立即显示最新 prompt。
	Acceptance Criteria:
	- 仅资源所有者可成功调用，成功返回 200 与更新后的对象；非所有者返回 403。
	- 更新后，调用者的会话或随后 GET /npc/{id} 能立即看到最新 prompt，但系统不会广播该 prompt 给其他玩家。
	- 更新操作在事件日志中记录一条 `prompt_updated` 记录（包含 actor、timestamp、diff 可选）。
	Priority: Medium
	Story Points: 3
5. A-05: 删除 NPC（DELETE /npc/{id}） + Prompt 提示库（GET /prompt-templates） — 清理内存状态并提供示例 prompt 静态库。
	Acceptance Criteria:
	- 仅资源所有者或管理员可删除；成功返回 200 并广播 `npc_deleted` 到订阅客户端。
	- 删除应从活动内存列表移除该 NPC 并释放相关短期缓存；事件日志保留审计记录（包含 actor、timestamp）。
	- 随后对该 id 的 GET /npc/{id} 返回 404 或已标记为已删除的状态。
	- 提供只读的 prompt 示例库（`GET /prompt-templates` 或静态文件 `docs/prompt-templates.json`），至少包含 6 条示例 prompt，示例不得包含私有凭证。
	Priority: Medium
	Story Points: 2

---

## Epic B — 仿真引擎与行为生成
目标：实现仿真循环、LLM Adapter（及本地回退策略）、事件总线与 state_update 广播。

Stories:
1. B-01: 仿真时钟与日结机制 — 实现 36 分钟 = 1 天的仿真时钟与日结触发。
	Acceptance Criteria:
	- 仿真时钟以可配置比率运行（默认 36 分钟 = 1 天），系统能返回当前仿真时间 API（如 GET /time）。
	- 在仿真日轮转时触发日结事件并记录到事件日志（包含触发时间与受影响 NPC 列表）。
	- 日结触发后 1s 内生成并记录保障金入账事件（若启用）。
	Priority: Medium
	Story Points: 3
2. B-02: 仿真循环：周期性行为生成（默认 90 秒） — 为每个 NPC 调度决策生成任务。
	Acceptance Criteria:
	- 系统定期（默认每 90 秒）为活跃 NPC 调度决策生成任务并记录开始/完成时间。
	- 决策生成的结果会在完成后写入事件日志并触发相应 state_update 广播。
	- 在高延迟或失败情况下（例如单次生成超时），系统使用本地回退策略并记录 `local-fallback` 事件。
	Priority: High
	Story Points: 5
3. B-03: LLM Adapter 接口与 mock 实现 — 支持实时调用与本地回退策略（5s 超时）。
	Acceptance Criteria:
	- 提供统一的 LLM Adapter 接口契约文档（方法/超时/异常格式）。
	- 提供可在本地运行的 mock adapter，返回结构化的行为描述以供仿真执行和测试。
	- 当真实 LLM 调用超时超过 5s 或失败时，自动切换到本地回退实现并在事件日志中标注来源。
	Priority: High
	Story Points: 5
4. B-04: 事件总线与事件日志 — 将行为描述写入事件总线并记录审计日志、写入快照。
	Acceptance Criteria:
	- 所有行为描述均以事件形式写入事件总线并持久化到事件日志（包含 timestamp、npc_id、action、source）。
	- 在事件消费并执行动作后，写入内存快照并将快照版本号与事件关联。
	- 事件日志支持按 NPC/时间范围查询并导出用于回放。
	Priority: High
	Story Points: 5
5. B-05: state_update 广播规范与实现 — WebSocket 广播消息包含 timestamp、npc_id、delta、version。
	Acceptance Criteria:
	- WebSocket `state_update` 消息包含必需字段：timestamp、npc_id、delta_changes、new_state_snapshot、version。
	- 订阅客户端能在承受常见网络波动下接收并按 version 去重处理消息。
	- 在广播失败场景应有重试或降级策略并记录失败事件。
	Priority: High
	Story Points: 5

---

## Epic C — 地点与经济交互
目标：实现小镇地点功能（如餐馆、市场）与 NPC 的基本经济行为（购买/工作/交易）。

Stories:
1. C-01: 地点数据模型与 GET /places 接口 — 返回地点列表与静态属性（价格/收益）。
	Acceptance Criteria:
	- GET /places 返回 200 与地点数组，数组内每项包含 id、name、type、price/reward（如适用）、description。
	- 前端能根据返回字段正确渲染地点列表与基本交互提示。
	Priority: Medium
	Story Points: 3
2. C-02: 购买/消费逻辑由仿真执行 — 在仿真步中处理购买请求并更新 inventory/money。
	Acceptance Criteria:
	- 购买动作由仿真循环在决策阶段执行：扣减 NPC.money，增加 NPC.inventory，并在事件日志中记录交易。
	- 购买后相关 state_update 被广播且前端显示 inventory 与 money 的更新。
	- 当余额不足时，购买请求被记录为失败并返回合适的失败原因（记录于事件日志）。
	Priority: Medium
	Story Points: 5
3. C-03: 工作行为与收益模型 — 在特定地点执行工作以赚取 money（消耗 energy）。
	Acceptance Criteria:
	- Work 行为执行成功时，会在 transactions 中生成收益记录并增加 NPC.money（数值合理且可配置）。
	- Work 行为会消耗 energy 并在 state_update 中反映能量变化。
	- 工作收益与消耗遵循配置的收益模型，且在回退或异常时有明确的降级策略。
	Priority: Medium
	Story Points: 5

---

## Epic D — 记忆、日志与审计
目标：实现 NPC 的 memory_log、recent/old 存储策略与可查询的事务/日志接口。

Stories:
1. D-01: memory_log 数据结构与 GET /npc/{id}/memory — 支持 recent_memory（7 天）与 old_memory（压缩摘要）。
	Acceptance Criteria:
	- GET /npc/{id}/memory 返回 200 并包含 recent_memory（最近 7 天逐日条目）与 old_memory（LLM 压缩摘要）。
	- recent_memory 的条目按时间倒序且每条包含 timestamp、summary、source_event_id。
	- 系统能在后台将超过 7 天的条目归档并写入 old_memory 摘要，摘要可追溯到原始事件集合。
	Priority: Medium
	Story Points: 5
2. D-02: 事件日志与事务查询（GET /npc/{id}/transactions） — 记录日结保障金、购买与工作收益。
	Acceptance Criteria:
	- GET /npc/{id}/transactions 返回按时间排序的事务列表（包含类型、amount、timestamp、related_event_id）。
	- 日结保障金、购买、工作收益均以事务记录形式存在且可用于核对余额变化。
	- 事务查询支持分页与时间范围过滤，返回数据与内存快照中的 money 字段一致。
	Priority: Medium
	Story Points: 3

---

## Sprint Candidates (最小冲刺候选列表)

下面给出针对初始团队（2 dev, 2 周冲刺假设）规划的前三个冲刺候选。每个冲刺包含建议的故事集合与估算点数。请根据团队实际速度调整。

Sprint 1 (目标：交付可演示的最小仿真与 NPC 创建路径) — Capacity target: ~20 points

Sprint 1 Total: 20 pts

Sprint 2 (目标：完善展示接口、单体查询与事件写入)

Sprint 2 Total: 20 pts

Sprint 3 (目标：经济、记忆与清理功能)

Sprint 3 Total: 23 pts

Notes:
- 优先级标注基于 MVP 必需性（High = 必需以进行演示或核心功能；Medium = 支持性功能），请与团队讨论并据此调整排期。
- 若团队速度偏低（例如每冲刺仅 10–12 pts），则将 Sprint 1 拆分为两个更小的交付（例如先完成 A-01 + B-03，然后 B-02 + B-05）。


---

## 待办（下一步）
1. 为每个故事补充详细验收准则与优先级。  
2. 将高优先级故事拆分为可在单个冲刺内完成的任务并估算点数。  
3. 根据需求启动 solutioning workflow 以生成 tech-spec 与架构草案（推荐，Level 2）。

---

文件生成器：BMAD Plan Workflow (自动草案)
