import { describe, it, expect, vi, beforeEach } from 'vitest';
import request from 'supertest';
import createApp from '../../src/app';
import { broadcast } from '../../src/ws/broadcaster';

vi.mock('../../src/ws/broadcaster', () => ({
  broadcast: vi.fn()
}));

describe('NPC routes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it('POST /api/npc creates npc with valid response', async () => {
    const app = createApp();
    const res = await request(app).post('/api/npc').send({ player_id: 'p1', name: 'RTest', prompt: 'test prompt' });
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
    await request(app).post('/api/npc').send({ player_id: 'p2', name: 'A', prompt: 'p' });
    const res = await request(app).post('/api/npc').send({ player_id: 'p2', name: 'B', prompt: 'p' });
    expect(res.status).toBe(409);
    expect(res.body.error).toBe('Player already has active NPC');
  });

  it('POST /api/npc validates input', async () => {
    const app = createApp();
    const res = await request(app).post('/api/npc').send({ player_id: 'p3' });
    expect(res.status).toBe(400);
  });

  it('GET /api/npc returns list', async () => {
    const app = createApp();
    await request(app).post('/api/npc').send({ player_id: 'p4', name: 'ListTest', prompt: 'p' });
    const res = await request(app).get('/api/npc');
    expect(res.status).toBe(200);
    expect(Array.isArray(res.body)).toBe(true);
  });

  it('GET /api/npc/:id returns npc', async () => {
    const app = createApp();
    const createRes = await request(app).post('/api/npc').send({ player_id: 'p5', name: 'GetTest', prompt: 'p' });
    const id = createRes.body.id;
    const res = await request(app).get(`/api/npc/${id}`);
    expect(res.status).toBe(200);
    expect(res.body.id).toBe(id);
  });
});
