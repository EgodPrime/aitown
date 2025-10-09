# Database schema and conventions

This document describes the minimal SQLite schema used by the aitown MVP, the meaning of fields, and conventions for JSON fields stored as TEXT.

Files
- migrations/0001_init.sql — SQL to create the schema
- backend/scripts/init_db.py — helper to run migrations and optionally seed minimal data

General conventions
- SQLite is used for the MVP. JSON-like structures (tags, inventory, shop_inventory) are stored as TEXT containing JSON strings. Applications must serialize/deserialize these fields.
- All timestamps are stored as ISO-8601 strings (UTC) in TEXT columns.
- Foreign key behavior depends on PRAGMA foreign_keys = ON. Our migrations enable it; callers should keep it enabled.

Tables

- player
  - id TEXT PRIMARY KEY — unique player id (e.g., "player:abc")
  - display_name TEXT NOT NULL — human-friendly name
  - password_hash TEXT — optional password hash
  - created_at TEXT NOT NULL — ISO-8601 UTC timestamp

- place
  - id TEXT PRIMARY KEY
  - name TEXT NOT NULL
  - tags TEXT — JSON array string, e.g. "[\"shop\",\"market\"]"
  - shop_inventory TEXT — JSON array string, e.g. "[\"coin\",\"apple\"]"
  - created_at TEXT NOT NULL

- road
  - id TEXT PRIMARY KEY
  - from_place TEXT NOT NULL (FK -> place.id)
  - to_place TEXT NOT NULL (FK -> place.id)
  - direction TEXT NOT NULL

- item
  - id TEXT PRIMARY KEY
  - name TEXT NOT NULL
  - description TEXT

- npc
  - id TEXT PRIMARY KEY
  - player_id TEXT (FK -> player.id) ON DELETE SET NULL
  - name TEXT
  - gender TEXT
  - age INTEGER
  - prompt TEXT
  - location_id TEXT (FK -> place.id) ON DELETE SET NULL
  - hunger INTEGER DEFAULT 100
  - energy INTEGER DEFAULT 100
  - mood INTEGER DEFAULT 100
  - inventory TEXT DEFAULT '[]' — JSON array string of objects like {"item_id": "item:..", "num": 2}
  - memory_id TEXT (FK -> npc_memory.npc_id)
  - is_dead INTEGER DEFAULT 0
  - created_at TEXT
  - updated_at TEXT

- npc_memory
  - npc_id TEXT PRIMARY KEY
  - long_memory TEXT
  - recent_memory TEXT

- memory_entry
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id)
  - text TEXT
  - timestamp TEXT

- event
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id)
  - event_type TEXT
  - payload TEXT
  - created_at TEXT
  - processed INTEGER DEFAULT 0
  - processed_at TEXT

- transactions
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - npc_id TEXT (FK -> npc.id) ON DELETE SET NULL
  - item_id TEXT (FK -> item.id) ON DELETE SET NULL
  - amount INTEGER
  - reason TEXT
  - created_at TEXT

Indexes (created in migration)
- idx_npc_player ON npc(player_id)
- idx_npc_location ON npc(location_id)
- idx_event_npc_created_at ON event(npc_id, created_at)
- idx_transactions_npc ON transactions(npc_id)

JSON field examples

- place.tags
  - Example: ["shop","market"] stored as TEXT: "[\"shop\",\"market\"]"

- npc.inventory
  - Example: [{"item_id": "item:coin", "num": 10}] stored as TEXT: "[{\"item_id\": \"item:coin\", \"num\": 10}]"

Notes
- For complex JSON queries consider enabling the JSON1 extension or migrating to a DB with native JSON support.
