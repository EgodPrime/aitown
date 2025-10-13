"""NPC model and repository.

Defines the NPC Pydantic model and a SQLite-backed NpcRepository.
"""

from __future__ import annotations

import sqlite3
import uuid
from typing import List, Optional
from loguru import logger

from aitown.repos.memory_repo import MemoryEntryRepository
import time

from aitown.models.npc_model import NPC, NPCStatus
from aitown.repos.interfaces import RepositoryInterface
from aitown.helpers.config_helper import get_config
from aitown.helpers.llm_helper import generate
import json
import re
from aitown.models.event_model import Event
from aitown.models.memory_entry_model import MemoryEntry
from aitown.kernel.event_bus import InMemoryEventBus
from aitown.kernel.event_bus import EventType

cfg = get_config("npc")

class NpcRepository(RepositoryInterface[NPC]):
    """SQLite-backed repository for NPC objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "npc"
