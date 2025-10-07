```markdown
# 10 - 验收标准（转化为可执行故事）

1. CRUD 自动化测试
   - 作为工程师，我要为 NPC 的 CRUD 编写自动化测试以验证基本行为。
   - 验收标准：单元/集成测试覆盖创建、冲突、更新（prompt）与删除；测试运行通过。

2. 时间与行为节奏验证
   - 作为 QA，我要验证仿真时间速率与行动频率（36 分钟 = 1 天；90s/行动）。
   - 验收标准：通过运行仿真并观察时间事件与广播，确认日结与保障金发放时序。

## QA Results (appended by qa agent)

Summary:

- This file contains two acceptance-story items focused on automated CRUD tests for NPCs and time/behavior rhythm validation. Both are clear at a high level but lack several testable details and explicit success metrics.

Findings & Severity:

1. Missing concrete test inputs and expected outputs (Severity: Medium)
   - The CRUD story does not define sample NPC payloads, data validation rules, or conflict scenarios. Tests need concrete examples to be deterministic.

2. Unclear test environment and fixtures (Severity: Medium)
   - No instructions about which persistence backend (in-memory, sqlite, test db) to use, or how to seed/teardown test data.

3. Time/behavior rhythm checks lack measurable assertions (Severity: High)
   - The story states "36 minutes = 1 day; 90s/action" but doesn't define which observable events should occur at those intervals, or acceptable timing tolerances for CI environments.

4. No negative / edge-case tests listed (Severity: Low)
   - E.g., creating NPC with invalid data, handling concurrent updates, boundary times near day rollover.

Suggested Fixes:

- CRUD tests: add at least 3 concrete example payloads (minimal valid NPC, NPC with optional fields, invalid NPC). Define expected HTTP status codes, response bodies or DB state after each action.
- Define test isolation: recommend using an ephemeral sqlite database or in-memory adapter with clear setup/teardown hooks. Document where to configure this in the test suite.
- Time/behavior: specify observable events to assert (e.g., "at simulated time T the system emits DAY_END event and updates NPC.account.balance by X"), include acceptable timing tolerance (e.g., ±5s in CI after time-scaling), and provide a deterministic time-advance helper for tests.
- Add negative tests for CRUD and timing edge cases (concurrent updates causing conflict, invalid payloads, day-boundary transitions).

Concrete Acceptance Tests to Add (examples):

1) CRUD Happy Path (unit/integration)
   - Setup: Fresh test DB, no NPCs
   - Action: POST /npcs {"name":"Test NPC","type":"villager","wealth":0}
   - Expect: 201 Created, response contains id and persisted fields
   - Action: GET /npcs/{id}
   - Expect: 200 OK, body equals created resource
   - Action: PATCH /npcs/{id} with updated prompt/fields
   - Expect: 200 OK, persisted changes visible
   - Action: DELETE /npcs/{id}
   - Expect: 204 No Content, subsequent GET returns 404

2) CRUD Conflict Handling
   - Setup: Create NPC
   - Action: Simulate two concurrent updates to prompt/content
   - Expect: Either last-write-wins documented behavior or a 409 Conflict with merge instructions; test should assert the agreed behavior

3) Time & Rhythm: Day End Broadcast
   - Setup: Use time-scaling helper to advance simulated time to just before day boundary
   - Action: Advance time by 36 scaled minutes to trigger day boundary
   - Expect: System emits DAY_END event, NPC payroll task runs, balances updated by configured stipend amount; assert event was emitted and balances changed as expected

4) Time Tolerance Test (CI-safe)
   - Setup: Time-scaling with deterministic clock
   - Action: Trigger actions scheduled every 90s (scaled)
   - Expect: Verify at least N actions occurred in expected order with tolerance ±5s (or scaled equivalent)

5) Negative Tests
   - Invalid NPC creation returns 400 with error message
   - Deleting non-existent NPC returns 404

### Concrete NPC payload examples (for CRUD tests)

Below are three concrete example payloads and the expected HTTP responses and DB state after each action. Use these directly in unit/integration tests.

A. Minimal valid NPC
- Payload (POST /npcs):

```json
{ "name": "Test NPC", "type": "villager" }
```

- Expected Response:
  - Status: 201 Created
  - Body: { "id": "<uuid>", "name": "Test NPC", "type": "villager", "created_at": "<iso>" }

- Expected DB state:
  - New row in `npcs` table with matching name/type fields, default values for optional fields (e.g., wealth=0, prompt=null)

B. NPC with optional fields (more complete)
- Payload (POST /npcs):

```json
{
  "name": "Merchant Mona",
  "type": "merchant",
  "wealth": 150,
  "prompt": "Sell rare items",
  "traits": ["shrewd","friendly"]
}
```

- Expected Response:
  - Status: 201 Created
  - Body: { "id": "<uuid>", "name": "Merchant Mona", "type": "merchant", "wealth": 150, "prompt": "Sell rare items", "traits": ["shrewd","friendly"], "created_at": "<iso>" }

- Expected DB state:
  - Row in `npcs` table contains the supplied optional fields; arrays serialized appropriately (e.g., JSON column) or linked via join table per schema

C. Invalid NPC payload (validation)
- Payload (POST /npcs):

```json
{ "name": "", "type": "unknown-type", "wealth": -10 }
```

- Expected Response:
  - Status: 400 Bad Request
  - Body: { "error": "validation_error", "fields": { "name": "required", "type": "unsupported", "wealth": "must be non-negative" } }

- Expected DB state:
  - No new row created; DB unchanged

Notes for test implementation:
- Use stable UUID / deterministic id assertions where possible (e.g., assert presence and format rather than exact value).
- Where timestamps are present, assert approximate ISO format or mock clock to deterministic values.
- For array or JSON fields, assert content equality regardless of ordering where ordering is not significant.
- Add tests for update (PATCH) and delete flows using the created id from the POST response.

Notes for Test Authors:

- Link these acceptance tests to concrete test files (e.g., tests/test_npc_crud.py, tests/test_time_rhythm.py). Use descriptive test names matching the acceptance criteria.
- If simulation relies on asynchronous background tasks or a scheduler, provide guidance to mock or control the scheduler so tests are deterministic.
- Where external integrations exist (websockets, message buses), prefer test doubles or local in-process adapters during CI runs.

Status: This QA review is appended-only as required. Please address the Suggested Fixes and update this file or the referenced test files. Once changes are made, re-run the relevant tests and re-submit for QA verification.
```
