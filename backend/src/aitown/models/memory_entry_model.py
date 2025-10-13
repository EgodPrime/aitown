"""MemoryEntry model extracted from repos/memory_repo.py"""
from typing import Optional
from pydantic import BaseModel, Field
import time


class MemoryEntry(BaseModel):
    id: Optional[int] = None
    npc_id: Optional[str] = None
    content: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
