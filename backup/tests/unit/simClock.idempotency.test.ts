import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';

describe('simClock idempotency', () => {
  let memoryRepo: any;
  let simClock: any;
  let npcService: any;

  beforeEach(async () => {
    process.env.SIM_DAY_DURATION_MS = '100';
    process.env.SIM_ENABLE_GUARANTEE_CREDIT = '1';
    vi.resetModules();
    vi.useFakeTimers();
  const memMod = await import('../../src/repos/memoryRepo');
  const simMod = await import('../../src/services/simClock');
  const npcMod = await import('../../src/services/npcService');
    memoryRepo = memMod.memoryRepo;
    simClock = simMod.simClock;
    npcService = npcMod.npcService;
    memoryRepo.clear();
    memoryRepo.clearEvents();
    memoryRepo.clearProcessedKeys();
  });

  afterEach(() => {
    try {
      simClock.stop();
    } catch (e) {}
    vi.useRealTimers();
    delete process.env.SIM_DAY_DURATION_MS;
    delete process.env.SIM_ENABLE_GUARANTEE_CREDIT;
  });

  it('skips duplicate day_end processing for same sim_day', async () => {
    // create one NPC
    const a = npcService.create('player1', { name: 'a', prompt: 'p' });

    simClock.start();

    // advance time to trigger first rollover
    vi.advanceTimersByTime(150);
    await Promise.resolve();

    // capture events after first rollover
    let events = memoryRepo.getEvents();
    const dayEnd = events.find((e: any) => e.event_type === 'day_end');
    const txBatch = events.find((e: any) => e.event_type === 'guarantee_credit_batch');
    expect(dayEnd).toBeTruthy();
    expect(txBatch).toBeTruthy();

    // check the recorded day_end event contains the idempotency key we used and that key is considered processed
    const recordedDayEnd = events.find((e: any) => e.event_type === 'day_end');
    expect(recordedDayEnd).toBeTruthy();
    const idKey = recordedDayEnd.idempotency_key;
    // tryAcquire should return false since already processed
    const acquired = memoryRepo.tryAcquireKey(idKey);
    expect(acquired).toBe(false);

    // ensure only one guarantee_credit_batch exists for that sim_day
    const batches = events.filter((e: any) => e.event_type === 'guarantee_credit_batch' && e.sim_day === recordedDayEnd.sim_day);
    expect(batches.length).toBe(1);
  });
});
