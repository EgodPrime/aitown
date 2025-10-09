# aitown - Technical Specification

**Author:** Egod
**Date:** 2025-10-08
**Project Level:** 2
**Project Type:** Web application
**Development Context:** Greenfield / MVP single-node prototype

---

## Source Tree Structure

Suggested starting source tree for the TypeScript implementation (minimal):

- src/
  - index.ts            # App entry, server bootstrap
  - server.ts           # Express / WebSocket server wiring
  - simulator.ts        # Simulation loop and scheduler
  - adapters/
    - llm.ts            # LLM Adapter interface + mock implementation
  - models/
    - npc.ts            # NPC types and in-memory model
    - place.ts
    - item.ts           # Item model (id, name, type, effects)
    - inventory.ts      # Inventory model and helpers
    - npcRelationship.ts# Social relations between NPCs (friend/neutral/enemy + score)
    - path.ts           # Path model representing edges between places (from, to, cost)
    - events.ts         # Event and transaction models
  - repos/
    - memoryRepo.ts     # In-memory snapshot & persistence adapter
  - services/
    - npcService.ts
    - simulationService.ts
  - routes/
    - npc.ts            # REST endpoints
    - places.ts
    - time.ts
  - ws/
    - broadcaster.ts    # WebSocket broadcasting utilities
  - utils/
    - clock.ts          # simulation clock utilities
    - logger.ts
  - types/
    - index.ts          # shared interfaces

---

## Technical Approach

Goal: Deliver a Level‑2 MVP that supports 10 concurrent NPC simulations on a single node, with mockable LLM adapter and robust fallback. Focus on clear separation: REST API + WebSocket broadcaster + simulation loop + LLM Adapter.

Key decisions:
- Use an in-memory authoritative state for MVP with optional periodic snapshot to disk (JSON) for debugging. Persisted DB is optional for MVP.
- LLM Adapter provides a common interface with two implementations: MockAdapter (default) and OpenAIAdapter (configurable via startup config). Timeout for LLM calls: 5s.
- Simulation loop is a scheduler that enqueues decision tasks per NPC at a configurable interval (default 90s). Each decision produces an action event which is applied to the in-memory state and emitted over WebSocket.
- Use event logging for auditability: every decision and state change is appended to an append-only event log (file or in-memory array) with timestamps and source.

---

## Implementation Stack

- Runtime: Node.js (>=18)
- Language: TypeScript
- HTTP: express
- WebSocket: ws (or socket.io if you prefer richer client features)
- Dev tooling: ts-node-dev or nodemon + tsc for build
- Testing: vitest / jest
- Linting: eslint + Prettier

Optional (post-MVP): SQLite / Postgres, Prisma or knex for persistence

---

## Technical Details

1. model (TypeScript interface)

```ts
interface INPC {
  id: string;
  playerId: string;
  name: string;
  prompt: string;
  hunger: number;
  energy: number;
  mood: number;
  money: number;
  inventory: Item[];
  location: string;
  alive: boolean;
}

// Places remain lightweight and reference paths for adjacency; events are generic records appended to the event log for audit, replay and snapshotting.
interface IPlace {
  id: string;
  name: string;
  type: 'restaurant' | 'market' | 'square' | 'factory' | string;
  description?: string;
  // place-specific static properties (e.g., prices, capacity)
  properties?: Record<string, any>;
}

interface IItem {
  id: string;
  name: string;
  type: 'consumable' | 'tool' | 'resource' | string;
  effects?: Record<string, number>;
}

interface IInventory {
  items: Record<string, number>; // itemId -> count
  addItem(itemId: string, qty?: number): void;
  removeItem(itemId: string, qty?: number): boolean;
}

interface INPCRelationship {
  npcId: string;
  otherNpcId: string;
  relation: 'friend' | 'neutral' | 'enemy' | string;
  intimacy: number; // -100..100
}

interface IPath {
  id: string;
  fromPlaceId: string;
  toPlaceId: string;
  cost?: number; // movement cost or time
  direction?: 'up' | 'down' | 'left' | 'right' | string; // logical direction on map
}

// Note: `path.ts` models edges between places so places don't need to store adjacency lists; path graph can be used for pathfinding and map partitions.

interface IEvent {
  id: string;
  timestamp: string; // ISO
  npcId?: string;
  type: string; // e.g., 'action', 'transaction', 'prompt_updated', 'daily-grant'
  payload: Record<string, any>;
  source?: 'llm' | 'local' | 'system';
}

interface ITown {
  id: string;
  name: string;
  description?: string;
  places: string[]; // list of place ids
  paths?: string[];  // list of path ids
  // optional metadata for map rendering or partitioning
  metadata?: Record<string, any>;
}
```

2. Simulation loop
- Scheduler maintains next-run timestamps per NPC. On tick, it calls SimulationService.generateDecision(npc) which uses LLM Adapter (or mock) to get a behavior description.
- Decision is translated to internal action functions which mutate NPC state atomically and append an event to the event log.

3. Event log and snapshot
- Append-only event log: stores events with {id, timestamp, npcId, action, source}
- Snapshot writer: after N events or every M seconds, write a JSON snapshot of in-memory state for debugging and quick recovery.

4. WebSocket contract
- `npc_created`, `npc_deleted`, `state_update` events. `state_update` includes: { timestamp, npc_id, delta_changes, new_state_snapshot, version }

---

## Development Setup

1. Install and run (development)

```bash
npm install
npm run dev    # hot-reload during development (ts-node-dev or similar)
# For a simple local run that resembles production behavior:
npm start
```

2. Environment
- Use `.env` or `config.yaml` to set: LLM adapter type, LLM API key (if used), simulation interval, snapshot path.

3. Local testing
- Provide scripts to seed N mock NPCs for load testing (e.g., `npm run seed -- --count=10`).

---

## Implementation Guide

Phase 1 (MVP core):
1. Implement TypeScript project skeleton and shared types.  
2. Implement REST endpoints: POST /npc, GET /npc, GET /npc/{id}, PATCH /npc/{id}/prompt, DELETE /npc/{id}.  
3. Implement WebSocket broadcaster and `state_update` contract.  
4. Implement Mock LLM Adapter and SimulationService to run loop for N NPCs.  
5. Implement event log append and simple snapshot writer.

Phase 2 (stability & ops):
1. Add LLM real adapter and configuration.  
2. Implement local-fallback strategies and detailed metrics (latency, success rate).  
3. Add basic persistence (SQLite) for durability and transactions.

---

## Testing Approach

- Unit tests for services and adapters (vitest).
  - `npx vitest run`  
- Integration tests for REST endpoints and WebSocket messages (supertest + ws client).  
- Small performance test: seed 10 NPCs and verify each `state_update` completes within expected time window.

---

## Deployment Strategy

- MVP / Production: single-node host-based deployment with `nginx` as reverse proxy. The Node.js backend runs as a persistent process (e.g., systemd or PM2) on the host. The frontend static assets (if any) should be built and served by `nginx` directly. Docker is explicitly not considered in this deployment plan.
- Use environment configuration for switching LLM adapters.
- For scaling/production improvements: move event log to a durable store (Postgres or message broker) and consider separating simulation workers or introducing job queues.

---

This tech-spec.md is intentionally concise to match Level 2 scope; run the 3‑solutioning workflow when you need per-epic tech-specs or architecture diagrams.
