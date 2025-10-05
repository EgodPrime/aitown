```markdown
# 14 - Automated memory summarization

1. Nightly/rollover summarization
   - 作为系统，我要在仿真日轮转或夜间任务中自动压缩超过 7 天的 memory_log 为长期摘要条目，以缓解存储并模拟长期记忆。
   - 验收标准：实现定时任务（基于仿真日的 rollover）调用 summarizer；在 N 天后 `GET /npc/{id}/memory` 显示最近 7 天的逐日条目与 1 个或数个摘要条目；提供单元测试使用 mock adapter 验证摘要逻辑。
