import { describe, it, expect, beforeEach } from 'vitest';
import { npcService } from '../../src/services/npcService';
import { memoryRepo } from '../../src/repos/memoryRepo';

describe('npcService', () => {
  beforeEach(() => {
    memoryRepo.clear();
  });

  it('creates and retrieves npc', () => {
    const player_id = 'player:test1';
    const npc = npcService.create(player_id, { name: 'Test', prompt: 'test prompt' } as any);
    expect(npc).toHaveProperty('id');
    const loaded = npcService.get(npc.id);
    expect(loaded).toBeDefined();
    expect(loaded?.player_id).toBe(player_id);
    expect(loaded).toHaveProperty('memory_log');
    expect(loaded?.memory_log).toEqual({ recent_memory: [], old_memory: '' });
    expect(loaded).toHaveProperty('transactions');
    expect(loaded?.transactions).toEqual([]);
  });

  it('prevents multiple active npcs per player', () => {
    const pid = 'player:dup';
    const a = npcService.create(pid, { name: 'A', prompt: 'p' } as any);
    expect(() => npcService.create(pid, { name: 'B', prompt: 'p' } as any)).toThrow();
  });

  it('lists active npcs with pagination', () => {
    // Create some npcs
    const npc1 = npcService.create('p1', { name: 'N1', prompt: 'p' } as any);
    const npc2 = npcService.create('p2', { name: 'N2', prompt: 'p' } as any);
    const npc3 = npcService.create('p3', { name: 'N3', prompt: 'p' } as any);

    // List all
    const result = npcService.list();
    expect(result.items).toHaveLength(3);
    expect(result.total).toBe(3);

    // List with limit
    const limited = npcService.list({ limit: 2 });
    expect(limited.items).toHaveLength(2);
    expect(limited.total).toBe(3);

    // List with offset
    const offset = npcService.list({ offset: 1, limit: 2 });
    expect(offset.items).toHaveLength(2);
    expect(offset.total).toBe(3);
  });

  it('returns empty list when no active npcs', () => {
    const result = npcService.list();
    expect(result.items).toEqual([]);
    expect(result.total).toBe(0);
  });

  it('updates prompt for owner and records event', () => {
    const player_id = 'player:upd';
    const npc = npcService.create(player_id, { name: 'U', prompt: 'old' } as any);
    const updated = npcService.updatePrompt(player_id, npc.id, 'new');
    expect(updated.prompt).toBe('new');
    const events = memoryRepo.getEvents();
    expect(events.length).toBeGreaterThan(0);
    const ev = events[events.length - 1];
    expect(ev.type).toBe('prompt_updated');
    expect(ev.actor).toBe(player_id);
    expect(ev.npc_id).toBe(npc.id);
    expect(ev.diff).toEqual({ from: 'old', to: 'new' });
  });

  it('prevents non-owner from updating prompt', () => {
    const owner = 'player:owner';
    const other = 'player:other';
    const npc = npcService.create(owner, { name: 'O', prompt: 'o' } as any);
    expect(() => npcService.updatePrompt(other, npc.id, 'x')).toThrow();
  });
});
