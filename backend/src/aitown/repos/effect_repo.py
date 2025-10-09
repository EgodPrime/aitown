import sqlite3
from typing import Optional, List
from pydantic import BaseModel
from aitown.repos.base import NotFoundError, to_json_text, from_json_text
from aitown.repos.interfaces import EffectRepositoryInterface
from aitown.repos.npc_repo import NpcRepository

class Effect(BaseModel):
    id: Optional[str] = None
    name: str
    attribute: str # hunger, energy, mood
    change: int

    def apply_to_npc(self, npc_id: str, factor: int = 1):
        npc_repo = NpcRepository()
        npc = npc_repo.get_by_id(npc_id)
        match self.attribute:
            case "hunger":
                npc.hunger = max(0, min(100, npc.hunger + self.change * factor))
                npc_repo.update(npc_id, {"hunger": npc.hunger})
            case "energy":
                npc.energy = max(0, min(100, npc.energy + self.change * factor))
                npc_repo.update(npc_id, {"energy": npc.energy})
            case "mood":
                npc.mood = max(0, min(100, npc.mood + self.change * factor))
                npc_repo.update(npc_id, {"mood": npc.mood})
            case _:
                pass



class EffectRepository(EffectRepositoryInterface):
    def create(self, effect: Effect) -> Effect:
        cur = self.conn.cursor()
        try:
            cur.execute(
                "INSERT INTO effect (id, name, attribute, change) VALUES (?, ?, ?, ?)",
                (effect.id, effect.name, effect.attribute, effect.change),
            )
        except sqlite3.IntegrityError as e:
            from aitown.repos.base import ConflictError

            raise ConflictError(str(e))
        else:
            self.conn.commit()
        return effect

    def get_by_id(self, id: str) -> Effect:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM effect WHERE id = ?", (id,))
        row = cur.fetchone()
        if not row:
            raise NotFoundError(f"Effect not found: {id}")
        return Effect(id=row["id"], name=row["name"], attribute=row["attribute"], change=row["change"])

    def delete(self, id: str) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM effect WHERE id = ?", (id,))
        if cur.rowcount == 0:
            raise NotFoundError(f"Effect not found: {id}")
        self.conn.commit()