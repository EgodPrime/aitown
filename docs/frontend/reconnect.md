# Frontend reconnect pattern (WebSocket + HTTP /state fallback)

This file contains a minimal, copy-paste friendly JavaScript snippet showing a robust reconnect strategy for clients. It: 

- Opens a WebSocket to `/ws` and listens for the initial `full_state` message.
- On websocket close or failure, attempts reconnect with exponential backoff.
- After a successful reconnect, if the websocket client did not receive the initial `full_state`, fetches `/state` as an HTTP fallback and reconciles the local UI state.

Use this as a starting point; adapt it to your frontend framework and UI state management.

```javascript
// Minimal reconnect helper for the AI Town frontend
// Usage: const client = new ReconnectClient({ wsUrl: 'ws://localhost:8000/ws', stateUrl: '/state', onState: handleState });

class ReconnectClient {
  constructor({ wsUrl, stateUrl, onState, maxBackoff = 30000 }) {
    this.wsUrl = wsUrl;
    this.stateUrl = stateUrl;
    this.onState = onState; // callback(payload)
    this.maxBackoff = maxBackoff;

    this.socket = null;
    this.connected = false;
    this.backoff = 1000;
    this.receivedInitialState = false;

    this.connect();
  }

  connect() {
    this.socket = new WebSocket(this.wsUrl);

    this.socket.addEventListener('open', () => {
      console.info('ws open');
      this.connected = true;
      this.backoff = 1000; // reset backoff
      // If we didn't receive the initial state via WS (race or lost), fall back to HTTP get
      if (!this.receivedInitialState) {
        this._fetchStateFallback();
      }
    });

    this.socket.addEventListener('message', (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg && msg.type === 'full_state') {
          this.receivedInitialState = true;
          if (this.onState) this.onState(msg.payload);
        } else if (msg && msg.type === 'state_update') {
          // incremental updates
          if (this.onState) this.onState(msg.payload);
        } else {
          // handle other message types as needed
        }
      } catch (e) {
        console.warn('failed to parse ws message', e);
      }
    });

    this.socket.addEventListener('close', () => {
      console.info('ws closed');
      this.connected = false;
      this._scheduleReconnect();
    });

    this.socket.addEventListener('error', (e) => {
      console.warn('ws error', e);
      // close triggers reconnect logic
      try { this.socket.close(); } catch (e) {}
    });
  }

  _scheduleReconnect() {
    const wait = Math.min(this.backoff, this.maxBackoff);
    console.info(`reconnect in ${wait}ms`);
    setTimeout(() => {
      this.backoff = Math.min(this.backoff * 2, this.maxBackoff);
      this.connect();
    }, wait);
  }

  async _fetchStateFallback() {
    // HTTP fallback to get full state when WS initial full_state may have been missed
    try {
      const r = await fetch(this.stateUrl, { method: 'GET', credentials: 'same-origin' });
      if (!r.ok) throw new Error('state fetch failed');
      const data = await r.json();
      // data.payload expected
      if (data && data.payload) {
        this.receivedInitialState = true;
        if (this.onState) this.onState(data.payload);
      }
    } catch (e) {
      console.warn('state fallback failed', e);
    }
  }

  close() {
    try { this.socket.close(); } catch (e) {}
    this.connected = false;
  }
}

// Example usage:
// function handleState(payload) { renderNpcs(payload); }
// const client = new ReconnectClient({ wsUrl: 'ws://localhost:8000/ws', stateUrl: '/state', onState: handleState });
```

Notes
- This snippet is framework-agnostic. In React/Vue/Svelte adapt callbacks to set state via your store.
- For mobile or flaky networks, consider using jittered backoff and persistent connection state across page visibility changes.
- If your frontend needs strict ordering or deduplication of incremental updates, implement a lightweight sequence number or timestamp check when applying `state_update` payloads.
