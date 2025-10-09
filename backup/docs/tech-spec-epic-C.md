# Tech Spec — Epic C: World Model & Persistence

## Overview
Epic C implements the world graph (places, paths), item persistence, inventories, and snapshotting.

## Stories Covered
- C-01: 地图与地点模型（IPlace, IPath）
- C-02: 道具与背包持久化（IItem, IInventory）
- C-03: 快照与恢复（snapshotting）
- C-04: 数据存储适配器（memory/sqlite）

## Components
- `worldService` — place/path graph manager
- `storage` — pluggable storage adapter (MemoryStore, SqliteStore)
- `snapshotter` — periodic snapshots of authoritative state

## Data Models
- ITown, IPlace, IPath, IItem, IInventory (see tech-spec.md for interfaces)

## Implementation Notes
- Use adjacency lists for place graph.
- Snapshot interval: configurable, default 5 minutes or N events.

## Testing
- Persistence round-trip tests
- Restore from snapshot tests
