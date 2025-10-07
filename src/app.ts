import express from 'express';
import cors from 'cors';
import npcRouter from './routes/npc';

export default () => {
  const app = express();
  app.use(cors());
  app.use(express.json());

  app.use('/api/npc', npcRouter);

  return app;
};
