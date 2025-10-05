```markdown
# 16 - Daily welfare distribution (idempotent)

1. Idempotent welfare job
   - 作为系统，我要在仿真日轮转时向所有存活 NPC 发放配置的基础保障金，并保证任务幂等，当任务并发运行时不会重复发放。
   - 验收标准：实现日轮转钩子或作业，记录发放批次 id；重复运行同一批次不会导致重复发放；`welfare_paid` 事件广播包含 batch_id 与受益者列表。
