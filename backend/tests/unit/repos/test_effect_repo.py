import pytest

import aitown.repos.effect_repo as effect_repo_module
from aitown.repos.base import ConflictError
from aitown.repos.effect_repo import Effect, EffectRepository
from aitown.repos.npc_repo import NPC, NpcRepository


def test_effect_repo_crud_operations(db_conn):
    repo = EffectRepository(db_conn)
    effect = Effect(id="effect:test", name="Test Effect", attribute="energy", change=5)

    created = repo.create(effect)
    assert created.id == "effect:test"

    fetched = repo.get_by_id("effect:test")
    assert fetched.name == "Test Effect"

    repo.delete("effect:test")

    with pytest.raises(Exception):
        repo.get_by_id("effect:test")

    with pytest.raises(Exception):
        repo.delete("effect:test")


def test_effect_repo_create_conflict(db_conn):
    repo = EffectRepository(db_conn)
    effect = Effect(id="effect:dup", name="Dup", attribute="mood", change=1)

    repo.create(effect)
    with pytest.raises(ConflictError):
        repo.create(effect)


def test_effect_apply_to_npc_updates_attributes(db_conn, monkeypatch):
    npc_repo = NpcRepository(db_conn)
    npc_repo.create(
        NPC(
            id="npc:1", name="Eve", hunger=70, energy=40, mood=55, inventory={"seed": 1}
        )
    )

    monkeypatch.setattr(effect_repo_module, "NpcRepository", lambda: npc_repo)

    effect = Effect(
        id="effect:energy", name="Energy Surge", attribute="energy", change=20
    )
    effect.apply_to_npc("npc:1", factor=2)
    updated = npc_repo.get_by_id("npc:1")
    assert updated.energy == 80

    hunger_effect = Effect(
        id="effect:hunger", name="Big Meal", attribute="hunger", change=-100
    )
    hunger_effect.apply_to_npc("npc:1")
    updated_again = npc_repo.get_by_id("npc:1")
    assert updated_again.hunger == 0


def test_effect_apply_to_npc_updates_mood(db_conn, monkeypatch):
    npc_repo = NpcRepository(db_conn)
    npc_repo.create(
        NPC(
            id="npc:2",
            name="Mia",
            hunger=50,
            energy=50,
            mood=10,
            inventory={"token": 1},
        )
    )

    monkeypatch.setattr(effect_repo_module, "NpcRepository", lambda: npc_repo)

    mood_effect = Effect(id="effect:mood", name="Joy", attribute="mood", change=30)
    mood_effect.apply_to_npc("npc:2")

    updated = npc_repo.get_by_id("npc:2")
    assert updated.mood == 40


def test_effect_apply_to_npc_ignores_unknown_attribute(db_conn, monkeypatch):
    npc_repo = NpcRepository(db_conn)
    npc_repo.create(
        NPC(
            id="npc:3",
            name="Lex",
            hunger=20,
            energy=90,
            mood=80,
            inventory={"token": 2},
        )
    )

    monkeypatch.setattr(effect_repo_module, "NpcRepository", lambda: npc_repo)

    noop_effect = Effect(id="effect:noop", name="Mystery", attribute="luck", change=999)
    noop_effect.apply_to_npc("npc:3")

    updated = npc_repo.get_by_id("npc:3")
    assert updated.hunger == 20
    assert updated.energy == 90
    assert updated.mood == 80
