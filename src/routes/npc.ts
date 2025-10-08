import express from 'express';
import { npcService } from '../services/npcService';
import { PROMPT_MAX_LENGTH } from '../config';
import { broadcast } from '../ws/broadcaster';

const router = express.Router();

router.post('/', (req, res) => {
  try {
    if (!req.body.name || typeof req.body.name !== 'string') return res.status(400).json({ error: 'name is required and must be string' });
    if (!req.body.prompt || typeof req.body.prompt !== 'string') return res.status(400).json({ error: 'prompt is required and must be string' });
  // Prefer player id from middleware (session/auth). Fall back to body for compatibility.
    const playerId = (req as any).player_id || req.body.player_id || 'player:anon';
    // Validate prompt length
    if (typeof req.body.prompt === 'string' && req.body.prompt.length > PROMPT_MAX_LENGTH) {
      return res.status(400).json({ error: 'prompt_too_long' });
    }
    const npc = npcService.create(playerId, req.body);
    broadcast('npc_created', { id: npc.id });
    const response = {
      id: npc.id,
      player_id: npc.player_id,
      name: npc.name,
      prompt: npc.prompt,
      initial_stats: {
        hunger: npc.hunger,
        energy: npc.energy,
        mood: npc.mood,
        money: npc.money,
        inventory: npc.inventory,
        location: npc.location,
        alive: npc.alive
      }
    };
    res.status(201).json(response);
  } catch (err: any) {
    if (err.message === 'PLAYER_HAS_ACTIVE_NPC') return res.status(409).json({ error: 'Player already has active NPC' });
    res.status(500).json({ error: 'server_error' });
  }
});

router.get('/', (req, res) => {
  let limit = 10;
  if (req.query.limit !== undefined) {
    const parsed = parseInt(req.query.limit as string);
    if (isNaN(parsed) || parsed <= 0 || parsed > 100) {
      return res.status(400).json({ error: 'limit must be a positive integer between 1 and 100' });
    }
    limit = parsed;
  }
  let offset = 0;
  if (req.query.offset !== undefined) {
    const parsed = parseInt(req.query.offset as string);
    if (isNaN(parsed) || parsed < 0) {
      return res.status(400).json({ error: 'offset must be a non-negative integer' });
    }
    offset = parsed;
  }
  const result = npcService.list({ limit, offset });
  res.json({
    npcs: result.items,
    pagination: {
      total: result.total,
      limit,
      offset
    }
  });
});

router.get('/:id', (req, res) => {
  const npc = npcService.get(req.params.id);
  if (!npc) return res.status(404).json({ error: 'not_found' });
  res.json(npc);
});

router.patch('/:id/prompt', (req, res) => {
  try {
    const id = req.params.id;
    const newPrompt = req.body.prompt;
  if (typeof newPrompt !== 'string') return res.status(400).json({ error: 'prompt is required and must be string' });
  if (newPrompt.length > PROMPT_MAX_LENGTH) return res.status(400).json({ error: 'prompt_too_long' });
    // For sensitive operations, require authenticated player id from middleware to avoid spoofing.
    const playerId = (req as any).player_id;
    if (!playerId) return res.status(401).json({ error: 'unauthorized' });
    const updated = npcService.updatePrompt(playerId, id, newPrompt);
    // Do NOT broadcast prompt changes to other players per story requirements
    res.json(updated);
  } catch (err: any) {
    if (err.message === 'NOT_FOUND') return res.status(404).json({ error: 'not_found' });
    if (err.message === 'FORBIDDEN') return res.status(403).json({ error: 'forbidden' });
    res.status(500).json({ error: 'server_error' });
  }
});

router.delete('/:id', (req, res) => {
  try {
    const id = req.params.id;
    const playerId = (req as any).player_id;
    if (!playerId) return res.status(401).json({ error: 'unauthorized' });
  const deleted = npcService.delete(playerId, id);
  // human-readable announcement
  const humanMsg = `${deleted.name} 永远离开了小镇`;
  // broadcast deletion to websocket subscribers with a readable announcement
  broadcast('npc_deleted', { id: deleted.id, actor: playerId, deleted_at: deleted.deleted_at, message: humanMsg });
  res.json({ id: deleted.id, deleted_at: deleted.deleted_at, message: humanMsg });
  } catch (err: any) {
    if (err.message === 'NOT_FOUND') return res.status(404).json({ error: 'not_found' });
    if (err.message === 'FORBIDDEN') return res.status(403).json({ error: 'forbidden' });
    res.status(500).json({ error: 'server_error' });
  }
});

export default router;
