import express from 'express';
import cors from 'cors';
import npcRouter from './routes/npc';

export default () => {
  const app = express();
  app.use(cors());
  app.use(express.json());

  // Simple auth/session middleware used in tests and for demos.
  // It derives player identity from the `x-player-id` header and attaches it to the request as `player_id`.
  app.use((req, _res, next) => {
    const pid = req.header('x-player-id');
    if (pid) {
      (req as any).player_id = pid;
    }
    next();
  });

  app.use('/api/npc', npcRouter);

  return app;
};
