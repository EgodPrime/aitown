```markdown
# 12 - WebSocket message schema: developer story

1. WebSocket message examples
   - 作为前端开发，我需要明确的 WebSocket 消息示例以便实现解析与展示。
   - 验收标准：库中包含 `full_state`, `state_update`, `npc_created`, `npc_updated`, `npc_died`, `welfare_paid` 的 JSON 范例与字段说明。

   Example - state_update:

   ```json
   {
     "type":"state_update",
     "timestamp":"2025-10-05T12:00:00Z",
     "payload":{
       "npc_id":"npc123",
       "position":"p1",
       "hunger":78,
       "energy":55,
       "mood":42,
       "recent_action":"ate_food",
       "delta":{
         "money":-5
       }
     }
   }
   ```

   Example - full_state: includes `npcs[]`, `places[]`, `time` and `config`.

