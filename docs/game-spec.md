# AI 小镇 - 规格说明书 (草案)

目标

- 在局域网内运行的多人观察型沙盒：玩家在本地网络中通过浏览器连接，创建并配置 NPC（由 LLM 驱动），观察 NPC 在固定地图中生活、工作、社交。

技术栈（用户要求）

- 前端：Vue + AntV（使用 AntV G6 做小镇/节点可视化）
- 后端：FastAPI + Python
- LLM：可插拔的适配器（开发阶段使用 Mock 模型；可配置接入 OpenAI 等服务）

核心玩法 / 功能

- 固定地图（2D 平面，坐标系）
- 玩家可以创建 NPC：设置名称、初始位置、行为 Prompt（自然语言），可选择性别/职业等元数据
- NPC 按照其 Prompt 驱动行为：周期性决定行动（移动、工作、社交、休息、发言等）并与其他 NPC 互动
- 后端运行 NPC 仿真循环，定期将状态更新推送给所有通过 WebSocket 连接的客户端
- 玩家主要操作：创建 NPC、修改 NPC 的 prompt、观察/播放/暂停仿真

简明契约（输入/输出、数据格式）

- NPC 对象（JSON）
  - id: str
  - name: str
  - prompt: str
  - x: float
  - y: float
  - metadata: dict (职业、年龄、性别等可选)
  - state: dict (当前行动、心情、上一条动作等)

- API
  - POST /npc -> 创建 NPC，返回 NPC 对象
  - GET /npc -> 返回全部 NPC 列表
  - GET /npc/{id} -> 单个 NPC
  - POST /npc/{id}/prompt -> 更新 prompt
  - WS /ws -> 推送事件流 {type: "state_update", payload: {...}}，并接收控制消息 {type: "control", action: "pause"}

- LLM Adapter 接口
  - generate_action(npc: NPC, context: dict) -> {action: str, meta: dict}
  - 可替换为真实 LLM 调用。实现需无阻塞或异步支持。

假设与限制（当前原型）

- LLM 调用会被封装，可在局域网环境中使用外部 API（需要互联网）也可在本地用 Mock。
- 初版使用内存存储（非持久化），适合局域网演示与测试；生产版应接入 DB（Postgres/SQLite）和鉴权。
- 并发量：示例适用于几十个 NPC；若需要数百/千级别，应优化消息广播与仿真性能。

边缘情况

- NPC prompt 非法/空：使用默认行为（闲逛）并记录告警
- LLM 超时/错误：采用退避策略/回退到本地规则
- 前端断开重连：前端在重连后拉取最新完整列表并继续监听 WS

优先级与里程碑（建议）

1. 最小可用原型（MVP）
   - 后端：FastAPI 实现 NPC CRUD + WebSocket 推送 + 简单模拟器（Mock LLM）
   - 前端：单页应用（Vue CDN + AntV G6 CDN），显示固定地图与 NPC，支持创建 NPC
2. 可插拔 LLM
   - 提供 adapter 模板，注释说明如何配置 OpenAI API
3. 持久化与多机部署
   - 引入 Postgres、任务队列（Celery / RQ）和鉴权

下一步

- 我可以现在生成一个可运行的原型：包括后端服务（FastAPI）与前端单页（Vue + AntV CDN）。
- 你想让我先：
  1. 生成并启动后端原型（我会在项目里加入 `server/`）
  2. 先做更详细的 PRD 与玩法细节（我会更新 `docs/`）

请告诉我你的偏好，或者直接回复“开始实现原型”。


---

## 详细数据契约（JSON Schema 草案）

下面的 schema 为开发实现提供参考：字段说明、类型、示例和业务约束。

1) NPC 对象（npc.json）

```json
{
  "$id": "https://example.com/schemas/npc.json",
  "type": "object",
  "required": ["id","name","player_id","x","y","prompt","state"],
  "properties": {
    "id": {"type":"string","description":"UUID"},
    "name": {"type":"string"},
    "player_id": {"type":"string","description":"玩家标识，确保每玩家仅有一个 NPC"},
    "prompt": {"type":"string"},
    "x": {"type":"number"},
    "y": {"type":"number"},
    "metadata": {"type":"object","additionalProperties": true},
    "state": {
      "type":"object",
      "properties": {
        "action": {"type":"string"},
        "text": {"type":"string"},
        "last_updated": {"type":"string","format":"date-time"}
      }
    },
    "hunger": {"type":"number","minimum":0},
    "energy": {"type":"number","minimum":0},
    "mood": {"type":"number","minimum":0},
    "money": {"type":"number","minimum":0},
    "inventory": {
      "type":"array",
      "items": {"$ref":"#/definitions/item_ref"}
    },
    "social_relations": {
      "type":"array",
      "items": {"$ref":"#/definitions/social_relation"}
    },
    "memory_log": {
      "type":"array",
      "items": {"$ref":"#/definitions/memory_entry"}
    },
    "alive": {"type":"boolean"}
  },
  "definitions": {
    "item_ref": {
      "type":"object",
      "required":["item_id","name"],
      "properties":{
        "item_id":{"type":"string"},
        "name":{"type":"string"},
        "type":{"type":"string"},
        "quantity":{"type":"integer","minimum":1},
        "meta":{"type":"object","additionalProperties":true}
      }
    },
    "social_relation":{
      "type":"object",
      "required":["other_id","relation","score"],
      "properties":{
        "other_id":{"type":"string"},
        "relation":{"type":"string","enum":["friend","neutral","enemy"]},
        "score":{"type":"number"}
      }
    },
    "memory_entry":{
      "type":"object",
      "required":["date","events","summary"],
      "properties":{
        "date":{"type":"string","format":"date"},
        "events":{"type":"array","items":{"type":"string"}},
        "summary":{"type":"string","description":"LLM 生成的摘要（当日志被压缩时使用）"}
      }
    }
  }
}
```

2) Item（物品）结构（item.json）

```json
{
  "$id": "https://example.com/schemas/item.json",
  "type":"object",
  "required":["item_id","name","type"],
  "properties":{
    "item_id":{"type":"string"},
    "name":{"type":"string"},
    "type":{"type":"string","description":"e.g., food, tool, misc"},
    "price":{"type":"number","minimum":0},
    "effects":{"type":"object","description":"消费或使用后对 NPC 属性的影响，如 {\"hunger\": +20}"}
  }
}
```

3) Place（地点）结构（place.json）

```json
{
  "$id":"https://example.com/schemas/place.json",
  "type":"object",
  "required":["place_id","name","type","actions"],
  "properties":{
    "place_id":{"type":"string"},
    "name":{"type":"string"},
    "type":{"type":"string","description":"e.g., restaurant, market, plaza, factory"},
    "x":{"type":"number"},
    "y":{"type":"number"},
    "actions":{
      "type":"array",
      "items":{"type":"object","properties":{
        "action_id":{"type":"string"},
        "name":{"type":"string"},
        "price":{"type":"number"},
        "reward":{"type":"number"},
        "energy_cost":{"type":"number"}
      },"required":["action_id","name"]}
    },
    "meta":{"type":"object","additionalProperties":true}
  }
}
```

4) Social relations（social_relations）结构

Social relations 可以嵌入 NPC 对象的 `social_relations` 字段，每条记录包含对方 id、关系类型与亲密度分数。参见上方 NPC schema 中的 `social_relation` 定义。

5) Memory log（memory_log）

Memory log 的条目为逐日事件列表与摘要。开发注意：系统需要提供一个周期任务，用 LLM 将 7 天之前的多条事件压缩为一条摘要（示例：`summarize_memory(npc_id, events)`）。摘要文本应保留其来源时间段的索引，以便审计。


## 推荐 API 示例

- GET /npc/{id}/memory -> 返回 `memory_log`（包含最近 7 天的清晰条目和历史摘要条目）
- POST /admin/summarize-memory -> 管理员触发手动摘要（可用于回溯）
- GET /places -> 返回地点列表（每个地点包括 `actions` 字段）
- POST /npc/{id}/buy -> body: { item_id, place_id }
- POST /npc/{id}/work -> body: { place_id }
- POST /npc/{id}/use-item -> body: { item_id }

以上 schema 为草案；开发团队可据此实现数据模型与数据库表结构（例如 NPC 表、Inventory 表、Transactions 表、Places 表、MemoryEntries 表 等）。
