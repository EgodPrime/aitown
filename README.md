# AITown TypeScript Backend (scaffold)

This repository contains a minimal Node.js + TypeScript scaffold that provides the HTTP endpoints and a WebSocket-based simulation broadcast skeleton for the AI Town prototype.

Quick start (requires Node.js >= 18):

1. npm install
2. npm run dev

Build: npm run build
Start (production): npm run start

# AI 小镇 - 原型

本仓库包含一个简单的原型：TypeScript 后端 + Vue 前端（CDN）用于在局域网内演示 LLM 驱动 NPC 的仿真小镇。

运行步骤（本地 / 局域网）

1. 安装依赖

```bash
npm install
```

2. 启动开发服务（在 0.0.0.0 上监听以便局域网访问）

```bash
npm run dev
```

3. 在局域网其他机器上打开浏览器，访问 `http://<host-ip>:3000/` 或项目中指定的前端路径。

说明

- 后端接口位于 `/api/*` 前缀下（在开发中，前端通过相对路径访问 `/api/npc` 等）。
- WebSocket 地址示例：`ws://<host>:3000/api/ws`（端口根据 `src/index.ts` 配置）
- 当前后端使用的是 `mock` LLM 逻辑，行为非常简单。替换或扩展 `src/adapters/llm` 中的实现以接入真实 LLM。

改进建议 / 下一步

- 增加持久化（SQLite/Postgres）
- 将 LLM 调用抽象为可配置适配器（支持 OpenAI、local LLM）
- 增加简单用户界面让玩家编辑 NPC 的 prompt
- 增加地图与位置边界检测、碰撞与可访问区域

欢迎告诉我接下来要做什么：
- 我可以把后端服务启动并提供调试检查步骤
- 我可以继续完善前端交互（例如可拖放 NPC，显示对话气泡）
- 将 LLM 适配器改成 OpenAI 示例实现（你需要提供 API key）

Configuration
-------------

You can tune the simulation timing with two environment variables:

- `AITOWN_SIMULATION_INTERVAL` — seconds between automatic simulation steps (default: `2.0` for dev; recommended `90` for production).
- `AITOWN_TICKS_PER_DAY` — how many simulation ticks make up one in-game day (default: `24`).

For example, to get a 36-minute in-game day set:

```bash
export AITOWN_SIMULATION_INTERVAL=90
export AITOWN_TICKS_PER_DAY=24
```

This will result in 24 * 90s = 2160s = 36 minutes per in-game day.
