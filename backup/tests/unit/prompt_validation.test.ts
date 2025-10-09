import { describe, it, expect, beforeEach } from 'vitest';
import { npcService } from '../../src/services/npcService';
import { PROMPT_MAX_LENGTH } from '../../src/config';
import { memoryRepo } from '../../src/repos/memoryRepo';

describe('prompt validation', () => {
  beforeEach(() => {
    memoryRepo.clear();
  });

  it('create should fail for prompt > 5000 chars', () => {
  const long = 'a'.repeat(PROMPT_MAX_LENGTH + 1);
    expect(() => npcService.create('p', { name: 'X', prompt: long } as any)).toThrow();
  });

  it('updatePrompt should fail for prompt > 5000 chars', () => {
    const npc = npcService.create('owner', { name: 'O', prompt: 'ok' } as any);
  const long = 'b'.repeat(PROMPT_MAX_LENGTH + 1);
    expect(() => npcService.updatePrompt('owner', npc.id, long)).toThrow();
  });
});
