"""Fixed, three-valued IV rules and chronological reporting policies."""
from __future__ import annotations

import numpy as np
import pandas as pd

EPS = 1e-12
RULES = ("S4", "F4", "sign4", "sign_falling4")
OUTCOMES = ("target_first", "adverse_first", "neither", "ambiguous")


def classify(m: np.ndarray, a: np.ndarray, b2: np.ndarray, rule: str,
             breadth: int = 4) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Classify bounded counts; sign controls retain the same scored-source eligibility."""
    if m.ndim != 2 or m.shape != a.shape or m.shape != b2.shape:
        raise ValueError("Expected identical event-by-instrument arrays")
    if rule not in RULES or not 1 <= breadth <= m.shape[1]:
        raise ValueError("Invalid rule or breadth")
    if any(np.isinf(x).any() for x in (m, a, b2)):
        raise ValueError("Infinite measurement")
    known = np.isfinite(m)
    if rule.startswith("sign"):
        known &= np.isfinite(a)
        yes = known & (a < 0)
        no = known & (a >= 0)
    else:
        yes = known & (m > 1)
        no = known & (m <= 1)
    if rule in ("F4", "sign_falling4"):
        yes &= np.isfinite(b2) & (b2 < -EPS)
        no |= np.isfinite(b2) & (b2 >= -EPS)
    count, missing = yes.sum(axis=1), (~(yes | no)).sum(axis=1)
    state = np.where(count >= breadth, "yes",
                     np.where(count + missing < breadth, "no", "unknown"))
    return state, count, missing


def or_states(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Three-valued union without relabeling unobserved votes as negative."""
    if a.shape != b.shape or not np.isin(a, ["yes", "no", "unknown"]).all() \
            or not np.isin(b, ["yes", "no", "unknown"]).all():
        raise ValueError("Invalid state arrays")
    return np.where((a == "yes") | (b == "yes"), "yes",
                    np.where((a == "no") & (b == "no"), "no", "unknown"))


def endpoint_join(events: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """Join exact T−1 only; absent observations remain absent."""
    if scores.duplicated(["date", "end_min"]).any():
        raise ValueError("Duplicate instrument endpoint")
    keys = events.copy()
    keys["end_min"] = keys.known_min - 1
    return keys.merge(scores, on=["date", "end_min"], how="left", validate="many_to_one")


def thin(frame: pd.DataFrame, mode: str) -> pd.DataFrame:
    """Apply a within-parent, within-date chronological execution policy."""
    if "variant" in frame and frame.variant.nunique() > 1:
        raise ValueError("Thin each parent separately")
    rows = frame.sort_values(["date", "known_min"], kind="stable")
    if mode == "all":
        return rows
    if mode == "first":
        return rows.drop_duplicates("date")
    if mode != "spaced60":
        raise ValueError(mode)
    keep, prior = [], {}
    for row in rows.itertuples():
        if row.known_min >= prior.get(row.date, -10000) + 60:
            keep.append(row.Index)
            prior[row.date] = row.known_min
    return rows.loc[keep]


def describe(frame: pd.DataFrame) -> dict:
    """Count the fixed first-touch outcomes, retaining every category in N."""
    if not frame.outcome.isin(OUTCOMES).all():
        raise ValueError("Unknown outcome")
    c = frame.outcome.value_counts()
    n, wins = len(frame), int(c.get("target_first", 0))
    return dict(n=n, targets=wins, days=int(frame.date.nunique()),
                rate=100 * wins / n if n else np.nan,
                **{name: int(c.get(name, 0)) for name in OUTCOMES[1:]})


def within_blocks(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return all stratum support and equal-block daily yes-minus-no contrasts."""
    records = []
    for (date, block), group in frame.groupby(["date", "block"], sort=True):
        yes, no = group[group.state.eq("yes")], group[group.state.eq("no")]
        both = bool(len(yes) and len(no))
        records.append(dict(date=date, block=block, yes_n=len(yes), no_n=len(no),
                            unknown_n=int(group.state.eq("unknown").sum()), both=both,
                            delta=100 * (yes.hit.mean() - no.hit.mean()) if both else np.nan))
    detail = pd.DataFrame(records, columns=["date", "block", "yes_n", "no_n",
                                           "unknown_n", "both", "delta"])
    detail["both"] = detail.both.astype(bool)
    daily = detail[detail.both].groupby("date").agg(delta=("delta", "mean"),
                                                   blocks=("block", "size")).reset_index()
    return detail, daily
