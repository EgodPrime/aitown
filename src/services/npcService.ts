import { INPC } from '../types';
import { memoryRepo } from '../repos/memoryRepo';
import { v4 as uuidv4 } from 'uuid';
import { PROMPT_MAX_LENGTH } from '../config';

export const npcService = {
  create(player_id: string, payload: Partial<INPC>) {
    // Defensive prompt length check
  if (payload.prompt && payload.prompt.length > PROMPT_MAX_LENGTH) throw new Error('PROMPT_TOO_LONG');
    // enforce one NPC per player (simple check)
    const existing = memoryRepo.list().find(n => n.player_id === player_id && n.alive);
    if (existing) throw new Error('PLAYER_HAS_ACTIVE_NPC');

    const npc: INPC = {
      id: uuidv4(),
      player_id,
      name: payload.name || 'npc',
      prompt: payload.prompt || '',
      hunger: 100,
      energy: 100,
      mood: 100,
      money: 0,
      inventory: {},
      location: 'start',
      alive: true,
      memory_log: { recent_memory: [], old_memory: '' },
      transactions: []
    };
    memoryRepo.save(npc);
    console.log(`NPC created: ${npc.id} for player: ${player_id}`);
    return npc;
  },
  get(id: string) {
    return memoryRepo.get(id);
  },
  list(options: { limit?: number; offset?: number } = {}) {
    return memoryRepo.findAll({
      ...options,
      filter: (npc: INPC) => npc.alive
    });
  }
  ,
  updatePrompt(player_id: string, id: string, newPrompt: string) {
    const npc = memoryRepo.get(id);
    if (!npc) throw new Error('NOT_FOUND');
    if (npc.player_id !== player_id) throw new Error('FORBIDDEN');

  if (newPrompt.length > PROMPT_MAX_LENGTH) throw new Error('PROMPT_TOO_LONG');

    const oldPrompt = npc.prompt;
    npc.prompt = newPrompt;
    memoryRepo.save(npc);

    // record event
    const event = {
      type: 'prompt_updated',
      actor: player_id,
      npc_id: id,
      timestamp: new Date().toISOString(),
      diff: {
        from: oldPrompt,
        to: newPrompt
      }
    };
    memoryRepo.appendEvent(event);
    return npc;
  }
  ,
  delete(player_id: string, id: string) {
    const npc = memoryRepo.get(id);
    if (!npc) throw new Error('NOT_FOUND');
    // simple admin check: allow if player_id matches owner or if player_id === 'admin'
    if (npc.player_id !== player_id && player_id !== 'admin') throw new Error('FORBIDDEN');

    // record deletion event
    const timestamp = new Date().toISOString();
    const event = {
      type: 'npc_deleted',
      actor: player_id,
      npc_id: id,
      npc_name: npc.name,
      timestamp
    };
    memoryRepo.appendEvent(event);

    // remove from active store
    memoryRepo.delete(id);

    return { id, deleted_at: timestamp, name: npc.name };
  }
};
