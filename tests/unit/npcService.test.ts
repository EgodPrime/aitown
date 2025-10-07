import { describe, it, expect } from 'vitest';
import { npcService } from '../../src/services/npcService';

describe('npcService', () => {
  it('creates and retrieves npc', () => {
    const player_id = 'player:test1';
    const npc = npcService.create(player_id, { name: 'Test', prompt: 'test prompt' } as any);
    expect(npc).toHaveProperty('id');
    const loaded = npcService.get(npc.id);
    expect(loaded).toBeDefined();
    expect(loaded?.player_id).toBe(player_id);
  });

  it('prevents multiple active npcs per player', () => {
    const pid = 'player:dup';
    const a = npcService.create(pid, { name: 'A', prompt: 'p' } as any);
    expect(() => npcService.create(pid, { name: 'B', prompt: 'p' } as any)).toThrow();
  });
});
