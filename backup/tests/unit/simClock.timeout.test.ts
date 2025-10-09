import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';

describe('simClock handler timeout', () => {
  let memoryRepo: any;
  let simClock: any;
  let npcService: any;

  beforeEach(async () => {
    process.env.SIM_DAY_DURATION_MS = '100';
    process.env.SIM_ENABLE_GUARANTEE_CREDIT = '1';
    // set handler timeout very small to force timeout
    process.env.SIM_DAY_END_HANDLER_TIMEOUT_MS = '10';
  vi.resetModules();
  // use real timers for this test because we will simulate async delay
  vi.useRealTimers();
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
    // ensure timers restored
    try { vi.useFakeTimers(); } catch (e) {}
    delete process.env.SIM_DAY_DURATION_MS;
    delete process.env.SIM_ENABLE_GUARANTEE_CREDIT;
    delete process.env.SIM_DAY_END_HANDLER_TIMEOUT_MS;
  });

  it('records day_end_failed when handler times out', async () => {
    // create one NPC
    const a = npcService.create('player1', { name: 'a', prompt: 'p' });

    // monkey-patch appendEvent to delay guarantee_credit_batch event asynchronously
    const originalAppend = memoryRepo.appendEvent.bind(memoryRepo);
    memoryRepo.appendEvent = (evt: any) => {
      if (evt && evt.event_type === 'guarantee_credit_batch') {
        return new Promise((resolve) => setTimeout(() => resolve(originalAppend(evt)), 50));
      }
      return originalAppend(evt);
    };

    simClock.start();

    // advance real time enough for the sim day to elapse
    await new Promise((r) => setTimeout(r, 150));

    const events = memoryRepo.getEvents();
    const failed = events.find((e: any) => e.event_type === 'day_end_failed');
    const batch = events.find((e: any) => e.event_type === 'guarantee_credit_batch');

    expect(failed).toBeTruthy();
    // batch may or may not be present depending on timing; ensure at least handler failure was recorded
    expect(failed.sim_day).toBeDefined();
  });
});
