from aitown.repos.effect_repo import EffectRepository
from aitown.models.effect_model import Effect

def test_create(effect_repo: EffectRepository):
    effect = Effect(name="Test Effect", attribute="strength", change=5)
    created_effect = effect_repo.create(effect)
    assert created_effect is not None
    assert created_effect.id is not None
    assert created_effect.name == effect.name
    assert created_effect.attribute == effect.attribute
    assert created_effect.change == effect.change

def test_delete(effect_repo: EffectRepository):
    effect = Effect(name="Delete Effect", attribute="intelligence", change=2)
    created_effect = effect_repo.create(effect)
    assert created_effect is not None
    deleted = effect_repo.delete(created_effect.id)
    assert deleted is True
    fetched_effect = effect_repo.get(created_effect.id)
    assert fetched_effect is None

def test_get(effect_repo: EffectRepository):
    effect = Effect(name="Get Effect", attribute="agility", change=-3)
    created_effect = effect_repo.create(effect)
    fetched_effect = effect_repo.get(created_effect.id)
    assert fetched_effect is not None
    assert fetched_effect.id == created_effect.id
    assert fetched_effect.name == created_effect.name
    assert fetched_effect.attribute == created_effect.attribute
    assert fetched_effect.change == created_effect.change

def test_list(effect_repo: EffectRepository):
    effect1 = Effect(name="List Effect 1", attribute="charisma", change=4)
    effect2 = Effect(name="List Effect 2", attribute="wisdom", change=-1)
    effect_repo.create(effect1)
    effect_repo.create(effect2)
    effects = effect_repo.list()
    assert len(effects) >= 2
    names = [e.name for e in effects]
    assert "List Effect 1" in names
    assert "List Effect 2" in names

def test_update(effect_repo: EffectRepository):
    effect = Effect(name="Update Effect", attribute="luck", change=0)
    created_effect = effect_repo.create(effect)
    updated_data = Effect(name="Updated Effect", attribute="luck", change=10)
    update_ok = effect_repo.update(created_effect.id, updated_data)
    assert update_ok is True
    fetched_effect = effect_repo.get(created_effect.id)
    assert fetched_effect is not None
    assert fetched_effect.name == "Updated Effect"
    assert fetched_effect.change == 10
    