"""Effect repository and Effect model.

Represents effects that can be applied to NPC attributes and a repository to persist them.
"""

from aitown.models.effect_model import Effect
from aitown.repos.interfaces import RepositoryInterface

class EffectRepository(RepositoryInterface[Effect]):
    """SQLite-backed repository for Effect objects."""
    def __init__(self, conn = None):
        super().__init__(conn)
        self.table_name = "effect"
