# LLM Adapter — Ops Notes

This short doc explains runtime choices for the LLM adapter and how to manage secrets during development and production.

Environment
- `LLM_ADAPTER` — `mock` (default) or `openai` (real adapter)
- `OPENAI_API_KEY` — required only if `LLM_ADAPTER=openai`
- `SIM_INTERVAL` — simulation tick in seconds (default in `.env.example` = 90)

Development
- Use `.env.example` as a starting point. Developers should not commit real API keys to the repo. Use local environment variables or a secret manager.
- Default is `LLM_ADAPTER=mock` so tests and local work do not require network access.

Production
- Configure `LLM_ADAPTER=openai` and set `OPENAI_API_KEY` as a host-level secret (systemd environment, cloud provider secret store, or a deploy-time injection mechanism). Do not write API keys into git.
- Run the Node.js backend behind `nginx` as reverse proxy. Ensure `nginx` only allows necessary ports and restricts access.

Fallback strategy
- LLM calls should implement a timeout (recommended 5s). On timeout or error, use a deterministic local fallback behavior (e.g., a simple rule-based decision generator) and log the incident with latency/error.
