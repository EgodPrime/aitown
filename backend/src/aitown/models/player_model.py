"""Player model extracted from repos/player_repo.py"""
from typing import Optional
from pydantic import BaseModel, Field
import time


class Player(BaseModel):
    id: Optional[str] = None
    display_name: str
    password_hash: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
