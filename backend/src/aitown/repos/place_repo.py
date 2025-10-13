"""Place repository and models.

This module provides the Place Pydantic model and a SQLite-backed PlaceRepository.
"""

import datetime
import enum
import sqlite3
import uuid
from typing import List, Optional

from pydantic import Field
import time

from aitown.models.place_model import Place, PlaceTag
from aitown.repos.interfaces import RepositoryInterface


class PlaceRepository(RepositoryInterface[Place]):
    """SQLite-backed repository for Place objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "place"