# 八、关键交互与流程（简要）

-- 玩家在前端填写创建表单 → 前端调用 POST /npc（请求需绑定玩家标识）→ 后端创建 NPC（或返回错误当玩家已有 NPC）并广播 npc_created → 所有客户端以文本方式更新界面
-- 后端仿真循环按时调用 LLM Adapter（默认使用服务器端 OpenAI 兼容 API 或玩家指定的 API，具体依配置）→ 更新 NPC 状态/位置并在仿真步中生效 → 广播 state_update
-- 仿真控制（pause/start）仅由管理员通过命令行或受限管理接口发起，普通玩家的 WebSocket `control` 消息将被忽略或返回权限错误
