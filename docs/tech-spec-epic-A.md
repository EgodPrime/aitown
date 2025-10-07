# Tech Spec — Epic A: NPC Management & Display

## Overview
Epic A implements core CRUD and read-only interfaces for NPC management and display.

## Stories Covered
- A-01: 创建 NPC
- A-02: 查看 NPC 列表
- A-03: 查看单个 NPC
- A-04: 更新 NPC prompt
- A-05: 删除 NPC

## Components
- `npcService` — handles domain logic for CRUD and state consistency
- `repos/memoryRepo` — in-memory storage with snapshot support
- `routes/npc` — REST API handlers
- `ws/broadcaster` — broadcasts `npc_created` and `npc_deleted`

## Data Models
- INPC (see `docs/tech-spec.md`)

## APIs
- POST /npc
- GET /npc
- GET /npc/{id}
- PATCH /npc/{id}/prompt
- DELETE /npc/{id}

## Implementation Notes
- Ensure idempotency and player ownership checks.
- Broadcast `npc_created` and `npc_deleted` via WebSocket after successful mutations.

## Testing
- Unit tests for `npcService` and API handlers.
- Integration test: create NPC → verify WebSocket `npc_created` event.

## Post-Review Follow-ups
- [x] Add logging for NPC creation in npcService.create (references Story A-01).
