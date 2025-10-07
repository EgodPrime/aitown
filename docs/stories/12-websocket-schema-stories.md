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


   Example - full_state (HTTP/WebSocket initial sync):

   ```json
   {
     "type": "full_state",
     "timestamp": "2025-10-05T12:00:00Z",
     "payload": {
       "npcs": [
         {
           "id": "npc123",
           "player_id": "player1",
           "name": "Mia",
           "position": "home",
           "hunger": 78,
           "energy": 55,
           "mood": 42,
           "recent_action": "ate_food",
           "money": 95
         }
       ],
       "places": [
         {"id":"home","label":"Home","capacity":4}
       ],
       "time": "2025-10-05T12:00:00Z",
       "config": {"simulation_interval_s":2.0}
     }
   }
   ```

   Field notes:
   - `type` (string): one of `full_state`, `state_update`, `npc_created`, `npc_updated`, `npc_died`, `welfare_paid`.
   - `timestamp` (ISO 8601 string): event creation time in UTC.
   - `payload` (object): message-specific data (see examples below).

   Example - npc_created:

   ```json
   {
     "type": "npc_created",
     "timestamp": "2025-10-05T12:01:00Z",
     "payload": {
       "id": "npc124",
       "player_id": "player2",
       "name": "Rex",
       "position": "village",
       "hunger": 50,
       "energy": 80,
       "mood": 60,
       "money": 10
     }
   }
   ```

   Example - npc_updated: (partial or full object can be sent in payload)

   ```json
   {
     "type": "npc_updated",
     "timestamp": "2025-10-05T12:02:00Z",
     "payload": {
       "id": "npc123",
       "hunger": 60,
       "recent_action": "slept"
     }
   }
   ```

   Example - npc_died:

   ```json
   {
     "type": "npc_died",
     "timestamp": "2025-10-05T12:03:00Z",
     "payload": {"id": "npc125", "reason": "starved"}
   }
   ```

   Example - welfare_paid: (payment / economy events)

   ```json
   {
     "type": "welfare_paid",
     "timestamp": "2025-10-05T12:04:00Z",
     "payload": {
       "npc_id": "npc123",
       "amount": 50,
       "balance": 145,
       "source": "government_grant"
     }
   }
   ```

   Example - state_update (single NPC update or aggregated list):

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

   Notes on `state_update` payload variants:
   - A `state_update` can be sent as a single-object payload (above) or as an aggregated list under `payload.updates` for multi-NPC broadcasts: `{ "payload": { "updates": [ {..}, {..} ] } }`.
   - Use `delta` to indicate numeric changes since prior state (optional).

