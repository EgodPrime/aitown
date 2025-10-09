# Tech Spec — Epic D: API, Web UI, and Handoff

## Overview
Epic D provides developer-facing HTTP/WebSocket APIs, a minimal static Web UI for QA, and deployment notes.

## Stories Covered
- D-01: REST API for state queries (Express)
- D-02: WebSocket state_update channel
- D-03: Minimal QA UI to view NPCs and trigger events
- D-04: Deployment & host-based production config (nginx)

## Components
- `api/server` — Express routes for read-only queries and commands
- `ws/server` — WebSocket server for broadcasts
- `ui/qa` — small React or static HTML client for QA

## Implementation Notes
- Keep API stable and versioned (v1).
- WebSocket messages are JSON with type and payload.

## Testing
- Endpoint contract tests
- WebSocket integration tests

## Handoff Checklist
- API OpenAPI spec
- Minimal QA UI steps
- Production deploy notes: `nginx` reverse-proxy configuration and systemd/PM2 process supervision scripts. (Docker is not part of the recommended deployment plan.)
