"""Compatibility shim for aitown.server package"""

# Re-export the app and NPCS from the local models module so tests that
# import aitown.server.* continue to work after the src/ layout migration.
from aitown.server.main import app, NPCS, PLAYER_API_CONFIGS

__all__ = ["app", "NPCS", "PLAYER_API_CONFIGS"]
