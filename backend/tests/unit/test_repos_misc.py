from aitown.repos import base as repos_base
from aitown.repos import interfaces as repos_interfaces


def test_base_json_helpers():
    s = repos_base.to_json_text({"x": 1})
    assert isinstance(s, str)
    assert repos_base.from_json_text(None) is None
    assert repos_base.from_json_text("not json") == "not json"


def test_interfaces_imported():
    # Ensure interfaces module is imported and contains expected classes
    assert hasattr(repos_interfaces, "NPCRepositoryInterface")
    assert hasattr(repos_interfaces, "PlayerRepositoryInterface")
