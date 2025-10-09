import { EventEmitter } from 'events';
import { memoryRepo } from '../repos/memoryRepo';
import { SIM_CONFIG } from '../config';
import { v4 as uuidv4 } from 'uuid';

type TimeProvider = () => number;

class SimClock extends EventEmitter {
  private simStartRealtimeMs: number;
  private simStartSimMs: number;
  private simDayDurationMs: number;
  private simDay: number;
  private timer: NodeJS.Timeout | null = null;
  private timeProvider: TimeProvider;

  constructor(opts: { simDayDurationMs?: number; timeProvider?: TimeProvider } = {}) {
    super();
    this.timeProvider = opts.timeProvider || (() => Date.now());
    this.simDayDurationMs = opts.simDayDurationMs || SIM_CONFIG.simDayDurationMs;
    // initialize sim start anchored to now
    this.simStartRealtimeMs = this.timeProvider();
    this.simStartSimMs = 0;
    this.simDay = 0;
  }

  start() {
    if (this.timer) return;
    // schedule next rollover based on simDayDurationMs
    this.scheduleTick();
  }

  stop() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  private scheduleTick() {
    const now = this.timeProvider();
    const elapsedSimMs = this.realtimeToSimMs(now - this.simStartRealtimeMs);
    const currentSimDayFraction = elapsedSimMs % this.simDayDurationMs;
    const msUntilNext = this.simDayDurationMs - currentSimDayFraction;
    this.timer = setTimeout(() => this.handleRollover(), Math.max(1, msUntilNext));
  }

  private realtimeToSimMs(realtimeDeltaMs: number) {
    // 1 realtime ms == 1 sim ms in this simple linear mapping
    return realtimeDeltaMs;
  }

  now() {
    const now = this.timeProvider();
    const elapsedSimMs = this.realtimeToSimMs(now - this.simStartRealtimeMs) + this.simStartSimMs;
    const simDay = Math.floor(elapsedSimMs / this.simDayDurationMs);
    const simDayFraction = (elapsedSimMs % this.simDayDurationMs) / this.simDayDurationMs;
    return {
      sim_time_ms: elapsedSimMs,
      sim_day: simDay,
      sim_day_fraction: simDayFraction,
      sim_time_iso: new Date(this.simStartRealtimeMs + elapsedSimMs).toISOString(),
      realtime_timestamp: new Date(now).toISOString()
    };
  }

  private async handleRollover() {
    // compute sim day at rollover
    const state = this.now();
    const eventId = uuidv4();
    const idempotencyKey = `${state.sim_day}:day_end`;

    // prepare affected npc summary
    const allNpcs = memoryRepo.findAll({}).items;
    const sample = allNpcs.slice(0, 5).map(n => n.id);
    const affected = { count: allNpcs.length, sample };

    const event = {
      event_id: eventId,
      idempotency_key: idempotencyKey,
      timestamp: new Date().toISOString(),
      event_type: 'day_end',
      source: 'sim-clock',
      sim_day: state.sim_day,
      affected
    };

    // append event to repo immediately
    memoryRepo.appendEvent(event);
    // idempotency: try to acquire processed key; if already processed, record duplicate and skip handler
    const acquired = memoryRepo.tryAcquireKey(idempotencyKey);
    if (!acquired) {
      const dup = {
        event_id: uuidv4(),
        timestamp: new Date().toISOString(),
        event_type: 'day_end_duplicate',
        source: 'sim-clock',
        sim_day: state.sim_day,
        idempotency_key: idempotencyKey
      };
      memoryRepo.appendEvent(dup);
      return this.scheduleTick();
    }
    this.emit('day_end', event);

    // handle guarantee credit if enabled (with timeout and failure handling)
    if (SIM_CONFIG.enable_guarantee_credit) {
      const handler = async () => {
        // create simple transactions for each NPC (demo: credit 100)
        const txs: any[] = [];
        const createdAt = new Date().toISOString();
        for (const npc of allNpcs) {
          const tx = {
            transaction_id: uuidv4(),
            npc_id: npc.id,
            amount: 100,
            type: 'guarantee_credit',
            timestamp: createdAt,
            source_event_id: eventId,
            correlation_id: `${state.sim_day}-day_end`
          } as any;
          // append to npc.transactions if exists
          if (!Array.isArray(npc.transactions)) npc.transactions = [];
          npc.transactions.push(tx as any);
          txs.push(tx);
        }
        // write a transaction event
        const txEvent = {
          event_id: uuidv4(),
          timestamp: new Date().toISOString(),
          event_type: 'guarantee_credit_batch',
          source: 'sim-clock',
          sim_day: state.sim_day,
          transaction_count: txs.length
        };
  await memoryRepo.appendEvent(txEvent);
        return txs;
      };

      const timeoutMs = SIM_CONFIG.dayEndHandlerTimeoutMs || 1000;
      const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('handler_timeout')), timeoutMs));

      try {
        await Promise.race([handler(), timeoutPromise]);
      } catch (err: any) {
        // on error or timeout, record failure event and release idempotency key for retry
        const failEvent = {
          event_id: uuidv4(),
          timestamp: new Date().toISOString(),
          event_type: 'day_end_failed',
          source: 'sim-clock',
          error: err && err.message,
          sim_day: state.sim_day
        };
        memoryRepo.appendEvent(failEvent);
        // release processed key so retry can happen
        memoryRepo.releaseKey(idempotencyKey);
      }
    } else {
      // record noop/disabled event for audit
      const noop = {
        event_id: uuidv4(),
        timestamp: new Date().toISOString(),
        event_type: 'guarantee_credit_disabled',
        source: 'sim-clock',
        sim_day: state.sim_day
      };
      memoryRepo.appendEvent(noop);
    }

    // advance internal sim day counter
    this.simDay = state.sim_day + 1;

    // schedule next tick
    this.scheduleTick();
  }
}

export const simClock = new SimClock();

// start automatically in production when module is loaded
if (require.main === module) {
  simClock.start();
}

export default simClock;
