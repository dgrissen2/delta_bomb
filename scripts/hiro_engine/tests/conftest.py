"""Shared fixtures for hiro_engine tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# make `hiro_engine` importable when pytest runs from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # helpers.py

from hiro_engine.config import load_config  # noqa: E402


@pytest.fixture(scope="session")
def config():
    return load_config()
