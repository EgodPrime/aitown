import express from 'express';
import { getTemplates } from '../config/promptTemplates';

const router = express.Router();

// Serve the prompt templates JSON as a read-only endpoint.
router.get('/', (_req, res) => {
  try {
    const data = getTemplates();
    res.json({ templates: data });
  } catch (err) {
    res.status(500).json({ error: 'server_error' });
  }
});

export default router;
