"""Effect repository and Effect model.

Represents effects that can be applied to NPC attributes and a repository to persist them.
"""

from aitown.models.effect_model import Effect
from aitown.repos.interfaces import RepositoryInterface

class EffectRepository(RepositoryInterface[Effect]):
    pass
