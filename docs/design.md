# 产品需求文档（PRD） — AI 小镇（初版）

版本: 0.1
作者: PM
日期: 2025-10-09

- Project Level: 2
- Greenfield: true
- Target date / Milestone: 2025-12-01 (可选，估算)
- Team size (initial): 2 devs + 1 PM

## 一、概述

目标：构建一个在局域网内运行的多人观察型沙盒，玩家可以在浏览器中创建并配置 LLM 驱动的 NPC，观察 NPC 在固定地图中生活、工作与社交。系统以“玩家创造 NPC，观察小镇”为核心互动模式。

重要功能:
- 服务器为所有 NPC 提供默认的 OpenAI 兼容 LLM（可配置）；
- LLM 与其他关键系统参数通过启动时读取的默认配置文件（例如 `config.yaml` 或环境变量）进行设置并生效，运行时不依赖管理员接口或管理员手动配置。
- 小镇时间会持续流逝，系统设计为持续运行。
- 玩家修改 NPC 的 prompt 后，变更不会总是立即反映为行为改变；NPC 会在随时间推进的仿真步中基于新 prompt 逐步调整行为。
- 每个玩家只能拥有且管理一个 NPC，且只能编辑自己的 NPC（边界由玩家标识控制）。

- NPC 拥有基本生存属性（饱食度、能量、心情），这些属性归零将导致 NPC 死亡（NPC被标记为死亡，不再出现在小镇中，但玩家可以查看和删除）。
- 小镇拥有若干个地点。
- 地点没有坐标属性，地点之间存在道路。
- NPC只能通过道路从一个地点移动到另一个地点。
- 道路都是双向的，但是道路具有上下左右四种方向属性，用于描述地点之间的相对位置关系。
- 地点拥有多种标签以提供功能，例如shop（可以买卖商品，并提供可购买的商品）、workable（NPC可以在此工作）、private_house（NPC可以购买此建筑并居住）、apratment（NPC可以免费居住的公寓）等。
- NPC 拥有包裹（inventory）与金钱（currency）系统，能够携带物品并用于购买/消费。
- 金钱也是一种物品（item），单位为“金币”，初始时每个NPC拥有100金币。
- NPC 能通过工作赚取金钱，工作地点为小镇上的标签为workable的地点。
- NPC每天会收到服务器发放的基础生存保障金（可配置数量）。
- NPC拥有记忆，分为长期记忆（string）和最近记忆（list[string]），最近记忆只保留7天，超过7天的记忆会与长期记忆融合压缩（通过LLM总结）成为新的长期记忆。
- NPC可以执行的动作包括吃饭、睡觉、工作、休息、购买、售出、玩耍、移动等。
- NPC被创建时玩家可以指定姓名、性别、年龄和prompt，NPC的初始位置默认为小镇广场。
- 仿真采用内部 Event Bus
  - 在每一次仿真迭代结束时：NPC的每次决策（字符串）首先被解析为对内部动作函数（action function）的调用描述（包含动作类型与参数），该调用描述作为NPC动作事件写入 Event Bus。
  - 在下一次仿真迭代开始之前：NPC动作事件由系统的事件消费者读取并实际执行对应的动作函数；动作执行完成后，执行结果（状态变更、交易记录、inventory 更新等）被写入事件日志并用于更新系统快照，这些状态变更在下一次仿真迭代时生效。
  - 每一次仿真过程中，NPC基于自己的prompt并引入自身属性、记忆和环境信息作为上下文，由大模型驱动生成接下来的决策。
- 在MVP版本中，前端仅提供NPC 信息、小镇信息、地点信息、时间信息与社交事件等文字信息展示。用户可以在一个窗口内创建、查看NPC和编辑NPC的prompt，在另一个窗口内看到小镇发生的各种事件。后续版本考虑图形化。
- 玩家的视角始终锁定在自己NPC所在的地点，并且默认只会接收到当前地点发生的事件消息、专门发给自己NPC的消息和世界通告消息。

架构设想：
- 后端采用Python+FastAPI
- 数据库采用SQLite，数据库通过sqlite3库访问
- 通过uvicorn直接部署
- 使用pytest进行单元测试

## 二、已确认的技术决策（团队共识）

- MVP 技术栈：单进程部署 + SQLite（文件数据库）。优点：实现简单、易调试、在局域网内对目标并发足够。
- LLM Provider：默认使用 mock 实现进行本地开发与测试；通过环境变量切换至真实 OpenAI 兼容 provider（例如 OPENAI_API_KEY / PROVIDER=openai）。
- 配置优先于运行时：LLM、基础保障金与关键参数在启动时从 `config.yaml` 或环境变量读取并生效。

## 三、详细架构说明（概览）

关键组件（MVP）：
- API 层（FastAPI）：对外提供玩家、NPC 管理、事件推送等 HTTP / WebSocket 接口。
- 持久层（SQLite）：存储 town, player, npc, place, road, item, memory_entry, npc_memory, event, transaction 等表。
- 仿真引擎（Simulation Engine）：包含 SimClock（可加速/推进）、决策调用（via LLM Adapter）、决策解析器、动作事件写入与事件执行。
- 事件总线（Event Bus）：MVP 为进程内内存队列 + events 表持久化，保证事件顺序与可重放性。
- LLM 适配器（LLM Adapter）：统一接口，支持 mock 与真实 provider。
- 执行器（Action Executors）：实现每个动作（move, eat, sleep, work, buy, sell, idle），负责状态更新与事务记录。
- 记忆管理器（Memory Manager）：维护 recent_memory（7 天）并按需调用 LLM 进行摘要合并到 long_memory。

组件交互简述：
1. SimClock 触发每个 NPC 的决策采集（或在测试/手动触发时推进若干步）。
2. LLM Adapter 返回决策字符串（mock 或真实 provider）。
3. 决策解析器把字符串解析为 Action(type, params)。解析结果写入 events 表与 Event Bus。
4. Event Consumer 在下一次仿真迭代前消费事件并调用对应的 Action Executor，执行结果写入 events 表并更新 NPC 快照。
5. Memory Manager 在合适时机触发记忆压缩（recent -> long）并调用 LLM Adapter 的摘要接口。

## 四、API 草案（主要端点）

- Players:
  - POST /player/register {user_name, passwd} -> 201 {id} (注册玩家， 错误 409: 已存在玩家)
  - POST /player/login {user_naem, passwd} -> 201 {id} （错误 409：账号不存在或密码错误）
- NPCs:
  - POST /npc/create_npc/{player_id} {name, gender, age, prompt} -> 201 {npc_id} (错误 409: 已存在 npc)
  - GET /npc/{npc_id} -> 200 (包含属性、inventory、memory 概览) （错误 404: NPC 不存在）
  - PATCH /npc/{npc_id} {prompt} -> 200 （错误 404: NPC 不存在 | 409: prompt过长）
  - GET /npc/get_all_npc/{player_id} -> 200 (通常该玩家所有的NPC)
- Places & Roads:
  - GET /place/all -> 200 (列表所有地点)
  - GET /place/nearby/{place_id} -> 200 (列出直接相连地点及其方向)
  - GET /place/npcs/{place_id} -> 200 (列出该地点的所有NPC)
  - GET /place/{place_id} -> 200 (包含地点属性、标签、当前NPC列表) （错误 404: 地点不存在）
- Events:
  - WS /event/stream (订阅当前玩家可见事件：当前地点、直达 NPC、world)

示例响应与约定：所有 JSON payload 使用 Pydantic 模型，时间字段为 ISO8601 字符串。

## 五、最小 SQLite Schema（DDL）

为保证开发快速可交付，以下为 MVP 推荐的最小 SQLite DDL（简化版）：

```sql
CREATE TABLE player (
  id TEXT PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE place (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tags TEXT, -- JSON array as TEXT, e.g. '["shop","workable"]'
  shop_inventory TEXT, -- JSON array JSON as TEXT or '[]'
  created_at TEXT NOT NULL
);

CREATE TABLE road (
  id TEXT PRIMARY KEY,
  from_place TEXT NOT NULL,
  to_place TEXT NOT NULL,
  direction TEXT NOT NULL  -- e.g., 'north', 'south', 'east', 'west'
);

CREATE TABLE item (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE memory_entry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  text TEXT,
  timestamp TEXT -- ISO8601
);

CREATE TABLE npc_memory (
  npc_id TEXT PRIMARY KEY,
  long_memory TEXT, -- compressed summary
  recent_memory TEXT -- JSON array as TEXT of memory_entry
);

CREATE TABLE npc (
  id TEXT PRIMARY KEY AUTOINCREMENT,
  player_id TEXT,
  name TEXT,
  gender TEXT,
  age INTEGER,
  prompt TEXT,
  location_id TEXT,
  hunger INTEGER DEFAULT 100,
  energy INTEGER DEFAULT 100,
  mood INTEGER DEFAULT 100,
  inventory TEXT, -- JSON array as TEXT e.g. '[{"item_id":"item1","num":2}]'
  memory_id TEXT,
  is_dead INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT
);

CREATE TABLE event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  event_type TEXT, -- e.g., 'action', 'transaction', 'prompt_updated'
  payload TEXT, -- JSON dict as TEXT of action params e.g. '{"type":"move","params":{"to_place_id":"place2"}}'
  created_at TEXT,
  processed INTEGER DEFAULT 0,
  processed_at TEXT
);

CREATE TABLE transaction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  item_id TEXT,
  amount INTEGER,
  reason TEXT,
  created_at TEXT
);
```

说明：为了尽快交付，JSON 字段以 TEXT 存储；长期可迁移到 PostgreSQL 并使用 JSONB。
