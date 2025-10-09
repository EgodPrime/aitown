# title: "Story A.1 — 设计并验证最小 SQLite schema（Data Models & Repos）"
# status: Done
# author: Egod
# epic: A
# story_id: A-01
# story_points: 3
# priority: Medium

---

# Story A.1 — 设计并验证最小 SQLite schema（Data Models & Repos）

Author: Egod
Date: 2025-10-09

简述
------
为 MVP 实现并验证一套最小可用的 SQLite schema（player、place、item、npc、memory_entry、event、transaction 等表），并保证迁移脚本可在内存或临时文件数据库上运行以供 CI/本地快速验证。

动机与背景
----------------
此故事为 Epic A 的首要任务，目的是建立可靠且可重复的持久层基础，供 Repository 层和上层服务（SimClock、Event Bus、Action Executors）依赖。参见 `docs/PRD.md`、`docs/epic-stories.md` 中对数据模型与持久化的需求说明。

接受标准 (Acceptance Criteria)
--------------------------------
1. 提供 SQL 迁移文件（或脚本）`migrations/0001_init.sql`，能够在空 SQLite 数据库（包含内存连接 ":memory:")上创建下列表：player、place、road、item、npc、memory_entry、event、transaction。
2. 提供初始化脚本（例如 `backend/src/aitown/helpers/init_db.py`），能接收 SQLite 连接字符串或已打开的连接并执行迁移与可选种子数据插入。
3. 每个表包含至少以下必需字段（见下方“建议 schema”），并为外键约束和索引提供合理默认（例如 npc.location_id → place.id、transaction.npc_id → npc.id）。
4. 在 `backend/tests/unit` 下有至少一个集成级别/单元测试用例：在内存 DB 上运行迁移并断言关键表存在与关键列存在。
5. README 或 docs/db.md 中记录字段含义、JSON 字段约定与示例（例如 tags、shop_inventory 存为 JSON 字符串）。

建议 schema（已与 migrations/0001_init.sql 对齐）
-------------------
- player
  - id TEXT PRIMARY KEY
  - display_name TEXT NOT NULL
  - password_hash TEXT
  - created_at TEXT NOT NULL

- place
  - id TEXT PRIMARY KEY
  - name TEXT NOT NULL
  - tags TEXT
  - shop_inventory TEXT
  - created_at TEXT NOT NULL

- road
  - id TEXT PRIMARY KEY
  - from_place TEXT NOT NULL (FK -> place.id)
  - to_place TEXT NOT NULL (FK -> place.id)
  - direction TEXT NOT NULL

- item
  - id TEXT PRIMARY KEY
  - name TEXT NOT NULL
  - description TEXT

- npc
  - id TEXT PRIMARY KEY
  - player_id TEXT (FK -> player.id) ON DELETE SET NULL
  - name TEXT
  - gender TEXT
  - age INTEGER
  - prompt TEXT
  - location_id TEXT (FK -> place.id) ON DELETE SET NULL
  - hunger INTEGER DEFAULT 100
  - energy INTEGER DEFAULT 100
  - mood INTEGER DEFAULT 100
  - inventory TEXT DEFAULT '[]' (JSON array stored as TEXT)
  - memory_id TEXT (FK -> npc_memory.npc_id)
  - is_dead INTEGER DEFAULT 0
  - created_at TEXT
  - updated_at TEXT

- npc_memory
  - npc_id TEXT PRIMARY KEY
  - long_memory TEXT
  - recent_memory TEXT

- memory_entry
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id)
  - text TEXT
  - timestamp TEXT

- event
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id)
  - event_type TEXT
  - payload TEXT
  - created_at TEXT
  - processed INTEGER DEFAULT 0
  - processed_at TEXT

- transactions (表名为复数 `transactions`)
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id) ON DELETE SET NULL
  - item_id TEXT (FK -> item.id) ON DELETE SET NULL
  - amount INTEGER
  - reason TEXT
  - created_at TEXT

索引（migration 中已创建）
- idx_npc_player ON npc(player_id)
- idx_npc_location ON npc(location_id)
- idx_event_npc_created_at ON event(npc_id, created_at)
- idx_transactions_npc ON transactions(npc_id)

实现任务（Implementation Tasks）
---------------------------------
1. 确认并更新 `migrations/0001_init.sql`，将上述字段与外键/索引写入（若已存在则校验并补充）。
2. 编写或更新 `backend/src/aitown/helpers/init_db.py`，接受 sqlite3.Connection 或文件路径并运行迁移、可选地注入最小种子数据（player 示例、place 示例、item 示例）。
3. 在 `backend/src/aitown/` 中核对/补充 Repository 接口签名（PlayerRepo, PlaceRepo, ItemRepo, NpcRepo, EventRepo, TransactionsRepo），保证能在后续故事中实现 CRUD。
5. 撰写 `docs/db.md`，列出每张表、字段描述、JSON 字段示例与约定（例如：tags 存为 JSON array stringified；inventory 为 list of {item_id, num}）。

测试计划（Test Notes）
---------------------
- 单元/集成测试：在 sqlite ":memory:" 上运行 `init_db`，使用 PR 的测试样例验证表存在并能进行基本 CRUD。
- 边界测试：插入带有大型 JSON 字段（数 KB）并验证读回完整性；插入违反 FK 的数据以确认 FK 约束行为（取决于是否启用 PRAGMA foreign_keys = ON）。

数据约定示例
----------------
place.tags 示例： `[]` 或 `["shop","market"]`

place.shop_inventory 示例：
```
["coin", "apple", "bread"]
```

依赖项
-------
- 参照 `docs/PRD.md` 与 `docs/epic-stories.md` 中的 Epic A 要求。
- 后续 Story A.3 将实现具体的 Repository 方法，A.4 将覆盖单元测试。

风险与注意事项
----------------
- SQLite JSON 存为 TEXT，查询/更新需要在应用层解析/串行化；如果日后需更复杂查询，需评估引入 JSON1 扩展或换数据库。
- FK 行为依赖 PRAGMA foreign_keys 的开启状态；测试与迁移脚本需显式设置以避免平台差异。

完成定义（Definition of Done）
---------------------------
1. `migrations/0001_init.sql` 和 `backend/src/aitown/helpers/init_db.py` 已提交。
2. 至少一个测试在内存 DB 上可以运行以验证表/列存在并执行一次基本插入（见 `backend/tests/unit/test_helpers_init_db.py`）。
3. `docs/db.md` 在 `docs/` 下完成并记录字段含义与 JSON 约定。

## Dev Agent Record

### Context Reference

 - `docs/story-context-A-01.xml`

### Agent Model Used

BMAD dev-story workflow (action-workflow)

### Completion Notes

- 手动核验：迁移脚本 `migrations/0001_init.sql` 包含建议的表、外键与索引。
- 实现：初始化辅助函数 `backend/src/aitown/helpers/init_db.py`，支持传入连接字符串或已打开的 sqlite3.Connection，并可选择插入种子数据。
- 测试：新增/更新单元测试 `backend/tests/unit/test_helpers_init_db.py`（在项目测试环境下用于验证内存 DB 的迁移与种子行为）。

### File List

- migrations/0001_init.sql — 创建所有必需表、外键与索引
- backend/src/aitown/helpers/init_db.py — 初始化脚本，执行迁移并可插入 seed
- backend/tests/unit/test_helpers_init_db.py — 验证 init_db 在 ":memory:" 上工作并测试异常/种子行为
- docs/db.md — 文档，记录 schema、字段含义与 JSON 约定

### Change Log

- 2025-10-09: 标记为 Done，记录实现文件与测试位置；人工核验完成。

### Status

Status: Done

Estimated effort: 3-5 story points (small)

---
自动生成：基于 `docs/PRD.md`、`docs/epic-stories.md` 与仓库现有测试样例。若需要将 story 写入不同编号（例如 A.2/A.3），请回复具体触发词或编号以运行交互更新。
