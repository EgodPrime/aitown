title: "Story 1.5: NPC Prompt 提示库与示例 Prompt + 删除 NPC" 
status: Done
author: Egod
epic: A
story_id: A-05
story_points: 5
priority: Medium

---

# Story 1.5: NPC Prompt 提示库与示例 Prompt

Status: Done

## Story

As a player,
I want a small library of curated example prompts when creating or editing my NPC,
so that I can quickly choose a reasonable starting prompt and learn how prompt changes affect behavior.

## Acceptance Criteria

1. 在创建或编辑 NPC 时，API/前端能返回一组示例 prompts（至少 6 条），来源于项目 `docs/prd.md` 的说明与团队提供的样例。
2. 示例 prompts 存放为只读资源文件（`{project-root}/docs/prompt-templates.json`），并在服务启动时加载到内存（或通过简单读接口按需读取）。
3. API 返回示例时不包含玩家私有信息或可执行凭据；示例为纯文本描述或 prompt 片段。
4. Story 的实现为非交互式：生成示例文件并提供 `GET /prompt-templates` 只读端点（或可由前端直接读取静态文件）。
5. 删除 NPC（A-05）相关：仅资源所有者或管理员可删除 NPC；删除成功返回 200 并广播 `npc_deleted` 到订阅客户端；删除应从活动内存列表移除该 NPC 且保留事件日志中的审计记录；随后对该 id 的 GET /npc/{id} 返回 404 或已标记为已删除的状态。

## Tasks / Subtasks

- [x] 创建 `docs/prompt-templates.json` 并填充至少 6 条示例 prompt
- [x] 添加 `GET /prompt-templates` 只读路由（或在现有静态文件托管下直接提供）
- [x] 在 README 或 docs 中说明如何扩展或替换示例库
- [x] 添加一个快速集成测试，确保 `GET /prompt-templates` 返回 200 且包含最少 6 条条目
- [x] 实现 `DELETE /npc/{id}`（复用现有权限中间件，确保仅资源所有者或管理员可执行）
- [x] 在删除逻辑中清理内存状态并保留事件日志；实现广播 `npc_deleted` 到 WebSocket 订阅客户端
- [x] 添加集成测试覆盖：删除操作的权限（owner vs non-owner）、内存移除、事件日志存在与广播发送

## Dev Notes

- 参考 `docs/prd.md` 中关于 prompt 影响行为与示例的部分。
- 示例为纯文本，不含任何私有 API key/凭证。
- 默认放在 `docs/prompt-templates.json`，后续可迁移至 `src/config` 或数据库。
 
关于删除 NPC 的实现要点（A-05）:
- 所有删除请求必须通过 `player_id` 中间件验证；若缺失返回 401；若非资源所有者且非管理员返回 403。
- 删除应从 `memoryRepo` 或相应内存快照中移除该 NPC 的活动条目；同时在 `memoryRepo.events` 中追加 `npc_deleted` 事件（含 actor, npc_id, timestamp）。
- 删除响应应返回 200 与被删除对象的简要副本（可选择仅返回 id 与删除时间以保持幂等性）。

## Implementation Notes

- The route and file are read-only for MVP; editing templates requires repo change or admin-only API in future.
- Keep prompts short (<= 500 characters) and focused on behavior hints (e.g., "喜欢社交、善于交谈"，"节俭型，优先存钱"等).
 
实现注意（合并项）:
- Prompt 提示库端点与删除 NPC 均应复用现有 auth/player-id 中间件以一致地识别调用者。
- Prompt 文件为只读静态资源，删除 NPC 为对内存状态的修改操作；两者应有清晰的测试覆盖。
- 将 story points 从 2 提升到 5 以反映合并后的工作量（Prompt 库 + 删除 API + 测试）。

## References

- docs/prd.md
- docs/tech-spec-epic-A.md

## Change Log

- 2025-10-08: Draft created by create-story workflow (non-interactive)
 - 2025-10-08: 生成 Story Context XML 并保存为 `docs/story-context-A.A-05.xml`
 - 2025-10-08: 开发完成：实现 prompt 模板端点与 NPC 删除功能，添加测试并全部通过（25/25）。
 - 2025-10-08: 开发完成：实现 prompt 模板端点与 NPC 删除功能，添加测试并全部通过（25/25）。
 - 2025-10-08: Story verified by Dev Story workflow; status set to Done.

## Review Notes

- Review date: 2025-10-08
- Reviewer: Automated Senior Developer Review
- Summary: Implementation meets acceptance criteria. Endpoints added: `GET /api/prompt-templates`, `DELETE /api/npc/:id`. Prompt templates file added. Tests added and all pass.

Action items (post-review):

1. Consider replacing simple admin check (player_id === 'admin') with role-based middleware or environment-configured admin list. (Backlog: A-05-1)
2. Consider loading `prompt-templates.json` at startup into memory for performance (Backlog: A-05-2).
3. Optional: provide localized templates or structured metadata for templates (id, locale) (Backlog: A-05-3).

Status: Ready for final QA and merge.
