"""Fixed causal rules and simple execution/accounting helpers."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/dgrissen/Dev/central_trade_data/thetadata")
PRIOR = ROOT / "mad_transfer_spx_2026-09-20-v1"
OLD = ROOT / "branch_b_iv_full_2024_2026_2026-09-19-v1"
DATA = ROOT / "b09_opportunity_expansion_2026-09-20-v1"
OUT = Path(__file__).resolve().parent
SPY = ROOT.parent / "databento/spy_ohlcv_1m/spy_ohlcv_1m.parquet"
REGISTRY = (
    OUT.parent / "sector_iv_mad_remaining_2025_2026_2026-09-19/all_sector_sources.json"
)
SYMBOLS = sorted("XLB XLC XLE XLF XLI XLK XLP XLRE XLU XLV XLY".split())
OUTCOMES = ["target_first", "adverse_first", "neither", "ambiguous"]
HALVES = ["2025_H1", "2025_H2", "2026_H1", "2026_H2"]
EPS = 1e-12


def digest(path: Path) -> str:
    """Hash a source without loading its interpretation."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def write_json(path: Path, content: dict) -> None:
    path.write_text(json.dumps(content, indent=2, allow_nan=False) + "\n")


def persistence(m: np.ndarray, b: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Require synchronous historic votes and the same currently falling names.

    Arrays are events × five ascending endpoints × instruments. Finite current
    M is source eligibility, not a requirement for current M to exceed one.
    """
    if m.shape != b.shape or m.ndim != 3 or m.shape[1] != 5 or not 1 <= k <= m.shape[2]:
        raise ValueError("Invalid persistence dimensions")
    if np.isinf(m).any() or np.isinf(b).any():
        raise ValueError("Infinite input")
    cm, cb = m[:, -1:, :], b[:, -1:, :]
    yes = np.isfinite(m) & (m > 1) & np.isfinite(b) & (b < -EPS)
    yes &= np.isfinite(cm) & np.isfinite(cb) & (cb < -EPS)
    no = (np.isfinite(m) & (m <= 1)) | (np.isfinite(b) & (b >= -EPS))
    no |= np.isfinite(cb) & (cb >= -EPS)
    votes, unknown = yes.sum(axis=2), (~(yes | no)).sum(axis=2)
    qualified = votes >= k
    state = np.where(
        qualified.any(axis=1),
        "yes",
        np.where(((votes + unknown) < k).all(axis=1), "no", "unknown"),
    )
    witness = np.where(qualified.any(axis=1), qualified.argmax(axis=1), -1)
    return state, witness


def either(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return np.where(
        (a == "yes") | (b == "yes"),
        "yes",
        np.where((a == "no") & (b == "no"), "no", "unknown"),
    )


def rvol(
    windows: pd.DataFrame, date: str | int, minute: int
) -> tuple[float, float, str]:
    """Use exactly 60 previous session dates and a complete current five-bar sum."""
    if date not in windows.index or minute - 1 not in windows.columns:
        return np.nan, np.nan, "current_unavailable"
    pos = windows.index.get_loc(date)
    if pos < 60:
        return np.nan, np.nan, "insufficient_history"
    now = windows.loc[date, minute - 1]
    if not np.isfinite(now):
        return np.nan, np.nan, "current_incomplete"
    history = windows.iloc[pos - 60 : pos][minute - 1].to_numpy()
    if not np.isfinite(history).all():
        return np.nan, np.nan, "incomplete_history"
    reference = float(np.median(history))
    if reference <= 0:
        return np.nan, reference, "nonpositive_reference"
    return float(now / reference), reference, "ok"


def unique(frame: pd.DataFrame) -> pd.DataFrame:
    """Deduplicate executions, failing if cross-parent outcome/price disagree."""
    for c in ["outcome", "entry_price"]:
        if (
            c in frame
            and frame.groupby(["date", "known_min"])[c]
            .nunique(dropna=False)
            .gt(1)
            .any()
        ):
            raise ValueError(f"Conflicting duplicate {c}")
    return (
        frame.sort_values(["date", "known_min"], kind="stable")
        .drop_duplicates(["date", "known_min"])
        .copy()
    )


def thin(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    rows = unique(frame)
    if policy == "all":
        return rows
    if policy == "first":
        return rows.drop_duplicates("date")
    if policy != "spaced60":
        raise ValueError(policy)
    last, keep = {}, []
    for r in rows.itertuples():
        if r.known_min >= last.get(r.date, -10000) + 60:
            last[r.date] = r.known_min
            keep.append(r.Index)
    return rows.loc[keep]


def describe(frame: pd.DataFrame) -> dict:
    if not frame.outcome.isin(OUTCOMES).all():
        raise ValueError("Invalid outcome")
    counts = frame.outcome.value_counts()
    n = len(frame)
    return {
        "n": n,
        "days": frame.date.nunique(),
        "rate": 100 * counts.get("target_first", 0) / n if n else np.nan,
        **{c: int(counts.get(c, 0)) for c in OUTCOMES},
    }


def keys(frame: pd.DataFrame) -> set[tuple[str, int]]:
    return set(zip(frame.date, frame.known_min, strict=True))


def difference(frame: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    other = keys(reference)
    return frame.loc[
        [k not in other for k in zip(frame.date, frame.known_min, strict=True)]
    ]
