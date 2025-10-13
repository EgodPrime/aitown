"""Player repository and model.

Defines a simple Player model and repository for persistence.
"""

import datetime
import sqlite3
import uuid
from typing import Optional

from pydantic import Field
import time

from aitown.models.player_model import Player
from aitown.repos.interfaces import RepositoryInterface


class PlayerRepository(RepositoryInterface[Player]):
    """SQLite-backed repository for Player objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "player"