-- Initial schema for aitown MVP
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS player (
  id TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS place (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  tags TEXT,
  shop_inventory TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS road (
  id TEXT PRIMARY KEY,
  from_place TEXT NOT NULL,
  to_place TEXT NOT NULL,
  direction TEXT NOT NULL,
  FOREIGN KEY(from_place) REFERENCES place(id) ON DELETE CASCADE,
  FOREIGN KEY(to_place)   REFERENCES place(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  value INTEGER DEFAULT 0,
  type TEXT NOT NULL,
  effect_ids TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS effect (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  attribute TEXT NOT NULL,
  change INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS npc (
  id TEXT PRIMARY KEY,
  player_id TEXT,
  name TEXT,
  gender TEXT,
  age INTEGER,
  prompt TEXT,
  location_id TEXT,
  status TEXT DEFAULT 'peaceful',
  hunger INTEGER DEFAULT 100,
  energy INTEGER DEFAULT 100,
  mood INTEGER DEFAULT 100,
  inventory TEXT DEFAULT '[]',
  long_memory TEXT,
  is_dead INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  FOREIGN KEY(player_id) REFERENCES player(id) ON DELETE SET NULL,
  FOREIGN KEY(location_id) REFERENCES place(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS memory_entry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  content TEXT,
  created_at TEXT,
  FOREIGN KEY(npc_id) REFERENCES npc(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT,
  payload TEXT,
  created_at TEXT,
  processed INTEGER DEFAULT 0,
  processed_at TEXT
);



-- Indexes
CREATE INDEX IF NOT EXISTS idx_npc_player ON npc(player_id);
CREATE INDEX IF NOT EXISTS idx_npc_location ON npc(location_id);