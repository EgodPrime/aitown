# aitown - Epic Breakdown

**Author:** Egod
**Date:** 2025-10-09
**Project Level:** 2
**Target Scale:** Local LAN MVP

---

## Epic Overview

本文件已按优先级重设计：先开发数据模型与持久层（包含 schema、仓储接口与迁移脚本），其次实现核心业务逻辑（仿真引擎、事件处理、记忆管理），随后实现后端 API 与 WebSocket，最后开发前端可视化与可观测性工具。

下面的 epic 顺序严格对应你提出的开发策略（数据层 → 业务层 → API → 前端）。每个 epic 包含建议的 story 与验收准则，并列出关键依赖。

## Epics（按执行顺序：4 大阶段）

下面将原先的多个 epics 精简为你指定的 4 个主要 Epic，以严格对应你的开发顺序：

### Epic A: 数据模型与仓储（Data Models & Repos）

- Story A.1: 设计并确认最小 SQLite schema（表：player, place, road, item, npc, memory_entry, event, transaction）
- Story A.2: 实现迁移/初始化脚本（schema init + seed data）
- Story A.3: 设计并实现 Repository 层（接口 + SQLite 实现，支持事务）
- Story A.4: 为 Repository 编写单元测试（SQLite 内存或临时文件）
- Story A.5: 编写数据库访问文档（字段说明、JSON 字段约定、示例 queries）

验收准则:
- Schema 与迁移脚本能成功创建并填充示例数据
- Repository 覆盖 CRUD 与事务场景，且有自动化单元测试
- 文档清楚说明 JSON 字段用法与约束

依赖关系: 无（优先完成）

### Epic B: 核心业务逻辑与服务（Domain Logic & Services）

- Story B.1: 实现 SimClock（可控速度、暂停、单步）和基本仿真循环
- Story B.2: 实现 Event Bus 与事件持久化（写入 event 表）
- Story B.3: 实现 Action Executors（move, eat, sleep, work, buy, sell, idle）并通过 Repository 修改状态
- Story B.4: 实现 Memory Manager（recent → long 的摘要策略）并与 LLM Adapter 集成（mock 实现）
- Story B.5: 实现服务层（npc_service, player_service, simulation_service）并编写服务层单元测试

验收准则:
- 使用 SimClock 能在本地运行多步仿真并把事件写入 DB
- Action Executors 能正确更新实体状态并记录相应交易/事件
- Memory 管理按规则工作（包含测试覆盖）

依赖关系: 完成 Epic A

### Epic C: 前端与 API（Frontend & API）

- Story C.1: 设计并实现后端 HTTP API（玩家、NPC、place、event）与 Pydantic 验证
- Story C.2: 实现 WebSocket 实时事件流（/ws/events）并与仿真事件源对接
- Story C.3: 实现简单前端（SPA）用于注册、创建 NPC、观察地图与事件流（可用静态文件或轻量框架）
- Story C.4: 为关键 API 与 WS 编写集成测试

验收准则:
- 后端 API 能通过集成测试完成主要调用
- WebSocket 客户端能订阅并接收实时事件
- 前端能完成核心用户旅程（注册→创建 NPC→观察）

依赖关系: 完成 Epic B

### Epic D: 系统联调与质量保证（Integration & QA）

- Story D.1: 编写端到端（E2E）集成测试覆盖从前端到后端的主要流
- Story D.2: 配置 CI（pytest、lint）并在 PR 中执行测试
- Story D.3: 性能与并发基本测试（并发写入、事件吞吐）
- Story D.4: 准备部署与运行文档（本地 LAN 部署说明、环境变量、启动脚本）

验收准则:
- E2E 测试能覆盖核心用户旅程并在 CI 中通过
- CI 在 PR 中执行并阻止测试失败的合并
- 有基本的运行文档使团队能在本地复现环境

依赖关系: 完成 Epic C

---

## 优先级与执行说明

1. 严格按顺序交付：Epic A → Epic B → Epic C → Epic D
2. 测试与 CI（部分属于 Epic D）应尽早并行启动，尤其是单元测试在 Epic A/B 实施时就应同时搭建
3. 每个 Epic 在完成时必须包括：
	- 验收准则通过的测试（单元/集成/端到端各自对应）
	- 简明的交付说明（如何运行、如何验证）

```
