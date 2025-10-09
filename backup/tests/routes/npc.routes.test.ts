import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import createApp from '../../src/app';
import { memoryRepo } from '../../src/repos/memoryRepo';
import { PROMPT_MAX_LENGTH } from '../../src/config';
import { broadcast } from '../../src/ws/broadcaster';

vi.mock('../../src/ws/broadcaster', () => ({
  broadcast: vi.fn()
}));

describe('NPC routes', () => {
  beforeEach(() => {
    memoryRepo.clear();
    vi.clearAllMocks();
  });
  it('POST /api/npc creates npc with valid response', async () => {
    const app = createApp();
    const res = await request(app)
      .post('/api/npc')
      .set('x-player-id', 'p1')
      .send({ name: 'RTest', prompt: 'test prompt' });
    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body).toHaveProperty('player_id', 'p1');
    expect(res.body).toHaveProperty('name', 'RTest');
    expect(res.body).toHaveProperty('prompt', 'test prompt');
    expect(res.body).toHaveProperty('initial_stats');
    expect(res.body.initial_stats).toHaveProperty('hunger', 100);
    expect(broadcast).toHaveBeenCalledWith('npc_created', { id: res.body.id });
  });

  it('POST /api/npc returns 409 on conflict', async () => {
    const app = createApp();
  await request(app).post('/api/npc').set('x-player-id', 'p2').send({ name: 'A', prompt: 'p' });
  const res = await request(app).post('/api/npc').set('x-player-id', 'p2').send({ name: 'B', prompt: 'p' });
    expect(res.status).toBe(409);
    expect(res.body.error).toBe('Player already has active NPC');
  });

  it('POST /api/npc validates input', async () => {
    const app = createApp();
    const res = await request(app).post('/api/npc').set('x-player-id', 'p3').send({});
    expect(res.status).toBe(400);

    // too long prompt
  const long = 'x'.repeat(PROMPT_MAX_LENGTH + 1);
    const res2 = await request(app).post('/api/npc').set('x-player-id', 'p3').send({ name: 'Too', prompt: long });
    expect(res2.status).toBe(400);
  });

  it('GET /api/npc returns list with pagination', async () => {
    const app = createApp();
  await request(app).post('/api/npc').set('x-player-id', 'p4').send({ name: 'ListTest', prompt: 'p' });
    const res = await request(app).get('/api/npc');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('npcs');
    expect(res.body).toHaveProperty('pagination');
    expect(Array.isArray(res.body.npcs)).toBe(true);
    expect(res.body.pagination).toHaveProperty('total');
    expect(res.body.pagination).toHaveProperty('limit', 10);
    expect(res.body.pagination).toHaveProperty('offset', 0);
  });

  it('GET /api/npc handles pagination params', async () => {
    const app = createApp();
  await request(app).post('/api/npc').set('x-player-id', 'p6').send({ name: 'Pag1', prompt: 'p' });
  await request(app).post('/api/npc').set('x-player-id', 'p7').send({ name: 'Pag2', prompt: 'p' });
    const res = await request(app).get('/api/npc?limit=1&offset=1');
    expect(res.status).toBe(200);
    expect(res.body.npcs).toHaveLength(1);
    expect(res.body.pagination.total).toBe(2);
    expect(res.body.pagination.limit).toBe(1);
    expect(res.body.pagination.offset).toBe(1);
  });

  it('GET /api/npc returns empty when no npcs', async () => {
    const app = createApp();
    const res = await request(app).get('/api/npc');
    expect(res.status).toBe(200);
    expect(res.body.npcs).toEqual([]);
    expect(res.body.pagination.total).toBe(0);
  });

  it('GET /api/npc/:id returns npc', async () => {
    const app = createApp();
  const createRes = await request(app).post('/api/npc').set('x-player-id', 'p5').send({ name: 'GetTest', prompt: 'p' });
    const id = createRes.body.id;
    const res = await request(app).get(`/api/npc/${id}`);
    expect(res.status).toBe(200);
    expect(res.body.id).toBe(id);
    expect(res.body).toHaveProperty('memory_log');
    expect(res.body.memory_log).toEqual({ recent_memory: [], old_memory: '' });
    expect(res.body).toHaveProperty('transactions');
    expect(res.body.transactions).toEqual([]);
  });

  it('GET /api/npc/:id returns 404 for non-existent', async () => {
    const app = createApp();
    const res = await request(app).get('/api/npc/nonexistent');
    expect(res.status).toBe(404);
    expect(res.body.error).toBe('not_found');
  });

  it('PATCH /api/npc/:id/prompt updates prompt for owner without broadcasting', async () => {
    const app = createApp();
  const createRes = await request(app).post('/api/npc').set('x-player-id', 'pp1').send({ name: 'PatchTest', prompt: 'initial' });
  const id = createRes.body.id;
  const res = await request(app).patch(`/api/npc/${id}/prompt`).set('x-player-id', 'pp1').send({ prompt: 'updated' });
    expect(res.status).toBe(200);
    expect(res.body.prompt).toBe('updated');
    // ensure broadcast not called for prompt update
    expect(broadcast).not.toHaveBeenCalledWith('prompt_updated', expect.anything());

    // patch with too long prompt
  const long = 'y'.repeat(PROMPT_MAX_LENGTH + 1);
  const res3 = await request(app).patch(`/api/npc/${id}/prompt`).set('x-player-id', 'pp1').send({ prompt: long });
    expect(res3.status).toBe(400);
  });

  it('PATCH /api/npc/:id/prompt returns 403 for non-owner', async () => {
    const app = createApp();
  const createRes = await request(app).post('/api/npc').set('x-player-id', 'pp2').send({ name: 'PatchTest2', prompt: 'p' });
  const id = createRes.body.id;
  const res = await request(app).patch(`/api/npc/${id}/prompt`).set('x-player-id', 'other').send({ prompt: 'bad' });
    expect(res.status).toBe(403);
  });

  it('GET /api/prompt-templates returns templates array with at least 6 items', async () => {
    const app = createApp();
    const res = await request(app).get('/api/prompt-templates');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('templates');
    expect(Array.isArray(res.body.templates)).toBe(true);
    expect(res.body.templates.length).toBeGreaterThanOrEqual(6);
  });

  it('DELETE /api/npc/:id allows owner to delete, removes from memory, logs event and broadcasts', async () => {
    const app = createApp();
    // create npc as owner pdel
    const createRes = await request(app).post('/api/npc').set('x-player-id', 'pdel').send({ name: 'ToDelete', prompt: 'p' });
    const id = createRes.body.id;

    const delRes = await request(app).delete(`/api/npc/${id}`).set('x-player-id', 'pdel');
    expect(delRes.status).toBe(200);
    expect(delRes.body).toHaveProperty('id', id);
    expect(delRes.body).toHaveProperty('deleted_at');

    // ensure memory repo no longer has the npc
    expect(memoryRepo.get(id)).toBeUndefined();

    // ensure event log contains npc_deleted
    const events = memoryRepo.getEvents();
    expect(events.find((e: any) => e.type === 'npc_deleted' && e.npc_id === id)).toBeTruthy();

    // ensure broadcast called
    expect(broadcast).toHaveBeenCalledWith('npc_deleted', expect.objectContaining({ id }));
  });

  it('DELETE /api/npc/:id returns 403 for non-owner', async () => {
    const app = createApp();
    const createRes = await request(app).post('/api/npc').set('x-player-id', 'owner2').send({ name: 'ToDelete2', prompt: 'p' });
    const id = createRes.body.id;
    const res = await request(app).delete(`/api/npc/${id}`).set('x-player-id', 'other');
    expect(res.status).toBe(403);
  });
});
