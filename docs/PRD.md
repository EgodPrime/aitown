```markdown
# aitown Product Requirements Document (PRD)

**Author:** Egod
**Date:** 2025-10-09
**Project Level:** 2
**Project Type:** Game (多人观察型沙盘)
**Target Scale:** Local LAN MVP

---

## Description, Context and Goals

本项目旨在构建一个在局域网内运行的多人观察型沙盘，玩家可以创建并配置由 LLM 驱动的 NPC，NPC 在固定地图中生活、工作与社交。核心体验为“玩家创建 NPC，观察小镇”，强调低进入门槛与持续仿真。

### Deployment Intent

MVP 在局域网/内网部署以便快速迭代与用户测试；可作为 Demo/POC 向早期用户展示核心玩法。

### Context

当前对 LLM 与代理型 NPC 的兴趣快速增长，本项目通过提供可配置的 NPC 与可视化观察沙盘，使开发者与玩家能快速体验和验证 LLM 驱动的互动行为。

### Goals

- 交付一个可在局域网内运行的 MVP，包含 NPC 的创建、查看、编辑与基本仿真行为
- 提供统一的 LLM 适配层（支持 mock 与 OpenAI-compatible provider），并能在启动时读取配置切换 provider
- 提供简单持久化（SQLite）与事件驱动的仿真引擎，保障事件顺序与可重放性

## Requirements

### Functional Requirements

FR001: 玩家可以注册与登录（POST /player/register, POST /player/login）
FR002: 玩家可以创建 NPC，并为 NPC 指定 name, gender, age, prompt（POST /npc/create_npc/{player_id}）
FR003: 玩家可以查看单个 NPC 的详情（GET /npc/{npc_id}）与其列表（GET /npc/get_all_npc/{player_id}）
FR004: 玩家可以编辑 NPC 的 prompt（PATCH /npc/{npc_id}）且变更应逐步在仿真中生效
FR005: 系统提供地点（place）与道路（road）接口，以支持 NPC 移动（GET /place/*）
FR006: 系统以事件驱动模型记录并处理 NPC 行为（事件队列、event 表）
FR007: 提供 WebSocket 事件流（WS /event/stream）以向客户端推送实时世界/NPC 事件
FR008: 实现基本经济系统（inventory 与 currency）并支持交易记录（transaction 表）
FR009: Memory 管理：recent memory 保持 7 天，超过后由 LLM 摘要合并至 long memory
FR010: LLM Adapter 支持 mock 与真实 provider，通过环境变量或 config 切换

### Non-Functional Requirements

NFR001: MVP 可在一台开发机器或小型局域网内稳定运行（低部署复杂度）
NFR002: 事件处理保证顺序性与可重放性（在 MVP 使用进程内队列）
NFR003: API 响应时间目标：多数请求 < 300ms（除 LLM 相关请求）
NFR004: 数据持久化为 SQLite（JSON 字段以 TEXT 存储以便快速交付），并记录创建/更新时间戳

## User Journeys

Primary Journey — 创建并观察 NPC：
1. 玩家注册并登录
2. 在界面中创建 NPC（填写基础属性与 prompt）
3. NPC 出现在小镇的默认位置并开始按 SimClock 运行决策
4. 玩家通过页面/WS 观察 NPC 行为，查看其 inventory、memory 与事件流
5. 玩家可编辑 NPC 的 prompt，系统在后续仿真步逐步将变更体现为行为变化

## UX Design Principles

- 清晰可视化：让玩家一眼看到 NPC 的位置与关键信息
- 低复杂度：核心操作（创建、查看、编辑）应在 1-2 步内完成
- 可观察性：提供事件流与 memory 视图，便于调试与理解 NPC 行为

## Epics

1. Core Simulation & Engine
2. Player & NPC Management

（详见 `epics.md`）

## Out of Scope

- 生产级水平的横向扩展与多服务器部署
- 复杂商业化功能（内购、结算系统）
- 高级分析/指标平台（后期可外接）

---

## Next Steps

1. 生成并确认 `epics.md`（本次已生成）
2. 启动 solutioning/workflow（生成 per-epic tech-spec）
3. 细化用户故事与验收标准（generate-stories）

## Document Status

- [ ] Goals and context validated with stakeholders
- [ ] All functional requirements reviewed
- [ ] User journeys cover all major personas
- [ ] Epic structure approved for phased delivery
- [ ] Ready for architecture phase

_Note: See technical-decisions.md for captured technical context_

---

_This PRD adapts to project level 2 and provides focused requirements for implementation._

```