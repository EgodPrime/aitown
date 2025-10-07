```markdown
# 07 - LLM 适配器：用户故事

1. 适配器抽象
   - 作为开发者，我要一个可插拔的 LLM Adapter 接口，便于切换 mock/OpenAI/玩家私有 API。
   - 验收标准：代码库包含 adapter 接口定义与至少两个实现（mock 与 server-default）；配置能选择适配器。

2. 失败降级策略
   - 作为系统，我要在外部 LLM 调用失败或超时时降级到本地规则，以保持仿真节奏。
   - 验收标准：当适配器调用失败时，系统记录错误并返回降级行为（可预期的默认动作），并广播降级日志。

````markdown
```markdown
# 07 - LLM 适配器：用户故事

1. 适配器抽象
    - 作为开发者，我要一个可插拔的 LLM Adapter 接口，便于切换 mock/OpenAI/玩家私有 API。
    - 验收标准：代码库包含 adapter 接口定义与至少两个实现（mock 与 server-default）；配置能选择适配器。

2. 失败降级策略
    - 作为系统，我要在外部 LLM 调用失败或超时时降级到本地规则，以保持仿真节奏。
    - 验收标准：当适配器调用失败时，系统记录错误并返回降级行为（可预期的默认动作），并广播降级日志。

```

````

---

Implementation notes:

- A basic LLM adapter was added at `src/aitown/server/llm_adapter.py`.
- Default adapters provided: `MockLLMAdapter` and `ServerDefaultLLMAdapter`.
- Select adapter with environment variable `AITOWN_LLM_ADAPTER` ("mock" or "server-default").
- Simulate server failures with `AITOWN_LLM_SIMULATE_FAIL=1` and latency with `AITOWN_LLM_SIMULATE_LATENCY`.
- Calls should use `call_with_fallback(adapter, prompt)` to ensure graceful downgrade to local rules on errors.


---

QA Results

- Reviewed files:
    - `docs/stories/07-llm-adapter-stories.md` (this file)
    - `src/aitown/server/llm_adapter.py`
    - `src/aitown/server/services.py`
    - `tests/test_llm_adapter.py`

- Acceptance criteria mapping:
    1. Adapter abstraction + two implementations: IMPLEMENTED
         - `BaseLLMAdapter` protocol + `MockLLMAdapter` and `ServerDefaultLLMAdapter` exist.
    2. Configuration selectable: IMPLEMENTED
         - `get_adapter()` uses `AITOWN_LLM_ADAPTER` env var to pick adapter; tests exercise this.
    3. Failure downgrade to local rules + logging: IMPLEMENTED
         - `call_with_fallback()` logs exceptions and returns `local_rules_fallback()` on errors; services use this helper.

- Tests:
    - Ran `tests/test_llm_adapter.py` — all tests passed (4 tests).
    - Ran full test suite — all tests passed (26 tests).

- Observations / Recommendations:
    1. `ServerDefaultLLMAdapter` is a placeholder that simulates failures/latency for testing. Replace with a real async HTTP implementation (httpx) before production use.
    2. Consider per-NPC or per-player adapter selection so player-provided API configs can be used dynamically (currently services return an `api_preference` action when a player config exists; next step could be wiring the adapter to use player credentials).
    3. `call_with_fallback()` currently uses a synchronous time-based approach; for production an async/cancellable pattern with proper timeout handling is recommended.
    4. Expand local-rule fallback heuristics to handle more prompt patterns and map to richer action types.

Verdict: PASS — Story acceptance criteria are implemented, tests are present and passing, and the code integrates with services. Production hardening (real HTTP adapter, async timeouts, per-player wiring) remains as follow-ups.

