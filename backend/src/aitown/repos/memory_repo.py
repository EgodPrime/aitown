"""Memory entry repository and model.

Stores short NPC memory entries persisted to the database.
"""

import datetime
import sqlite3
from typing import List, Optional

from pydantic import Field
import time

from aitown.models.memory_entry_model import MemoryEntry
from aitown.repos.interfaces import RepositoryInterface


class MemoryEntryRepository(RepositoryInterface[MemoryEntry]):
    """SQLite-backed repository for MemoryEntry objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "memory_entry"