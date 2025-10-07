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

    // Send POST request
    const res = await request(app).post('/api/npc').send({ player_id: 'test', name: 'TestNPC', prompt: 'test' });
    expect(res.status).toBe(201);

    // Wait a bit for message
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Check message received
    expect(messages).toHaveLength(1);
    expect(messages[0]).toEqual({
      type: 'npc_created',
      payload: { id: res.body.id }
    });

    // Cleanup
    ws.close();
    server.close();
  });
});