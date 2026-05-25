"""Configuration loader for `config/defaults.yaml`.

Caches the parsed YAML in a module-level dict so the file is read once per process.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_PATH = "config/defaults.yaml"


@lru_cache(maxsize=8)
def load_config(path: str = _DEFAULT_PATH) -> dict[str, Any]:
    """Load and cache the YAML config. Subsequent calls return the cached dict."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Configuration at {path} did not parse as a mapping")
    return data


def get_default(key: str, path: str = _DEFAULT_PATH) -> Any:
    """Return a single value from the cached config.

    Raises KeyError naming both the missing key and the config path.
    """
    cfg = load_config(path)
    if key not in cfg:
        raise KeyError(f"Configuration key '{key}' not found in {path}")
    return cfg[key]
