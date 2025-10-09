import { memoryRepo } from '../repos/memoryRepo';
import { llmAdapter } from '../adapters/llm';
import { broadcast } from '../ws/broadcaster';
import { SIM_CONFIG, LLM_CONFIG } from '../config';
import { INPC, IDecision, IAction } from '../types';
import { v4 as uuidv4 } from 'uuid';

class SimulationService {
  private intervalId: NodeJS.Timeout | null = null;

  start() {
    if (this.intervalId) return;
    this.intervalId = setInterval(() => this.generateDecisions(), SIM_CONFIG.decisionIntervalMs);
  }

  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private async generateDecisions() {
    // Top-level guard so unexpected errors are recorded and do not prevent future runs
    try {
      const activeNpcs = memoryRepo.findAll({ filter: (npc: INPC) => npc.alive }).items;
      if (activeNpcs.length === 0) return;

      const timestamp = new Date().toISOString();
      const eventId = uuidv4();

      // Record start
      const startEvent = {
        event_id: eventId,
        timestamp,
        event_type: 'decision_generation_start',
        npc_count: activeNpcs.length,
        source: 'simulation-service'
      };
      memoryRepo.appendEvent(startEvent);

      const decisions: { npcId: string; decision: IDecision; startTime: number; endTime?: number }[] = [];

      for (const npc of activeNpcs) {
        const startTime = Date.now();

        // Emit per-npc start event for finer-grained auditing
        const perNpcStart = {
          event_id: uuidv4(),
          timestamp: new Date().toISOString(),
          event_type: 'decision_generation_start.npc',
          npc_id: npc.id,
          source: 'simulation-service'
        };
        memoryRepo.appendEvent(perNpcStart);

        // Use AbortController to cancel underlying adapter work on timeout
        const controller = new AbortController();
        const timeout = setTimeout(() => {
          controller.abort();
        }, LLM_CONFIG.llmTimeoutMs);

        try {
          const decision = await llmAdapter.generateDecision(npc, { signal: controller.signal });
          clearTimeout(timeout);
          const endTime = Date.now();
          decisions.push({ npcId: npc.id, decision, startTime, endTime });

          // Emit per-npc complete event
          const perNpcComplete = {
            event_id: uuidv4(),
            timestamp: new Date().toISOString(),
            event_type: 'decision_generation_complete.npc',
            npc_id: npc.id,
            duration_ms: endTime - startTime,
            source: 'simulation-service'
          };
          memoryRepo.appendEvent(perNpcComplete);
        } catch (err) {
          clearTimeout(timeout);
          // Fallback
          const fallbackDecision: IDecision = {
            action: { type: 'noop', description: 'Fallback action due to timeout or error' },
            reasoning: 'local-fallback'
          };
          const endTime = Date.now();
          decisions.push({ npcId: npc.id, decision: fallbackDecision, startTime, endTime });

          // Log fallback event
          const fallbackEvent = {
            event_id: uuidv4(),
            timestamp: new Date().toISOString(),
            event_type: 'local-fallback',
            npc_id: npc.id,
            error: err instanceof Error ? err.message : 'unknown'
          };
          memoryRepo.appendEvent(fallbackEvent);

          // Emit per-npc complete event with fallback marker
          const perNpcComplete = {
            event_id: uuidv4(),
            timestamp: new Date().toISOString(),
            event_type: 'decision_generation_complete.npc',
            npc_id: npc.id,
            duration_ms: endTime - startTime,
            fallback: true,
            source: 'simulation-service'
          };
          memoryRepo.appendEvent(perNpcComplete);
        }
      }

      // Apply decisions
      for (const { npcId, decision } of decisions) {
        const npc = memoryRepo.get(npcId);
        if (!npc) continue;

        this.applyAction(npc, decision.action);

        // Add to memory_log
        const memoryEntry = {
          timestamp,
          content: `Decision: ${decision.action.description || decision.action.type}`
        };
        if (!npc.memory_log.recent_memory) npc.memory_log.recent_memory = [];
        npc.memory_log.recent_memory.push(memoryEntry);
        // Keep recent 7 days, but simple: limit to 100 entries
        if (npc.memory_log.recent_memory.length > 100) {
          npc.memory_log.recent_memory.shift();
        }

        memoryRepo.save(npc);

        // Broadcast state_update
        const delta = decision.action.changes || {};
        const newState = { ...npc };
        const version = Date.now(); // simple version
        broadcast('state_update', {
          timestamp,
          npc_id: npcId,
          delta_changes: delta,
          new_state_snapshot: newState,
          version
        });
      }

      // Record completion
      const completionEvent = {
        event_id: uuidv4(),
        timestamp: new Date().toISOString(),
        event_type: 'decision_generation_complete',
        decisions_count: decisions.length,
        source: 'simulation-service'
      };
      memoryRepo.appendEvent(completionEvent);
    } catch (err) {
      const failureEvent = {
        event_id: uuidv4(),
        timestamp: new Date().toISOString(),
        event_type: 'decision_generation_failed',
        error: err instanceof Error ? err.message : String(err),
        source: 'simulation-service'
      };
      memoryRepo.appendEvent(failureEvent);
    }
  }

  private applyAction(npc: INPC, action: IAction) {
    if (!action.changes) return;
    for (const [key, value] of Object.entries(action.changes)) {
      if (typeof value === 'number' && typeof (npc as any)[key] === 'number') {
        (npc as any)[key] += value;
        // Clamp to 0-100 for stats
        if (['hunger', 'energy', 'mood'].includes(key)) {
          (npc as any)[key] = Math.max(0, Math.min(100, (npc as any)[key]));
        }
      }
    }
  }
}

export const simulationService = new SimulationService();
