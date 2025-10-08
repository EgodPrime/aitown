import { describe, it, expect, beforeEach, vi } from 'vitest';
import request from 'supertest';
import createApp from '../../src/app';
vi.mock('../../src/ws/broadcaster', () => ({ broadcast: vi.fn() }));
import { broadcast } from '../../src/ws/broadcaster';
import { memoryRepo } from '../../src/repos/memoryRepo';
import { PROMPT_MAX_LENGTH } from '../../src/config';

describe('PATCH prompt integration', () => {
  beforeEach(() => {
    memoryRepo.clear();
  });

  it('PATCH updates prompt for owner and subsequent GET returns updated prompt; no broadcast emitted for prompt_updated', async () => {
    const app = createApp();
    // Create NPC as player:owner1
    const createRes = await request(app).post('/api/npc').set('x-player-id', 'owner1').send({ name: 'I', prompt: 'old' });
    expect(createRes.status).toBe(201);
    const id = createRes.body.id;

    // Patch prompt as same player
    const patchRes = await request(app).patch(`/api/npc/${id}/prompt`).set('x-player-id', 'owner1').send({ prompt: 'newprompt' });
    expect(patchRes.status).toBe(200);
    expect(patchRes.body.prompt).toBe('newprompt');

    // GET should return updated prompt
    const getRes = await request(app).get(`/api/npc/${id}`);
    expect(getRes.status).toBe(200);
    expect(getRes.body.prompt).toBe('newprompt');

    // Ensure no broadcast event for prompt_updated
    expect(broadcast).not.toHaveBeenCalledWith('prompt_updated', expect.anything());
    
    // patch with too long prompt (using config)
    const tooLong = 'z'.repeat(PROMPT_MAX_LENGTH + 1);
    const resTooLong = await request(app).patch(`/api/npc/${id}/prompt`).set('x-player-id', 'owner1').send({ prompt: tooLong });
    expect(resTooLong.status).toBe(400);
  });
});
