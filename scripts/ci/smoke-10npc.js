// Minimal smoke test harness for 10 NPCs
// This script attempts to use the app's HTTP API to create NPCs and simulate a few cycles.
// It uses the local server endpoints and a mock adapter where possible.

const fetch = require('node-fetch');

const BASE = process.env.BASE_URL || 'http://localhost:3000';

async function createNpc(i) {
  const res = await fetch(`${BASE}/npc`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-player-id': `test-${i}` },
    body: JSON.stringify({ name: `SmokeNPC-${i}`, prompt: `Behavior test npc ${i}` })
  });
  if (!res.ok) throw new Error(`Create NPC failed: ${res.status}`);
  return res.json();
}

async function run() {
  console.log('Starting smoke test: creating 10 NPCs');
  const npcs = [];
  for (let i = 0; i < 10; i++) {
    try {
      const npc = await createNpc(i);
      npcs.push(npc);
      console.log('Created', npc.id || npc);
    } catch (err) {
      console.error('Error creating npc', err.message);
      process.exit(2);
    }
  }

  // Wait a short while to let the system process and emit events (if running locally)
  console.log('Waiting 5s for system to process cycles...');
  await new Promise(r => setTimeout(r, 5000));

  // Check a sample NPC for GET /npc/{id}
  const sample = npcs[0];
  try {
    const res = await fetch(`${BASE}/npc/${sample.id}`, { headers: { 'x-player-id': 'test-0' } });
    if (!res.ok) throw new Error(`GET npc failed: ${res.status}`);
    const body = await res.json();
    console.log('Sample NPC fetched:', body.id || 'ok');
  } catch (err) {
    console.error('Failed to fetch sample NPC', err.message);
    process.exit(3);
  }

  console.log('Smoke test completed successfully (basic).');
}

run().catch(err => {
  console.error('Smoke test error', err);
  process.exit(1);
});
