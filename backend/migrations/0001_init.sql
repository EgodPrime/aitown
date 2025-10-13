-- Initial schema for aitown MVP
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS player (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  display_name TEXT NOT NULL,
  password_hash TEXT,
  created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS place (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  tags TEXT,
  shop_inventory TEXT
);

CREATE TABLE IF NOT EXISTS road (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  from_place INTEGER NOT NULL,
  to_place INTEGER NOT NULL,
  direction TEXT NOT NULL,
  FOREIGN KEY(from_place) REFERENCES place(id) ON DELETE CASCADE,
  FOREIGN KEY(to_place)   REFERENCES place(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS item (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  value INTEGER DEFAULT 0,
  type TEXT NOT NULL,
  effect_ids TEXT,
  description TEXT
);

CREATE TABLE IF NOT EXISTS effect (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  attribute TEXT NOT NULL,
  change INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS npc (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  player_id INTEGER,
  name TEXT,
  gender TEXT,
  age INTEGER,
  prompt TEXT,
  location_id INTEGER,
  status TEXT DEFAULT 'peaceful',
  hunger INTEGER DEFAULT 100,
  energy INTEGER DEFAULT 100,
  mood INTEGER DEFAULT 100,
  inventory TEXT DEFAULT '{}',
  long_memory TEXT,
  is_dead INTEGER DEFAULT 0,
  created_at REAL,
  updated_at REAL,
  FOREIGN KEY(player_id) REFERENCES player(id) ON DELETE SET NULL,
  FOREIGN KEY(location_id) REFERENCES place(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS memory_entry (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  npc_id TEXT,
  content TEXT,
  created_at REAL,
  FOREIGN KEY(npc_id) REFERENCES npc(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS event (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT,
  payload TEXT,
  created_at REAL,
  processed INTEGER DEFAULT 0,
  processed_at REAL
);

CREATE TABLE IF NOT EXISTS town (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  description TEXT,
  sim_start_time REAL DEFAULT 0
);


-- Indexes
CREATE INDEX IF NOT EXISTS idx_npc_player ON npc(player_id);
CREATE INDEX IF NOT EXISTS idx_npc_location ON npc(location_id);