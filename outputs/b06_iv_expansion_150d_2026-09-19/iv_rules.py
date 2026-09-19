"""Typed adapter to the exact previously executed and committed IV rule functions.

The experiment archive is trusted local research source. Extract only its three
pure calculation functions; never execute its historical main body or outcomes.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ARCHIVE = Path(__file__).resolve().parent.parent / 'b06_iv_recovery_findings_2026-09-19/evidence.json'
SOURCE = json.loads(ARCHIVE.read_text())['experiment_source']
SOURCE_SHA256 = hashlib.sha256(SOURCE.encode()).hexdigest()
NAMES = {'add_quality', 'make_surface', 'guard_tests'}
functions = [node for node in ast.parse(SOURCE).body
             if isinstance(node, ast.FunctionDef) and node.name in NAMES]
if {node.name for node in functions} != NAMES:
    raise ValueError('Missing frozen IV rule function')
scope: dict[str, Any] = {'np': np, 'pd': pd}
exec(compile(ast.Module(body=functions, type_ignores=[]), str(ARCHIVE), 'exec'), scope)


def add_quality(frame: pd.DataFrame) -> pd.DataFrame:
    return scope['add_quality'](frame)


def make_surface(frame: pd.DataFrame, valid_column: str,
                 grid: pd.DatetimeIndex) -> tuple[pd.DataFrame, pd.DataFrame]:
    return scope['make_surface'](frame, valid_column, grid)


def check_guard_boundaries() -> int:
    return scope['guard_tests']()


def classify(known: int, missing: int) -> str:
    """Keep the frozen eleven-sector denominator and explicit unknown state."""
    if known < 0 or missing < 0 or known + missing > 11:
        raise ValueError('Invalid eleven-sector counts')
    return 'yes' if known >= 6 else 'no' if known + missing < 6 else 'unknown'


def slopes(values: np.ndarray) -> tuple[float, float, float]:
    """Require all thirty actual samples for both slopes and acceleration."""
    if len(values) != 30:
        raise ValueError('Exactly thirty samples required')
    if not np.isfinite(values).all():
        return np.nan, np.nan, np.nan
    weights = np.arange(15) - 7
    first = float(np.dot(weights, values[:15]) / 280)
    second = float(np.dot(weights, values[15:]) / 280)
    return first, second, (second - first) / 15
