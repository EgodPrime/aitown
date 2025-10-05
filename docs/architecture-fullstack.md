# Architecture — AI 小镇 (Full-Stack)

版本: 0.1
作者: architect
日期: 2025-10-05

概述

此文档为 AI 小镇（MVP -> 生产演进）的全栈架构说明。目标是提供清晰的系统分层、组件接口、数据模型与部署建议，便于开发团队把 PRD 中的功能（NPC 仿真、LLM 驱动动作、内存摘要、基于地点的移动）安全、可扩展地实现。

顶级组件

- Frontend (Text-first SPA)
  - 轻量 Vue/React 单页或静态页面原型（`web/ui-text-prototype.html` 为参考实现）
  - 负责展示 NPC 列表、详情、Memory、事件流与 SVG 地图
  - 通过 REST 与 WebSocket 与后端通信

- Backend API (FastAPI prototype)
  - 负责 CRUD、仿真调度、LLM 调用封装、事件广播 WebSocket
  - 核心职责：NPC 管理、Places 管理、Actions (buy/work/use/move)、memory_log 存取、admin 控制

- LLM Adapter
  - 抽象层：实现统一接口 (generate_action(npc, context) -> action payload)
  - 支持多实现：mock (离线测试)、service-default (服务端 OpenAI), player-provided (可选，需安全处理)

- Persistence
  - 初期：SQLite 或本地文件（快速迭代）
  - 推荐生产：Postgres（ACID）、可扩展到分库/分表
  - 模式：NPCs, Places, Items, Inventory, Transactions, MemoryEntries, Users/Players, APIKey (加密存储)

- Task Queue / Worker
  - 用于异步、可伸缩的 LLM 请求与长时任务（memory summarization），建议 Celery / RQ / Dramatiq

- WebSocket Broker
  - WebSocket 连接由 FastAPI (uvicorn + websockets) 管理。生产可考虑使用 Redis pub/sub 或消息代理（Kafka/RabbitMQ）解耦广播与后端工作进程。

- Monitoring & Observability
  - Metrics: request latency, LLM call rate, queue backlog
  - Logs: structured logging, correlation ids for events
  - Tracing: optional (OpenTelemetry)

高层数据流（示例）

1. 玩家在前端提交 `POST /npc` -> 后端验证 player_id 限制并在 DB 中创建 NPC -> 广播 `npc_created` 到 WebSocket 客户端。
2. 仿真循环每 90s/ NPC 触发：Worker 从 DB 读取 NPC 状态、构造 context (hunger, energy, mood, memory snippet, nearby places) -> 调用 LLM Adapter -> 解析 action -> 更新 DB 状态并广播 `state_update`。
3. 玩家点击地图的 place -> 前端发起 `POST /npc/{id}/move {place_id}` -> 后端将该请求入队（或写入 NPC.next_action）以在下次仿真周期生效 -> 广播移动请求事件。

API 设计（建议）

- Public / Player APIs (authenticated)
  - POST /npc { name, prompt, player_id } -> 201 created
  - GET /npc -> list NPCs (可分页/过滤)
  - GET /npc/{id} -> NPC detail
  - POST /npc/{id}/prompt { prompt } -> 200
  - GET /npc/{id}/memory -> recent 7 days + long-term summary
  - POST /npc/{id}/buy { item_id, place_id } -> 200
  - POST /npc/{id}/work { place_id } -> 200
  - POST /npc/{id}/move { place_id } -> 202 accepted (queued)
  - POST /npc/{id}/use-item { item_id } -> 200

- Admin APIs (protected)
  - POST /admin/summarize-memory { npc_id } -> trigger summarization
  - POST /admin/sim/control { action: start|pause } -> control sim

- Realtime WebSocket
  - Endpoint: /ws
  - Client -> Server messages: {type:'control', action:'pause'|'start'|'force_move', ...}
  - Server -> Client messages: {type:'state_update', payload: {...}}, {type:'npc_created'}, {type:'npc_updated'}

数据模型 & 重要字段（简要）

- NPC
  - id, name, player_id, prompt, x,y 或 place_id, state {hunger,energy,mood,money,inventory[]}, alive, memory_log

- Place
  - place_id, name, x, y, type, actions[] (buy/work), meta

- MemoryEntry
  - id, npc_id, date, events[], summary, source_range

- Item / Inventory / Transaction
  - 标准电商式记录：item_id, price, effects

LLM 集成模式与成本控制

- 可插拔 Adapter：统一接口供仿真调用。Adapter 层负责：请求构建、温控（temperature）、token限制、失败退避与降级。
- 成本控制策略：批量并发限制、优先使用 mock/local adapter 在演示环境、对高频调用做采样、启用缓存（重复 prompt）和批处理（同一时间段内相似请求合并）。

安全、隐私与玩家提供的 API 密钥

- 玩家可选择提供私有 OpenAI-compatible key（可选）。严格规定：
  - 在后端仅以加密形式短期存储（例如使用 KMS 或加密字段），并限制用途与 TTL
  - 所有密钥访问需审计日志；公开回退到服务端默认 adapter

- 身份与权限
  - 玩家仅能管理其 own NPC（post/create/delete/edit prompt）
  - Admin role 才能 pause/start 仿真或触发全局 summarization

扩展性与伸缩方案

- 单机演示：FastAPI + 单进程 worker + SQLite
- 小规模部署：Uvicorn workers behind nginx, Postgres, Redis for pub/sub & Celery workers
- 大规模：Kubernetes deployment, autoscaling workers, Redis/Kafka for event streaming, sidecar for tracing/logging

运维与运行手册要点

- 配置管理：全部敏感配置使用环境变量或 secrets 管理（Kubernetes Secrets / Vault）
- 数据迁移：使用 Alembic 管理 Postgres schema 变更
- 回归与 Canary：逐步发布 LLM 模型切换或 adapter 插件

实施计划（3 周示例）

Week 0 — 验证与对齐
- 需求验收（PM/PO 确认 API contract）

Week 1 — MVP 后端 + 仿真
- 实现 FastAPI CRUD + in-memory/SQLite persistence
- 实现 WebSocket 广播
- 实现 mock LLM Adapter 与简单仿真循环

Week 2 — 前端与交互
- 文本原型完善（SVG 地图、事件流）
- 实现 POST /npc/{id}/move 与 place 映射

Week 3 — 异步 & 持久化
- 引入 Postgres、Redis、Celery 做持久化与异步 LLM 调用
- 引入简单 admin 控制面板

风险与缓解

- LLM 调用成本过高：缓解 -> mock 本地、批量化、采样、速率限制
- WebSocket 广播成为瓶颈：缓解 -> Redis pub/sub 或消息代理分离广播
- 玩家提供密钥泄露风险：缓解 -> KMS、加密、短到期、最小化暴露

附录：示例 FastAPI move 路由草案

```py
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post('/npc/{npc_id}/move')
async def move_npc(npc_id: str, payload: dict):
    # payload 可以是 {place_id} 或 {x,y}
    place_id = payload.get('place_id')
    if place_id:
        # validate place exists, enqueue or set npc.next_target
        enqueue_move(npc_id, place_id=place_id)
        return {"status":"accepted"}
    x = payload.get('x')
    y = payload.get('y')
    if x is not None and y is not None:
        enqueue_move(npc_id, x=x, y=y)
        return {"status":"accepted"}
    raise HTTPException(status_code=400, detail='invalid payload')
```

结语

该文档为第一版全栈架构蓝图。下一步：将 API contract 转为 OpenAPI/JSON Schema（用于前后端自动化），并开始第一周的实现任务分配与故事拆分。
