```markdown
# 15 - LLM telemetry, retries and deterministic mock

1. Telemetry and retry policy
   - 作为运维，我需要适配器暴露基本的指标（success_count, failure_count, timeout_count）并有可配置的重试策略。
   - 验收标准：适配器实现接口支持 retries=N, timeout_ms=M; 当超过阈值时触发本地降级逻辑并广播 a `llm_degraded` event；指标通过 simple counters 可被导出。

2. Deterministic mock for tests
   - 作为工程师，我需要 mock adapter 能返回可预测/可注入的行为以便编写稳定单元测试。
   - 验收标准：mock adapter 支持 setting seed 或 predefined responses；单元测试使用 mock adapter 验证 summarization、decision-making 执行路径。
