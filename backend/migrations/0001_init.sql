-- Initial schema for aitown MVP
PRAGMA foreign_keys = ON;

CREATE TABLE player (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE place (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tags TEXT,
  shop_inventory TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE road (
  id TEXT PRIMARY KEY,
  from_place TEXT NOT NULL,
  to_place TEXT NOT NULL,
  direction TEXT NOT NULL,
  FOREIGN KEY(from_place) REFERENCES place(id) ON DELETE CASCADE,
  FOREIGN KEY(to_place)   REFERENCES place(id) ON DELETE CASCADE
);

CREATE TABLE item (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT
);

CREATE TABLE npc (
  id TEXT PRIMARY KEY,
  player_id TEXT,
  name TEXT,
  gender TEXT,
  age INTEGER,
  prompt TEXT,
  location_id TEXT,
  hunger INTEGER DEFAULT 100,
  energy INTEGER DEFAULT 100,
  mood INTEGER DEFAULT 100,
  inventory TEXT DEFAULT '[]',
  memory_id TEXT,
  is_dead INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY(player_id) REFERENCES player(id) ON DELETE SET NULL,
  FOREIGN KEY(location_id) REFERENCES place(id) ON DELETE SET NULL,
  FOREIGN KEY(memory_id) REFERENCES npc_memory(npc_id) ON DELETE CASCADE
);

CREATE TABLE memory_entry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  text TEXT,
  timestamp TEXT,
  FOREIGN KEY(npc_id) REFERENCES npc(id) ON DELETE CASCADE
);

CREATE TABLE npc_memory (
  npc_id TEXT PRIMARY KEY,
  long_memory TEXT,
  recent_memory TEXT
);

CREATE TABLE event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  event_type TEXT,
  payload TEXT,
  created_at TEXT,
  processed INTEGER DEFAULT 0,
  processed_at TEXT,
  FOREIGN KEY(npc_id) REFERENCES npc(id) ON DELETE CASCADE
);


CREATE TABLE transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  item_id TEXT,
  amount INTEGER,
  reason TEXT,
  created_at TEXT,
  FOREIGN KEY(npc_id) REFERENCES npc(id) ON DELETE SET NULL,
  FOREIGN KEY(item_id) REFERENCES item(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_npc_player ON npc(player_id);
CREATE INDEX IF NOT EXISTS idx_npc_location ON npc(location_id);
CREATE INDEX IF NOT EXISTS idx_event_npc_created_at ON event(npc_id, created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_npc ON transactions(npc_id);
