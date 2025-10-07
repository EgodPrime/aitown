# Tech Spec — Epic B: Simulation Engine & Behavior

## Overview
Epic B implements the simulation loop, LLM Adapter integration, event bus, and state update broadcasting.

## Stories Covered
- B-01: 仿真时钟与日结机制
- B-02: 仿真循环：周期性行为生成
- B-03: LLM Adapter 接口与 mock 实现
- B-04: 事件总线与事件日志
- B-05: state_update 广播

## Components
- `simulationService` — scheduler and orchestrator
- `adapters/llm` — LLM interface and implementations
- `ws/broadcaster` — state_update emission
- `events` — append-only event log and snapshot writer

## Data Models
- Event model (IEvent) — structured payload, source, and timestamp

## Implementation Notes
- LLM calls must respect a 5s timeout; on timeout use local fallback.
- Decisions are translated to action functions that mutate NPC state atomically.
- Persist events to event log for replay and auditing.

## Testing
- Mock adapter integration tests
- Performance test: seed 10 NPCs and ensure decision cycles complete within acceptable time
