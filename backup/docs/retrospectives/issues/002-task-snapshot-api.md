title: "ISSUE DRAFT: Implement memoryRepo snapshot/write API"
assignees: ["Amelia"]
labels: ["prep", "repo", "high"]

## Summary
Add `memoryRepo.writeSnapshot(npc_id)` API that returns `{ version, timestamp }` and protects concurrent writes.

## Details
- Deliverables: API implementation, unit & integration tests, concurrency protection
- Acceptance: Integration test shows snapshot written within 5s after event

## Estimate
2-3 days
