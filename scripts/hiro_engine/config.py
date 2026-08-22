"""Frozen config loader (R8.2). Fail closed: a missing key raises, no defaults."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PKG_DIR = Path(__file__).resolve().parent
REPO_ROOT = PKG_DIR.parent.parent          # scripts/hiro_engine -> repo root
DEFAULT_CONFIG = PKG_DIR / "config.yaml"


class ConfigError(Exception):
    """Raised when the frozen config is missing or malformed (fail closed)."""


def _expand(p: str) -> Path:
    q = Path(os.path.expanduser(str(p)))
    return q if q.is_absolute() else REPO_ROOT / q


@dataclass(frozen=True)
class Config:
    """The frozen thresholds file, loaded verbatim. CONFIG_HASH = sha256 of the yaml bytes."""

    raw: dict[str, Any]
    config_hash: str
    path: Path

    def section(self, name: str) -> dict[str, Any]:
        if name not in self.raw:
            raise ConfigError(f"config section missing: {name!r} (fail closed, no defaults)")
        return self.raw[name]

    def get(self, section: str, key: str) -> Any:
        sec = self.section(section)
        if key not in sec:
            raise ConfigError(f"config key missing: {section}.{key} (fail closed, no defaults)")
        return sec[key]

    # -- typed accessors used across the engine ------------------------------
    def num(self, section: str, key: str) -> float:
        return float(self.get(section, key))

    def i(self, section: str, key: str) -> int:
        return int(self.get(section, key))

    def path_of(self, key: str) -> Path:
        return _expand(self.get("data", key))

    @property
    def control_days(self) -> list[str]:
        return list(self.get("control_dataset", "days"))

    @property
    def control_data_hash(self) -> str:
        return str(self.get("control_dataset", "data_hash"))

    @property
    def verification_artifact(self) -> Path:
        return _expand(self.get("verification", "artifact"))

    @property
    def verification_hash(self) -> str:
        return str(self.get("verification", "artifact_hash"))


REQUIRED_SECTIONS = [
    "r1_instruments", "r3_derived", "r4_vetoes", "r5_clock", "r6_entries",
    "r7_exits", "data", "control_dataset", "verification", "logging",
]


def load_config(path: str | Path | None = None) -> Config:
    p = Path(path) if path is not None else DEFAULT_CONFIG
    if not p.exists():
        raise ConfigError(f"config file not found: {p}")
    data = p.read_bytes()
    raw = yaml.safe_load(data)
    if not isinstance(raw, dict):
        raise ConfigError(f"config is not a mapping: {p}")
    for sec in REQUIRED_SECTIONS:
        if sec not in raw:
            raise ConfigError(f"config section missing: {sec!r} (fail closed, no defaults)")
    return Config(raw=raw, config_hash=hashlib.sha256(data).hexdigest(), path=p)
