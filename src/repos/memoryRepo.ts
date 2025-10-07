import { INPC } from '../types';

const store: Record<string, INPC> = {};

export const memoryRepo = {
  list(): INPC[] {
    return Object.values(store);
  },
  get(id: string): INPC | undefined {
    return store[id];
  },
  save(npc: INPC) {
    store[npc.id] = npc;
    return npc;
  },
  delete(id: string) {
    delete store[id];
  }
};
