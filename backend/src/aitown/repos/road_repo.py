"""Road repository and the Road model.

Represents bidirectional connections between places and a repository to persist them.
"""

import uuid
from typing import List, Optional

from aitown.models.road_model import Road
from aitown.repos.interfaces import RepositoryInterface


class RoadRepository(RepositoryInterface[Road]):
    """SQLite-backed repository for Road objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "road"