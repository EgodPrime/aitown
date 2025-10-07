import express from 'express';
import { npcService } from '../services/npcService';
import { broadcast } from '../ws/broadcaster';

const router = express.Router();

router.post('/', (req, res) => {
  try {
    if (!req.body.name || typeof req.body.name !== 'string') return res.status(400).json({ error: 'name is required and must be string' });
    if (!req.body.prompt || typeof req.body.prompt !== 'string') return res.status(400).json({ error: 'prompt is required and must be string' });
    const playerId = req.body.player_id || 'player:anon';
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
  const list = npcService.list();
  res.json(list);
});

router.get('/:id', (req, res) => {
  const npc = npcService.get(req.params.id);
  if (!npc) return res.status(404).json({ error: 'not_found' });
  res.json(npc);
});

export default router;
