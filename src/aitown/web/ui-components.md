# UI 组件说明 — 文本优先原型

目标

- 定义可复用的前端组件（轻量级、无样式依赖）以便快速在 Vue/React 中实现。

组件清单

1. NPCList
   - 目的：列出所有 NPC 并允许选择
   - Props: none (组件内部从 GET /npc 拉取)
   - Events: select(npc_id)
   - Data shape: [{id,name,hunger,energy,mood,money,inventory}]

2. NPCDetail
   - 目的：展示所选 NPC 详细信息与快速交互按钮
   - Props: npc (object)
   - Events: promptSaved, actionInvoked
   - 内部行为: 展示 `GET /npc/{id}` 返回的对象，支持编辑 prompt 并 POST /npc/{id}/prompt

3. MemoryPanel
   - 目的：展示最近 7 天 memory_log 与长时摘要
   - Props: npc_id
   - Methods: refresh() -> 调用 GET /npc/{id}/memory
   - Events: requestSummarize

4. ActionsPanel
   - 目的：提供上下文相关动作按钮（Buy, Work, Use Item）
   - Props: npc (object), places (array)
   - Events: buy(item_id,place_id), work(place_id), useItem(item_id)
   - Implementation: 显式调用 POST /npc/{id}/buy /work /use-item

5. EventFeed
   - 目的：显示来自 WebSocket 的广播消息（state_update、npc_created 等）
   - Props: none (订阅 /ws)
   - Events: messageClicked

6. MapPanel (新增)
   - 目的：在文本优先 UI 中渲染一个小型格子地图，中心为当前聚焦位置/选中 NPC，显示可一步到达的邻居并支持点击发起强制移动
   - Props: center {x:number,y:number}, size (optional, default 5), cellSize (px)
   - Events: cellClicked({x,y})
   - Methods: render(center)
   - Rendering: 推荐使用 SVG 来绘制格子与连接线（更清晰的邻居连线），每个格子为一个可点击 rect 元素，中心格高亮。
   - Place semantics: MapPanel 仅展示从后端 `GET /places` 返回的登记地点名称（在相应格子中）。格子上如果没有登记地点则为“虚空”（void），不提供移动交互，仅作为视图聚焦目标。
   - Interaction: on cellClicked -> 若为非中心格且当前选中 NPC 存在，则触发 POST /npc/{id}/move 或发送 WS control {type:'control',action:'force_move', npc_id, x, y}

   Implementation notes:
   - SVG advantages: crisp lines, precise hit targets, easy to draw connecting lines between center and neighbors.
   - Accessibility: provide aria-label on each rect with coordinates and role="button" for keyboard users; also allow cell selection via keyboard controls in the MapPanel component.

UI 行为说明补充

- NPC 列表现在仅展示当前 MapPanel 中心格的 NPC；当用户在地图上点击其他格子并将视图聚焦到该格时，NPC 列表随之刷新为该格的 NPC 列表（或显示空列表）。


数据流与通信

- 初始化：页面加载 -> NPCList 获取 /npc -> 渲染列表
- 选择 NPC -> NPCDetail 拉取 /npc/{id} 并填充 MemoryPanel（GET /npc/{id}/memory）
- 编辑 Prompt -> POST /npc/{id}/prompt -> 显示即时确认（optimistic UI），行为在后续 state_update 中体现
- 动作调用（buy/work） -> POST 对应端点 -> 等待 state_update 广播以确认并回写最终状态
- WebSocket `/ws` 用于接收 `state_update`、`npc_created`、`npc_updated` 等；EventFeed 订阅并渲染

错误处理与 UX 约定

- 对后端请求使用短超时并展示轻量级错误提示（toast 或行内错误文本）。
- 对于重要操作（如购买导致 money 变化）应使用 `state_update` 回写校验结果不可逆更改。

可扩展项

- 将组件封装为小型 Vue SFC，可在 `web/` 下创建 `components/` 目录以便继续迭代。
- 提供 mock 数据适配器以支持离线体验与演示。

示例：NPCList -> 事件处理伪代码（Vue）

```text
<NPCList @select="id => selectNPC(id)" />
function selectNPC(id){ this.selectedId=id; this.$refs.detail.load(id); this.$refs.memory.refresh(); }
```
