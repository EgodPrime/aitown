import { describe, it, expect } from 'vitest';
import { mockGenerateAction } from '../__mocks__/mockLLMAdapter';

describe('smoke: mock llm adapter', () => {
  it('returns a deterministic action object', async () => {
    const npc = { id: 'npc:test', name: 'Test NPC' };
    const action = await mockGenerateAction(npc);
    expect(action).toHaveProperty('type');
    expect(action).toHaveProperty('description');
    expect(action).toHaveProperty('changes');
    expect(action.type).toBe('noop');
  });
});
