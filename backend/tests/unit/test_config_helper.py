import pytest
from pathlib import Path
from unittest.mock import patch

from aitown.helpers import config_helper, path_helper


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the config cache before each test."""
    config_helper._CONFIG_CACHE = None


def test_load_toml(tmp_path):
    """Test _load_toml function."""
    config_file = tmp_path / "test.toml"
    config_file.write_text("""
[section]
key = "value"
""")
    result = config_helper._load_toml(config_file)
    assert result == {"section": {"key": "value"}}


def test_ensure_loaded_caches_config(tmp_path, monkeypatch):
    """Test that _ensure_loaded caches the config."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("""
[section]
key = "value"
""")
    monkeypatch.setattr(path_helper, "CONFIG_PATH", config_file)
    
    # Mock _load_toml to return the expected dict
    with patch.object(config_helper, '_load_toml', return_value={"section": {"key": "value"}}):
        # First call
        cfg1 = config_helper._ensure_loaded()
        # Second call should return cached
        cfg2 = config_helper._ensure_loaded()
        assert cfg1 is cfg2
        assert cfg1 == {"section": {"key": "value"}}


def test_ensure_loaded_file_not_found(monkeypatch, tmp_path):
    """Test _ensure_loaded raises FileNotFoundError when config file doesn't exist."""
    config_file = tmp_path / "missing.toml"
    monkeypatch.setattr(path_helper, "CONFIG_PATH", config_file)
    
    # Mock Path.exists to return False
    with patch.object(Path, 'exists', return_value=False):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            config_helper._ensure_loaded()


def test_ensure_loaded_normalizes_to_dict(monkeypatch, tmp_path):
    """Test _ensure_loaded normalizes non-dict config to dict."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('key = "value"')
    monkeypatch.setattr(path_helper, "CONFIG_PATH", config_file)
    
    # Mock _load_toml to return a non-dict that can be converted to dict
    with patch.object(config_helper, '_load_toml', return_value=[('key', 'value')]):
        cfg = config_helper._ensure_loaded()
        assert cfg == {'key': 'value'}


def test_get_config_full_config():
    """Test get_config returns full config when no section specified."""
    with patch.object(config_helper, '_ensure_loaded', return_value={"section1": {"key1": "value1"}, "section2": {"key2": "value2"}}):
        cfg = config_helper.get_config()
        assert cfg == {"section1": {"key1": "value1"}, "section2": {"key2": "value2"}}


def test_get_config_specific_section():
    """Test get_config returns specific section."""
    with patch.object(config_helper, '_ensure_loaded', return_value={"section1": {"key1": "value1"}, "section2": {"key2": "value2"}}):
        cfg = config_helper.get_config("section1")
        assert cfg == {"key1": "value1"}


def test_get_config_section_not_found():
    """Test get_config raises KeyError for non-existent section."""
    with patch.object(config_helper, '_ensure_loaded', return_value={"section1": {"key1": "value1"}}):
        with pytest.raises(KeyError, match="Configuration section not found: nonexistent"):
            config_helper.get_config("nonexistent")


def test_get_config_section_not_dict():
    """Test get_config wraps non-dict section value in dict."""
    with patch.object(config_helper, '_ensure_loaded', return_value={"section1": {"key1": "value1"}, "section2": "scalar_value"}):
        cfg = config_helper.get_config("section2")
        assert cfg == {"section2": "scalar_value"}
