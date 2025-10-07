import { INPC } from '../types';
import { memoryRepo } from '../repos/memoryRepo';
import { v4 as uuidv4 } from 'uuid';

export const npcService = {
  create(player_id: string, payload: Partial<INPC>) {
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
      alive: true
    };
    memoryRepo.save(npc);
    console.log(`NPC created: ${npc.id} for player: ${player_id}`);
    return npc;
  },
  get(id: string) {
    return memoryRepo.get(id);
  },
  list() {
    return memoryRepo.list();
  }
};
