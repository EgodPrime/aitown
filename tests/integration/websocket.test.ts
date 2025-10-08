import { describe, it, expect } from 'vitest';
import WebSocket from 'ws';
import http from 'http';
import createApp from '../../src/app';
import { initBroadcaster } from '../../src/ws/broadcaster';
import request from 'supertest';

describe('WebSocket Broadcasting Integration', () => {
  it('client receives npc_created event on POST /api/npc', async () => {
    const app = createApp();
    const server = http.createServer(app);
    initBroadcaster(server);

    // Start server on random port
    await new Promise<void>((resolve) => {
      server.listen(0, () => resolve());
    });

    const port = (server.address() as any).port;

    // Connect WebSocket client
    const ws = new WebSocket(`ws://localhost:${port}`);
    const messages: any[] = [];
    ws.on('message', (data) => {
      messages.push(JSON.parse(data.toString()));
    });

    // Wait for connection
    await new Promise<void>((resolve) => {
      ws.on('open', () => resolve());
    });

    // Send POST request to create npc
    const res = await request(app)
      .post('/api/npc')
      .send({ player_id: 'test', name: 'TestNPC', prompt: 'test' });
    expect(res.status).toBe(201);

    // Wait a bit for created message
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Check created message received
    expect(messages).toHaveLength(1);
    expect(messages[0]).toEqual({
      type: 'npc_created',
      payload: { id: res.body.id }
    });

    // Now delete the NPC as the owner and expect an npc_deleted broadcast
    const id = res.body.id;
    const delRes = await request(app)
      .delete(`/api/npc/${id}`)
      .set('x-player-id', 'test');
    expect(delRes.status).toBe(200);

    // Wait a bit for deleted message
    await new Promise((resolve) => setTimeout(resolve, 100));

  // Expect two messages: created then deleted
  expect(messages.length).toBeGreaterThanOrEqual(2);
  expect(messages[1].type).toBe('npc_deleted');
  expect(messages[1].payload).toHaveProperty('id', id);
  // Expect human-readable message announcing departure
  expect(messages[1].payload).toHaveProperty('message');
  expect(typeof messages[1].payload.message).toBe('string');
  expect(messages[1].payload.message).toContain('永远离开了小镇');

    // Cleanup
    ws.close();
    server.close();
  });
});