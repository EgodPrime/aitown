# Solution Architecture — AI 小镇

**Author:** Egod
**Date:** 2025-10-08
**Project Level:** 2

## Executive Summary

This document describes a focused solution architecture for the AI 小镇 MVP. The primary goal is to deliver a single-node TypeScript implementation that supports 10 concurrent NPC simulations, clear separation of concerns, observable event-driven simulation, and an LLM Adapter with robust fallback.

Key outputs:
- Component diagram and responsibilities
- Technology decisions (concrete versions to be chosen during implementation)
- Data flow and event logging strategy
- Source tree and deployment plan

## Technology and Library Decisions

| Category | Technology | Version | Rationale |
|---|---:|---:|---|
| Language | Node.js + TypeScript | >=18 | Team familiarity; good for rapid MVP and type safety |
| HTTP framework | express | ^4.x | Lightweight, widely used |
| WebSocket | ws | ^8.x | Simple, low-footprint WebSocket server |
| Testing | vitest | ^1.x | Fast unit/integration testing for TypeScript |
| Persistence (optional) | SQLite | N/A | Lightweight local persistence for MVP if needed |

## Component Overview

- API Server (Express)
- WebSocket Broadcaster
- Simulation Service (Scheduler + Decision Engine)
- LLM Adapter (Mock + Real implementations)
- Event Log & Snapshot Writer
- Repos/Memory Layer (in-memory, optional SQLite)

## Data Architecture

- Primary entities: NPC, Place, Path, Item, Inventory, Event, Town
- Event-driven state updates: decisions → events → apply to in-memory state → write snapshot → broadcast state_update

## API and WebSocket Contracts

- REST endpoints: POST /npc, GET /npc, GET /npc/{id}, PATCH /npc/{id}/prompt, DELETE /npc/{id}, GET /places, GET /npc/{id}/memory, GET /npc/{id}/transactions
- WebSocket events: npc_created, npc_deleted, state_update

## Source Tree

See `docs/tech-spec.md` Proposed Source Tree section.

## Deployment

- Development: run directly with npm (e.g., `npm run dev` for hot-reload during development and `npm start` for a simple production-like run). Use PM2 only if process supervision is required in a dev/staging environment.
- Production: serve the backend Node.js process behind `nginx` as a reverse proxy. The frontend (QA UI) can be served as static files by `nginx` (built assets) and websocket/http proxied to the Node process. Docker is not considered in this deployment plan; we assume direct host-based deployment with `nginx` for the product environment.

---

## Next Steps

1. Review this architecture and approve or request changes.  
2. Run Cohesion Check (automated) and address any gaps.  
3. Generate per-epic tech-specs (generated below) and iterate.
