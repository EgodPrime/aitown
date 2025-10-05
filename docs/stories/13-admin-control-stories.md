```markdown
# 13 - Admin simulation control

1. Admin pause/start
   - 作为管理员，我需要通过受保护的接口或 CLI 暂停/恢复仿真，以便在维护或调整时停止世界推进。
   - 验收标准：实现 `/admin/simulation/pause` 和 `/admin/simulation/resume`（或等效 CLI）受单个 ADMIN_TOKEN 环境变量保护；普通玩家调用返回 403；在 pause 状态下仿真循环不再触发 state_update。
