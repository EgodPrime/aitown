## UI Wires & Text-First Design — AI 小镇 (MVP)

目标

- 提供一个完全以文本为主的前端展现，满足 PRD 中“前端为文本驱动”的要求。
- 优先支持观察 NPC 列表、查看单个 NPC 的状态与 memory_log、编辑 NPC prompt、触发购买/工作/使用物品 等动作。
- 在信息密度与可读性间取得平衡，面向非技术普通用户（家庭、教育场景）。

主要页面与模块

1. 控制台 / 主视图
   - 顶部: 仪表栏（当前虚拟时间、仿真状态：Running / Paused、连接状态）
   - 左侧: NPC 列表（按 name 列出），每项显示简短摘要：name | player_id | 简要状态（hunger/energy/mood）
   - 中间: 详细面板（当选中一个 NPC）：显示 NPC 基本信息（name, prompt 摘要, location, money, inventory 摘要）、当前 action / last_text、最近的 memory_log（最近 7 天以详细条目呈现）以及“长时记忆摘要”（来自 LLM 的 compress）
   - 右侧: Actions 面板（context-aware 动作按钮）：Buy Food, Work, Use Item (下拉选择 inventory), Edit Prompt（打开内联编辑器）
    - 中间偏上/地图面板: 显示以当前选中 NPC 为中心的小地图（见下方 Map 面板说明），在地图上通过纵向/横向线段显示可一步到达的位置（上下左右邻居），并允许点击地块发起强制移动请求。
   - 底部: 事件流 / 系统广播（按时间倒序显示 `state_update`、npc_created、npc_updated、purchase/work 日志）

2. 创建 NPC 弹窗 / 表单（文本表单）
   - 简单字段：name, starting prompt (textarea), optional metadata JSON（可选）
   - 提交后调用 POST /npc 并在成功后在事件流显示 npc_created

3. Prompt 编辑器（内联）
   - 支持纯文本编辑与“保存”按钮；提交后调用 POST /npc/{id}/prompt，前端展示提示："Prompt updated — changes take effect gradually during simulation"

4. Memory 面板
   - 显示最近 7 天的 memory_log（逐日条目）
   - 显示“长时记忆摘要”文本（若存在），并提供按钮“请求重生成摘要”（调用 POST /admin/summarize-memory）

   6. Map 面板（新增）
      - 目的：在文本 UI 中渲染小镇地图，但只显示明确登记的地点（places）；其它格视为“虚空”（void），不作为地点交互目标。
      - 语义说明：地图以格子坐标为基础，但格子中只会展示 `places` 列表里存在的地点名（例如 Market、Restaurant、Plaza）。用户看到的不是坐标列表，而是地点名或空白（虚空）。
      - 布局：位于详细面板上方或侧边，呈 5x5（可配置）方格，以选中 NPC 的位置所对应的格子为中心。中心格以明显样式标记；若中心格无登记地点，则显示为中心的“虚空”格。
      - 可达视觉：在中心与其正交邻格（上下左右）之间画可视线段，但仅当邻格包含登记地点时才高亮线段，表示该方向上有一步可达的地点。
      - 交互：
        - 点击包含地点的格子会触发“前往该地点”的强制移动请求（frontend 尝试使用 POST /npc/{id}/move body {place_id}；若后端不支持 place_id 参数，则退回到使用坐标 {x,y}）。
        - 点击虚空格仅会把视图聚焦到该格（用于观察），但不会发起移动请求。
      - NPC 列表行为变更：NPC 列表现在只显示当前地图中心格对应地点（若存在）的 NPC；若中心为虚空，则列表为空。
      - 强制移动的规则说明（UI 层面）：
         - 点击目标地点会发送强制移动请求；后端应在下一次该 NPC 的行动（仿真周期）前把该请求作为 NPC 的下一个行动目标（实现细节需后端支持）。
         - 若后端不支持该 API，前端将回退为通过 WebSocket 发送 control 消息作为备用信号（需后端监听并实现），并在事件流中记录“移动请求已发送”。


5. Admin 控制（仅在发现当前用户为管理员时显示）
   - Pause Simulation / Start Simulation（发送 WebSocket control 消息或调用 admin API）
   - 手动触发 memory summarization

高保真文本布局示例（主视图）

| 仪表栏: Town Time: 2025-10-05 09:12 | Simulation: Running | WS: Connected |
| NPC 列表 (左) | Map & 详细面板 (中)                              | Actions (右) |
| - Alice (A001) | Map (5x5, center = Alice at 12,5):              | [Buy Food]   |
| - Bob   (B002) |  ---------------------------                    | [Work]       |
| ...            | | 11,7 | 12,7 | 13,7 | 14,7 | 15,7 |           | [Use Item]   |
|                | |-----------------------------|                 | [Edit Prompt]|
|                | | 11,6 | 12,6 | 13,6 | 14,6 | 15,6 |           |              |
|                | | 11,5 | 12,5 | 13,5 | 14,5 | 15,5 | <- center |              |
|                | | 11,4 | 12,4 | 13,4 | 14,4 | 15,4 |           |              |
|                | | 11,3 | 12,3 | 13,3 | 14,3 | 15,3 |           |              |
|                |  ---------------------------                    |              |
|                | Name: Alice                                    |              |
|                | Prompt: "A friendly baker..."                  |              |
|                | Location: Market (x:12,y:5)                     |              |
|                | Money: 12.50                                   |              |
|                | Inventory: [ Bread x2 ]                        |              |
|                | Recent Memory:                                 |              |
|                | - 2025-10-04: Bought bread at Market (+5 hunger)|              |
--------------------------------------------------------------------------------
| Event Feed: [2025-10-05 09:11] state_update: Alice moved to Market ...            |
--------------------------------------------------------------------------------

可访问性与交互要点

- 使用较大字号与清晰的行高以提高可读性（文本为主的 UI 需要良好排版）。
- 将关键数值（hunger/energy/mood/money）以短文本或小徽章形式突出显示。示例：h:45 e:80 m:+10 $
- 对于触发类动作（buy/work）在本地先做乐观更新并显示 loading，实际结果以 `state_update` 广播为准并回写最终状态。

验收标准

- 用户可以创建一个 NPC 并在列表中看到它（POST /npc -> ws 广播 npc_created）。
- 用户能选中 NPC 并查看最近 7 天的 memory_log（GET /npc/{id}/memory）。
- 用户能编辑 prompt 并看到即时确认消息，且 NPC 的行为在随后仿真周期中逐步体现。 
- Admin 可见且可操作 Pause/Start 控制（且普通玩家看不到）。

设计备注（与开发对齐）

- 前端只以文本为主，不要求头像或复杂图形；地图坐标以文字或简易 ASCII/表格显示。
- WebSocket 消息结构与 `state_update` 保持为文本 JSON，前端仅做渲染与过滤。
- 为避免频繁 UI 抖动，事件流应合并短时间内来自同一 NPC 的多条冗余更新（节流/去重策略）。
