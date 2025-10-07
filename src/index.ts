import express from 'express';
import http from 'http';
import cors from 'cors';
import npcRouter from './routes/npc';
import { initBroadcaster } from './ws/broadcaster';

const app = express();
app.use(cors());
app.use(express.json());

app.use('/api/npc', npcRouter);

const server = http.createServer(app);
initBroadcaster(server as any);

const port = process.env.PORT || 3000;
server.listen(port, () => {
  console.log('Server listening on', port);
});
