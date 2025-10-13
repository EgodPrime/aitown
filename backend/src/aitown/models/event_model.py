"""Event model extracted from repos/event_repo.py"""
from typing import Optional
from pydantic import BaseModel, Field
import time


class Event(BaseModel):
    id: Optional[int] = None
    npc_id: Optional[str] = None
    event_type: str
    payload: dict = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    processed: int = 0
    processed_at: Optional[float] = None
