from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

CONFIG_PATH = Path("~/.evolva/config.yaml")


def load_config() -> dict[str, Any]:
    """Read ~/.evolva/config.yaml, or an empty config when it does not exist."""
    path = CONFIG_PATH.expanduser()
    if not path.exists():
        return {}

    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def save_config(config: dict[str, Any]) -> None:
    """Write ~/.evolva/config.yaml."""
    path = CONFIG_PATH.expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
