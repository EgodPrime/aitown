import { INPC, IDecision } from '../types';

export interface LLMAdapter {
  // Accept an optional options bag which may include an AbortSignal to cancel long-running requests
  generateDecision(npc: INPC, options?: { signal?: AbortSignal }): Promise<IDecision>;
}

export class MockLLMAdapter implements LLMAdapter {
  async generateDecision(npc: INPC, options?: { signal?: AbortSignal }): Promise<IDecision> {
    // Respect abort signal when provided
    if (options?.signal?.aborted) {
      const err: any = new Error('aborted');
      err.name = 'AbortError';
      throw err;
    }

    // Simple mock: if hunger > 50, eat; else rest
    const action = npc.hunger > 50 ?
      { type: 'eat', description: 'Eat to reduce hunger', changes: { hunger: -20 } } :
      { type: 'rest', description: 'Rest to recover energy', changes: { energy: 10 } };

    // Simulate async work and allow aborting during delay
    return await new Promise<IDecision>((resolve, reject) => {
      const timer = setTimeout(() => {
        resolve({ action, reasoning: 'Mock decision based on hunger' });
      }, 10);

      const onAbort = () => {
        clearTimeout(timer);
        const err: any = new Error('aborted');
        err.name = 'AbortError';
        reject(err);
      };

      options?.signal?.addEventListener?.('abort', onAbort, { once: true });
    });
  }
}

// Default instance
export const llmAdapter: LLMAdapter = new MockLLMAdapter();
