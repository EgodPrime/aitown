"""Item repository and item model.

Provides Item pydantic model and ItemRepository for DB operations.
"""

import enum
import sqlite3
import uuid
from typing import List, Optional

from pydantic import Field

from aitown.models.item_model import Item, ItemType
from aitown.repos.interfaces import RepositoryInterface


class ItemRepository(RepositoryInterface[Item]):
    """SQLite-backed repository for Item objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "item"