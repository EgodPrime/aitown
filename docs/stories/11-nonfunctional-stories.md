```markdown
# 11 - 非功能与实施计划：故事化

1. 可用性与重连
   - 作为用户，我希望在断线重连后前端能重新拉取 `full_state` 并继续显示当前数据。
   - 验收标准：实现 `/state` 或 WebSocket 重连时的 full_state 拉取逻辑；手动断连/重连测试通过。
   - 前端参考实现：`docs/frontend/reconnect.md` 包含简单的 WebSocket + HTTP `/state` 回退示例（可复制粘贴）。

2. 性能与降级
   - 作为运维，我需要在单机上支持 50 个 NPC 并在 LLM 调用高延迟时降级，保证仿真节奏。
   - 验收标准：在模拟高延迟情况下，系统能触发降级策略并维持广播频率；性能阈值文档化。
   
## QA Results (appended by qa agent)

Summary:

- Story-11 covers reconnect behavior and nonfunctional performance/degradation. Implementation work includes adding `/state` HTTP fallback (done) and a recommended frontend reconnect pattern (documented in `docs/frontend/reconnect.md`). Overall, implementation is sound but needs explicit acceptance tests and a small set of operational checks.

Findings & Severity:

1. Reconnect fallback implemented but not documented in server API docs (Severity: Low)
   - `/state` endpoint added and returns `{type: 'full_state', payload: [...]}`. Add a short line in API docs (or OpenAPI) so frontend teams know the exact response shape.

2. Frontend snippet exists but needs integration guidance for ordering/deduping (Severity: Medium)
   - The reconnect snippet is framework-agnostic. Recommend adding notes on how to merge `full_state` with incremental `state_update` messages and how to ignore duplicates (sequence numbers or timestamp checks).

3. Performance & degradation tests are not yet automated (Severity: High)
   - Story requires proving the system can support 50 NPCs and degrade under LLM latency. Add load tests and a simulated-high-latency adapter to validate behaviour and record thresholds.

4. Monitoring/metrics suggestion missing (Severity: Medium)
   - Recommend adding basic metrics (current NPC count, average adapter latency, simulation loop ticks/sec) to detect when degradations are triggered and to tune thresholds.

Suggested Fixes / Recommendations:

- Document `/state` response in the API docs or OpenAPI schema: include `type` and `payload` fields and example payload (small sample of NPC object).
- Extend `docs/frontend/reconnect.md` with a short subsection describing deduping strategy:
  - Option A: server includes a monotonic `seq` or `tick` in `state_update` messages; client ignores older seq.
  - Option B: client applies simple timestamp checks per NPC to avoid older updates overwriting newer state.
- Implement a simulated adapter for tests (mock LLM) that can be configured with artificial latency and failure rates. Add a test harness that:
  1. Creates 50 NPCs (or parameterized N)
  2. Configures the adapter to respond slowly (e.g., 500ms, 1s, 2s per call)
  3. Runs the simulation loop for M steps and asserts that the system continues to produce `state_update` broadcasts at the expected frequency (or within documented tolerance)
  4. Verifies that fallback behavior (e.g., movement-only or deterministic mock_generate_action) is used when adapter latency exceeds threshold
- Add a small metrics endpoint (optional) or log lines that record adapter call latencies and tick durations; these make it easier to validate thresholds in automated runs.

Concrete acceptance tests (examples):

1) Reconnect full_state retrieval
   - Setup: Start server, create a few NPCs, connect a client over websocket and verify initial `full_state` received.
   - Action: Force-close the websocket, reconnect the websocket but drop the initial `full_state` message (simulate race/loss).
   - Expect: Client uses HTTP GET /state to fetch full state and reconciles UI to include all NPCs; no stale UI state remains.

2) Deduping/incremental ordering test
   - Setup: Server sends `state_update` messages with artificially reordered seq numbers.
   - Action: Client receives out-of-order updates.
   - Expect: With either seq-based dedupe or timestamp ordering, client ends with the latest state (not older out-of-order updates).

3) Performance degradation simulation
   - Setup: Create 50 NPCs in the in-memory store. Swap the llm_adapter with a test adapter that sleeps for X ms per call.
   - Action: Run N simulation steps (e.g., equal to TICKS_PER_DAY or a smaller number) with adapter latencies at increments (e.g., 100ms, 500ms, 1000ms, 2000ms).
   - Expect: For each latency level, assert whether the simulation loop continues to produce `state_update` broadcasts at acceptable frequency (document acceptable variance). When latency exceeds threshold, assert the system switches to fallback behavior and broadcast frequency remains within defined tolerances.

4) Smoke test for `/state` endpoint
   - Setup: Create some NPCs
   - Action: HTTP GET /state
   - Expect: 200 OK and JSON body with keys `type=='full_state'` and `payload` containing the NPC array.

Status & Next Steps:

- `/state` endpoint and frontend snippet implemented and committed.
- Recommended: Add at least one automated test from the above list (Smoke test for `/state` and a basic degradation simulation) to lock acceptance criteria.
- Recommended: Small docs update to include `/state` in API docs/OpenAPI and an added deduping subsection in `docs/frontend/reconnect.md`.

Please address the small documentation/API note and decide whether you want me to add the automated degradation tests (I can implement a mock adapter and test harness if you want). 


```
