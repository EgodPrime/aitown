# Architecture Decision Records (ADRs)

## ADR 001 — Language and Runtime

- Decision: Use Node.js (>=18) with TypeScript for MVP.
- Status: Accepted
- Rationale: Rapid iteration, existing repo tooling, team familiarity.

## ADR 002 — Simulation Model

- Decision: In-memory authoritative simulation with append-only event log and periodic JSON snapshots for recovery.
- Status: Accepted
- Rationale: Simplifies MVP implementation; allows deterministic replay for debugging.

## ADR 003 — LLM Adapter

- Decision: Implement a pluggable LLM Adapter interface with MockAdapter as default and OpenAIAdapter as optional.
- Status: Accepted
- Rationale: Supports offline development and robust fallback strategies.
