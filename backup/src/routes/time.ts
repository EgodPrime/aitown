import express from 'express';
import simClock from '../services/simClock';

const router = express.Router();

router.get('/', (req, res) => {
  try {
    const now = simClock.now();
    res.json({
      sim_time_iso: now.sim_time_iso,
      sim_day: now.sim_day,
      sim_day_fraction: now.sim_day_fraction,
      realtime_timestamp: now.realtime_timestamp
    });
  } catch (err: any) {
    res.status(500).json({ error: 'server_error' });
  }
});

export default router;
