"""Town model extracted from repos/town_repo.py"""
from typing import Optional
from pydantic import BaseModel


class Town(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    sim_start_time: Optional[float] = None
