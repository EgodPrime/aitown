```markdown
# Project Workflow Analysis

**Date:** 2025-10-09
**Project:** aitown
**Analyst:** Egod

## Assessment Results

### Project Classification

- **Project Type:** Game (多人观察型沙盘，基于 NPC 与 LLM 的交互)
- **Project Level:** 2
- **Instruction Set:** prd  (current)

> Routing note: 检测到项目类型为 "Game"，路由器默认建议使用 GDD (game design doc) 路径 — 即将 instruction_set 设为 `gdd` 会触发游戏专用的规划工作流。当前文档保留 PRD 路线作为已存在的决策；如果你希望遵循路由器建议，我可以把 Instruction Set 改为 `gdd` 并切换后续生成的模板。

### Scope Summary

- **Brief Description:** 构建一个在局域网内运行的多人观察型沙盘，玩家可创建并配置 LLM 驱动的 NPC，NPC 在固定地图中生活、工作与社交，系统以“玩家创建 NPC，观察小镇”为核心交互模型。
- **Estimated Stories:** 5-15
- **Estimated Epics:** 1-2
- **Timeline:** 目标里程碑 2025-12-01（估算）

### Context

- **Greenfield/Brownfield:** Greenfield（新项目）
- **Existing Documentation:** PRD（当前文档）
- **Team Size:** 2 devs + 1 PM
- **Deployment Intent:** 在局域网内运行（本地/内网部署作为 MVP）

## Recommended Workflow Path

### Primary Outputs

- Focused PRD（当前已有）
- 技术规格（Tech Spec）用于实现细节和数据库 schema
- 简要 epics / story 列表以支持开发排期

### Workflow Sequence

1. 生成并确认 `project-workflow-analysis.md`（本文件）作为路由决策依据
2. 运行 Level 2 路径：调用 PRD 子工作流（instructions-med），并同时生成 tech-spec（tech-spec/workflow）
3. 补全 epics 与 story 列表，输出 `epics.md` 与 `project backlog`
4. 技术实现：SQLite MVP、FastAPI 后端、LLM adapter mock → 切换至 OpenAI provider 的部署说明

### Next Actions

- 已确认：继续 PRD 路径并采用 4 阶段 Epic 顺序（Data models & repos → Business logic & services → Frontend & API → Integration & QA）。
- 接下步操作：生成并审阅 `epic-stories.md`（已生成为 `docs/epic-stories.md`），随后实现并测试仓储(`backend/src/aitown/repos`)、数据初始化 (`backend/src/aitown/db.py`)。

若你同意，我会按照 PRD workflow（`bmad/bmm/workflows/2-plan/prd/workflow.yaml` 的 `instructions-med.md`）继续生成 `PRD.md` 更新草稿，并在每个 `template-output` 点请求你的确认。

## Special Considerations

- LLM 配置优先在启动时从 `config.yaml` 或环境变量读取（支持 mock 与 OpenAI provider 的切换）
- Memory 管理规则：recent memory 保持 7 天，超出后由 LLM 摘要合并至 long memory
- Event Bus 设计：内部事件队列保证事件顺序与可重放性，MVP 使用进程内队列
- 数据存储在 MVP 阶段使用 SQLite（JSON 字段以 TEXT 存储），后期可迁移到 PostgreSQL + JSONB

## Technical Preferences Captured

- Backend: Python + FastAPI
- Database: SQLite (MVP)
- Server: uvicorn
- Testing: pytest
- LLM Provider: mock for dev/test; OpenAI-compatible provider via env (OPENAI_API_KEY / PROVIDER=openai)
- Storage format: JSON stored as TEXT in SQLite for MVP

---

_This analysis serves as the routing decision for the adaptive PRD workflow and will be referenced by future orchestration workflows._

```