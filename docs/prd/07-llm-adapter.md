# 七、可配置 LLM 适配器

- 提供 mock 实现用于离线演示
- 提供 adapter 接口，便于接入 OpenAI 等
- Adapter 责任：请求构建、温控（temperature）、token 限制、失败重试与降级到本地规则
