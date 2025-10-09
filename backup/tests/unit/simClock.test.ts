import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';

describe('simClock', () => {
  let memoryRepo: any;
  let simClock: any;
  let npcService: any;

  beforeEach(async () => {
    // configure accelerated sim for tests
    process.env.SIM_DAY_DURATION_MS = '100';
    process.env.SIM_ENABLE_GUARANTEE_CREDIT = '1';
    vi.resetModules();
    vi.useFakeTimers();
    // dynamic import after setting env so module initialization reads the env
    const memMod = await import('../../src/repos/memoryRepo');
    const simMod = await import('../../src/services/simClock');
    const npcMod = await import('../../src/services/npcService');
    memoryRepo = memMod.memoryRepo;
    simClock = simMod.simClock;
    npcService = npcMod.npcService;
    memoryRepo.clear();
    memoryRepo.clearEvents();
  });

  afterEach(() => {
    try {
      simClock.stop();
    } catch (e) {}
    vi.useRealTimers();
    delete process.env.SIM_DAY_DURATION_MS;
    delete process.env.SIM_ENABLE_GUARANTEE_CREDIT;
  });

  it('emits day_end and creates guarantee credit transactions when enabled', async () => {
    // create two NPCs
    const a = npcService.create('player1', { name: 'a', prompt: 'p' });
    const b = npcService.create('player2', { name: 'b', prompt: 'q' });

    simClock.start();

    // advance time past one sim day
    vi.advanceTimersByTime(150);

    // allow pending microtasks
    await Promise.resolve();

    const events = memoryRepo.getEvents();
    const dayEnd = events.find((e: any) => e.event_type === 'day_end');
    const txBatch = events.find((e: any) => e.event_type === 'guarantee_credit_batch');

    expect(dayEnd).toBeTruthy();
    expect(dayEnd.sim_day).toBeGreaterThanOrEqual(0);
    expect(txBatch).toBeTruthy();
    expect(txBatch.transaction_count).toBe(2);

    // check NPCs have transactions appended
    const na = npcService.get(a.id);
    const nb = npcService.get(b.id);
    expect(Array.isArray(na.transactions)).toBe(true);
    expect(Array.isArray(nb.transactions)).toBe(true);
    expect(na.transactions.length).toBeGreaterThanOrEqual(1);
    expect(nb.transactions.length).toBeGreaterThanOrEqual(1);
  });
});
