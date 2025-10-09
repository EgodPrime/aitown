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
    return Promise.resolve(evt);
  },
  getEvents() {
    return this.events.slice();
  },
  clearEvents() {
    this.events.length = 0;
  }

  // processed keys for idempotency demo (in-memory)
  ,processedKeys: new Set<string>() as Set<string>
  ,
  tryAcquireKey(key: string) {
    if (this.processedKeys.has(key)) return false;
    this.processedKeys.add(key);
    return true;
  },
  hasProcessedKey(key: string) {
    return this.processedKeys.has(key);
  },
  markProcessedKey(key: string) {
    this.processedKeys.add(key);
  },
  releaseKey(key: string) {
    this.processedKeys.delete(key);
  },
  clearProcessedKeys() {
    this.processedKeys.clear();
  }
};
