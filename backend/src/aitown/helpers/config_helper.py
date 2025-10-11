from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict, Optional

from .path_helper import CONFIG_PATH


def _load_toml(fp: Path) -> Dict[str, Any]:
    with fp.open("rb") as f:
        return tomllib.load(f)


_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def _ensure_loaded() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    cfgp = CONFIG_PATH
    if not cfgp.exists():
        raise FileNotFoundError(f"Config file not found: {cfgp}")
    cfg = _load_toml(cfgp)
    if not isinstance(cfg, dict):
        # normalize to dict
        cfg = dict(cfg)
    _CONFIG_CACHE = cfg
    return _CONFIG_CACHE


def get_config(section: Optional[str] = None) -> Dict[str, Any]:
    """Return the configuration as a dict or a specific section.

    Args:
        section: Optional section name to return. If None, returns the full config dict.

    Returns:
        dict: configuration mapping (or sub-dictionary for the section).

    Raises:
        FileNotFoundError: if the config file cannot be found.
        KeyError: if the requested section does not exist in the config.
    """
    cfg = _ensure_loaded()
    if section is None:
        return cfg
    try:
        val = cfg[section]
    except KeyError:
        raise KeyError(f"Configuration section not found: {section}")
    # Ensure we return a dict-like structure for sections
    if not isinstance(val, dict):
        # return the raw value wrapped in a dict under its name for consistency
        return {section: val}
    return val
