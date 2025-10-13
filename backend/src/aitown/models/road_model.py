"""Road model extracted from repos/road_repo.py"""
from typing import Optional
from pydantic import BaseModel


class Road(BaseModel):
    id: Optional[str] = None
    from_place: str
    to_place: str
    direction: str
