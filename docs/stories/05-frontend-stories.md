```markdown
# 05 - 前端展示：用户故事

1. 文本优先展示
   - 作为玩家，我希望界面以文本展示 NPC 列表、地点、时间与事件流，以便在低带宽/低工期下完成演示。
   - 验收标准：前端页面能渲染 NPC 列表、当前仿真时间、地点列表与事件流（从 WebSocket 接收）。

2. 地点动作提示
   - 作为玩家，当我查看某地点时，界面应展示可用动作及成本/收益（buy, work）。
   - 验收标准：`GET /places` 返回动作与参数；前端在地点视图显示这些信息。

## QA Results

- Reviewer: qa
- Date: 2025-10-05
- Story: 05 - 前端展示：用户故事 (story-05)
- Result: Passed MVP acceptance criteria on manual review. The frontend renders NPC list, current simulation time, places list and event stream; place view shows available actions and parameters from `GET /places`.

Notes:
- Recommendation: mark story-05 status as Done in the tracker and proceed to implementation of additional UI polish stories if desired.
```
