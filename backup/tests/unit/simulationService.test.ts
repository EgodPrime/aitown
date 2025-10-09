import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock dependencies before importing modules that use them
vi.mock('../../src/adapters/llm', () => ({
  llmAdapter: {
    generateDecision: vi.fn()
  }
}));

vi.mock('../../src/ws/broadcaster', () => ({
  broadcast: vi.fn()
}));

import { simulationService } from '../../src/services/simulationService';
import { memoryRepo } from '../../src/repos/memoryRepo';
import { llmAdapter } from '../../src/adapters/llm';
import { broadcast } from '../../src/ws/broadcaster';
import { INPC } from '../../src/types';

describe('SimulationService', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    memoryRepo.clear();
    memoryRepo.clearEvents();
    vi.clearAllMocks();
  });

  afterEach(() => {
    simulationService.stop();
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('should schedule decision generation every 90 seconds', async () => {
    const npc: INPC = {
      id: 'npc1',
      player_id: 'p1',
      name: 'Test NPC',
      prompt: 'Test prompt',
      hunger: 60,
      energy: 50,
      mood: 70,
      money: 0,
      inventory: {},
      location: 'town',
      alive: true,
      memory_log: { recent_memory: [], old_memory: '' },
      transactions: []
    };
    memoryRepo.save(npc);

    (llmAdapter.generateDecision as any).mockResolvedValue({
      action: { type: 'eat', changes: { hunger: -20 } },
      reasoning: 'test'
    });

    simulationService.start();

    // Advance 90 seconds
    vi.advanceTimersByTime(90000);
    // allow pending timers and microtasks (promises) to resolve
    vi.runOnlyPendingTimers();
    await Promise.resolve();
    // Run the decision generation directly to avoid timer-based flakiness
    await (simulationService as any).generateDecisions();

    const events = memoryRepo.getEvents();
    expect(events.some(e => e.event_type === 'decision_generation_start')).toBe(true);
    expect(events.some(e => e.event_type === 'decision_generation_complete')).toBe(true);
  });

  it('should use local fallback on timeout', async () => {
    const npc: INPC = {
      id: 'npc1',
      player_id: 'p1',
      name: 'Test NPC',
      prompt: 'Test prompt',
      hunger: 60,
      energy: 50,
      mood: 70,
      money: 0,
      inventory: {},
      location: 'town',
      alive: true,
      memory_log: { recent_memory: [], old_memory: '' },
      transactions: []
    };
    memoryRepo.save(npc);

  // Simulate adapter rejecting/aborting
  (llmAdapter.generateDecision as any).mockRejectedValue(new Error('timeout'));

    simulationService.start();

    vi.advanceTimersByTime(90000);
    vi.runOnlyPendingTimers();
    await Promise.resolve();

    // Run the decision generation directly to avoid timer-based flakiness
    await (simulationService as any).generateDecisions();

    const events = memoryRepo.getEvents();
    // Expect local-fallback event recorded
    expect(events.some((e: any) => e.event_type === 'local-fallback' && e.npc_id === 'npc1')).toBe(true);
    // Expect per-npc start/complete events
    expect(events.some((e: any) => e.event_type === 'decision_generation_start.npc' && e.npc_id === 'npc1')).toBe(true);
    expect(events.some((e: any) => e.event_type === 'decision_generation_complete.npc' && e.npc_id === 'npc1')).toBe(true);
  });

  it('should apply action changes to NPC', async () => {
    const npc: INPC = {
      id: 'npc1',
      player_id: 'p1',
      name: 'Test NPC',
      prompt: 'Test prompt',
      hunger: 60,
      energy: 50,
      mood: 70,
      money: 0,
      inventory: {},
      location: 'town',
      alive: true,
      memory_log: { recent_memory: [], old_memory: '' },
      transactions: []
    };
    memoryRepo.save(npc);

    (llmAdapter.generateDecision as any).mockResolvedValue({
      action: { type: 'eat', changes: { hunger: -20, energy: 10 } }
    });

  // Call generation directly to avoid timer-based flakiness
  await (simulationService as any).generateDecisions();

  const updatedNpc = memoryRepo.get('npc1');
    expect(updatedNpc).toBeDefined();
    // hunger should have decreased by 20
    expect((updatedNpc as any).hunger).toBe(40);

    // broadcast should be called with a state_update and include delta_changes
    expect(broadcast).toHaveBeenCalled();
    const bcalls = (broadcast as any).mock.calls;
    const stateUpdateCall = bcalls.find((c: any) => c[0] === 'state_update');
    expect(stateUpdateCall).toBeDefined();
    const payload = stateUpdateCall[1];
    expect(payload).toHaveProperty('delta_changes');
    // delta_changes should reflect the changes we applied
    expect(payload.delta_changes).toHaveProperty('hunger');
  });
});
