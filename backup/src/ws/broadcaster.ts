import { WebSocketServer } from 'ws';

let wss: WebSocketServer | null = null;

export function initBroadcaster(server: any) {
  wss = new WebSocketServer({ server });
  wss.on('connection', (socket) => {
    // simple echo for now
    socket.on('message', (msg) => {
      // noop
    });
  });
}

export function broadcast(event: string, payload: any) {
  if (!wss) return;
  const message = JSON.stringify({ type: event, payload });
  wss.clients.forEach(c => {
    if (c.readyState === 1) c.send(message); // 1 is OPEN
  });
}
