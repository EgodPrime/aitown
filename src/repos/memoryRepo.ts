import { INPC } from '../types';

const store: Record<string, INPC> = {};

export const memoryRepo = {
  list(): INPC[] {
    return Object.values(store);
  },
  findAll(options: { limit?: number; offset?: number; filter?: (npc: INPC) => boolean } = {}): { items: INPC[]; total: number } {
    let items = Object.values(store);
    if (options.filter) {
      items = items.filter(options.filter);
    }
    const total = items.length;
    if (options.offset) {
      items = items.slice(options.offset);
    }
    if (options.limit) {
      items = items.slice(0, options.limit);
    }
    return { items, total };
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
  },
  clear() {
    Object.keys(store).forEach(key => delete store[key]);
  }
  ,
  // simple event log for auditing actions like prompt updates
  events: [] as any[],
  appendEvent(evt: any) {
    this.events.push(evt);
    return evt;
  },
  getEvents() {
    return this.events.slice();
  },
  clearEvents() {
    this.events.length = 0;
  }
};
