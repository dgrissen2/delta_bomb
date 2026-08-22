"""Scorecard (R9/R11) — a staged pipeline; each stage writes its frame so any
number in the R9 table can be traced to rows (design.md).

Stages: 1 filter -> 2 entries -> 3 qualify -> 4 metrics -> 5 controls -> 6 criteria.
Interpretation notes (build_notes.md): R6.3-suppressed episodes are NOT
qualifying (R11.1 exempts only R4/R6.4 blocks); control weighting uses SIGNAL
minutes (research convention: outcomes measured from the next bar's open).
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .config import REPO_ROOT, Config
from .control import build_control_frame, clock_matched, midpoint_matched
from .feeds import FeedError, load_spx_day

FILL_QUALIFY_EXCLUDE = ("A beats B", "HIRO down")


class ScorecardError(Exception):
    pass


def _read_log(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ScorecardError(f"log not found: {path}")
    return pd.read_csv(path, dtype={"session_date": str})


def _read_sessions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["date", "disposition", "outage_min", "mode", "config_hash"])
    return pd.read_csv(path, dtype={"date": str})


# ---------------------------------------------------------------------------
def stage1_filter(cfg: Config, log: pd.DataFrame, sessions: pd.DataFrame,
                  rehearsal: bool, d_from: Optional[str], d_to: Optional[str]) -> pd.DataFrame:
    mode = "backtest" if rehearsal else "live"
    df = log[log["mode"] == mode].copy()
    if d_from:
        df = df[df.session_date >= d_from]
    if d_to:
        df = df[df.session_date <= d_to]
    if not len(df):
        raise ScorecardError(f"no {mode} rows to grade")
    hashes = sorted(df.config_hash.dropna().unique())
    if len(hashes) > 1:
        raise ScorecardError(
            "refusing to combine sessions with different CONFIG_HASHes (R9 reset rule): "
            + ", ".join(h[:12] + "…" for h in hashes))
    sess = sessions[sessions["mode"] == mode]
    countable = set(sess[sess.disposition == "countable"].date)
    dispo = dict(zip(sess.date, sess.disposition))
    df["disposition"] = df.session_date.map(dispo)
    df = df[df.session_date.isin(countable)]
    if not len(df):
        raise ScorecardError("no countable sessions (dispositions: "
                             + str(sorted(set(dispo.values()))) + ")")
    return df


def stage2_entries(rows: pd.DataFrame) -> pd.DataFrame:
    entries = rows[rows.event_type == "entry"]
    exits = rows[rows.event_type == "exit"]
    recs = []
    for r in entries.itertuples():
        x = exits[(exits.session_date == r.session_date) & (exits.trade_id == r.trade_id)]
        x = x.iloc[0] if len(x) else None
        recs.append(dict(
            date=r.session_date, trade_id=int(r.trade_id), branch=r.branch, side=r.side,
            signal_min=int(r.signal_min), entry_min=int(r.entry_min), s0=float(r.s0),
            episode=int(r.episode) if pd.notna(r.episode) else None,
            exit_type=(x.outcome_type if x is not None else None),
            exit_ref=(float(x.exit_ref) if x is not None and pd.notna(x.exit_ref) else None),
            minutes=(float(x.outcome_minutes) if x is not None and pd.notna(x.outcome_minutes) else None),
            adverse=(float(x.adverse) if x is not None and pd.notna(x.adverse) else None)))
    df = pd.DataFrame(recs)
    if len(df):
        df["pnl"] = np.where(df.side == "sell_first", df.exit_ref - df.s0, df.s0 - df.exit_ref)
    return df


def stage3_qualify(rows: pd.DataFrame) -> pd.DataFrame:
    ev = rows[rows.event_type.isin(["signal", "skip"])].copy()
    keep = []
    for r in ev.itertuples():
        notes = str(r.notes or "")
        if r.event_type == "skip" and any(x in notes for x in FILL_QUALIFY_EXCLUDE):
            continue
        if pd.isna(r.episode) or r.branch not in ("A", "B"):
            continue
        keep.append(dict(date=r.session_date, branch=r.branch, episode=int(r.episode),
                         min=int(r.signal_min) if pd.notna(r.signal_min) else None,
                         via=r.event_type))
    q = pd.DataFrame(keep)
    if len(q):
        q = q.sort_values(["date", "branch", "episode"]).drop_duplicates(
            ["date", "branch", "episode"])
    return q


def _would_have_filled(cfg: Config, tr) -> Optional[bool]:
    """Deterministic re-check from stored SPX: would the fill touch have printed
    within the 60-min horizon absent the scratch?"""
    try:
        spx = load_spx_day(cfg.path_of("spx_dir"), tr.date)
    except FeedError:
        return None
    fill = cfg.num("r1_instruments", "fill_touch_pts")
    clock = cfg.i("r5_clock", "clock_minutes")
    seg = spx[(spx["min"] >= tr.entry_min) & (spx["min"] < tr.entry_min + clock)]
    if tr.side == "sell_first":
        return bool((seg.high >= tr.s0 + fill).any())
    return bool((seg.low <= tr.s0 - fill).any())


def stage4_metrics(cfg: Config, entries: pd.DataFrame) -> dict:
    m: dict = {"warnings": []}
    for br in ("A", "B", "ALL"):
        e = entries if br == "ALL" else entries[entries.branch == br]
        fills = e[e.exit_type == "fill"]
        noncens = e[e.exit_type != "censored"]
        m[f"{br}_entries"] = len(e)
        m[f"{br}_fills"] = len(fills)
        m[f"{br}_fill_rate"] = len(fills) / len(noncens) if len(noncens) else float("nan")
        m[f"{br}_censored"] = int((e.exit_type == "censored").sum())
    scr = entries[entries.exit_type == "scratch"]
    m["scratch_losses"] = sorted((-scr.pnl).tolist()) if len(scr) else []
    m["median_scratch_loss"] = float(np.median(-scr.pnl)) if len(scr) else float("nan")
    whf = []
    for tr in scr.itertuples():
        r = _would_have_filled(cfg, tr)
        if r is None:
            m["warnings"].append(f"no stored SPX for {tr.date} — would-have-filled unknown")
        elif r:
            whf.append(tr.date)
    m["would_have_filled_scratches"] = len(whf)
    adv = entries[entries.adverse.notna()]
    m["adverse_gt10_n"] = int((adv.adverse > 10).sum())
    m["adverse_gt10_frac"] = float((adv.adverse > 10).mean()) if len(adv) else float("nan")
    return m


def stage5_controls(cfg: Config, entries: pd.DataFrame) -> dict:
    frame = build_control_frame(cfg)     # verifies the data hash (R8.2)
    out = {}
    b = entries[entries.branch == "B"]
    a = entries[entries.branch == "A"]
    out["B_control"] = clock_matched(cfg, b.signal_min, frame) if len(b) else float("nan")
    out["A_control"] = midpoint_matched(cfg, a.signal_min, frame) if len(a) else float("nan")
    return out


def _best_session(entries: pd.DataFrame) -> Optional[str]:
    """best = most fills; ties -> highest summed pnl; ties -> earliest date (R9)."""
    if not len(entries):
        return None
    g = entries.groupby("date").agg(
        fills=("exit_type", lambda s: (s == "fill").sum()),
        pnl=("pnl", "sum")).reset_index()
    g = g.sort_values(["fills", "pnl", "date"], ascending=[False, False, True])
    return str(g.iloc[0].date)


def stage6_criteria(cfg: Config, sessions_countable: list[str], entries: pd.DataFrame,
                    qualify: pd.DataFrame, metrics: dict, controls: dict) -> pd.DataFrame:
    n_sess = len(sessions_countable)
    rows = []

    def crit(name, measured, threshold, ok, inconclusive=False):
        rows.append(dict(criterion=name, measured=measured, threshold=threshold,
                         status="INCONCLUSIVE" if inconclusive
                         else ("PASS" if ok else "FAIL")))

    q_days = qualify.groupby("date").size() if len(qualify) else pd.Series(dtype=int)
    crit("qualifying signals on >=7/10 sessions", f"{(q_days > 0).sum()}/{n_sess}",
         ">=7 of 10", (q_days > 0).sum() >= 7)
    e_per_day = entries.groupby("date").size() if len(entries) else pd.Series(dtype=int)
    d13 = int(((e_per_day >= 1) & (e_per_day <= 3)).sum())
    crit("1-3 executable entries on >=6/10 sessions", f"{d13}/{n_sess}", ">=6 of 10", d13 >= 6)
    fills_by_day = (entries[entries.exit_type == "fill"].groupby("date").size()
                    if len(entries) else pd.Series(dtype=int))
    crit(">=8 fills total", metrics["ALL_fills"], ">=8", metrics["ALL_fills"] >= 8)
    crit(">=1 fill on 6/10 sessions", f"{(fills_by_day > 0).sum()}/{n_sess}", ">=6 of 10",
         (fills_by_day > 0).sum() >= 6)
    max_per_day = int(e_per_day.max()) if len(e_per_day) else 0
    crit("<=3 entries/session", max_per_day, "<=3", max_per_day <= 3)

    qb = int((qualify.branch == "B").sum()) if len(qualify) else 0
    b_inc = qb < 20
    crit("Branch B qualifying signals", qb, ">=20 (else INCONCLUSIVE)", qb >= 20,
         inconclusive=False)
    crit("Branch B fill rate", round(metrics["B_fill_rate"], 3) if metrics["B_fill_rate"] == metrics["B_fill_rate"] else "n/a",
         ">=0.45", metrics["B_fill_rate"] >= 0.45 if not b_inc else False, inconclusive=b_inc)
    crit("Branch B vs clock-matched control",
         f"{metrics['B_fill_rate']:.3f} vs {controls['B_control']:.3f}"
         if metrics["B_fill_rate"] == metrics["B_fill_rate"] else "n/a",
         "not below control",
         metrics["B_fill_rate"] >= controls["B_control"] if not b_inc else False,
         inconclusive=b_inc)
    qa = int((qualify.branch == "A").sum()) if len(qualify) else 0
    a_inc = qa < 8
    crit("Branch A qualifying episodes", qa, ">=8 (else INCONCLUSIVE)", qa >= 8)
    crit("Branch A fill rate", round(metrics["A_fill_rate"], 3) if metrics["A_fill_rate"] == metrics["A_fill_rate"] else "n/a",
         ">=0.70", metrics["A_fill_rate"] >= 0.70 if not a_inc else False, inconclusive=a_inc)
    crit("Branch A vs midpoint-matched control (+10pp)",
         f"{metrics['A_fill_rate']:.3f} vs {controls['A_control']:.3f}"
         if metrics["A_fill_rate"] == metrics["A_fill_rate"] else "n/a",
         ">= control + 0.10",
         (metrics["A_fill_rate"] >= controls["A_control"] + 0.10) if not a_inc else False,
         inconclusive=a_inc)

    frac = metrics["adverse_gt10_frac"]
    crit("adverse > 10 pts", f"{metrics['adverse_gt10_n']} trades "
         f"({frac:.1%})" if frac == frac else "0", "<=10% and <=1 trade",
         (metrics["adverse_gt10_n"] <= 1)
         and (frac <= 0.10 if frac == frac else True))
    msl = metrics["median_scratch_loss"]
    crit("median scratch loss", round(msl, 2) if msl == msl else "no scratches",
         "<=3 pts", (msl <= 3.0) if msl == msl else True)
    crit("would-have-completed scratches", metrics["would_have_filled_scratches"],
         "<=1", metrics["would_have_filled_scratches"] <= 1)

    # RISK RE-CHECK: best session removed, thresholds unchanged, denominators reduced
    best = _best_session(entries)
    if best is not None:
        e2 = entries[entries.date != best]
        m2 = stage4_metrics(cfg, e2)
        f2 = m2["adverse_gt10_frac"]
        crit(f"re-check (drop {best}): adverse > 10 pts",
             f"{m2['adverse_gt10_n']} ({f2:.1%})" if f2 == f2 else "0",
             "<=10% and <=1 trade",
             m2["adverse_gt10_n"] <= 1 and (f2 <= 0.10 if f2 == f2 else True))
        msl2 = m2["median_scratch_loss"]
        crit(f"re-check (drop {best}): median scratch loss",
             round(msl2, 2) if msl2 == msl2 else "no scratches", "<=3 pts",
             (msl2 <= 3.0) if msl2 == msl2 else True)
        crit(f"re-check (drop {best}): would-have-completed scratches",
             m2["would_have_filled_scratches"], "<=1",
             m2["would_have_filled_scratches"] <= 1)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def run_scorecard(cfg: Config, rehearsal: bool = False,
                  d_from: Optional[str] = None, d_to: Optional[str] = None,
                  log_path: Optional[Path] = None,
                  sessions_path: Optional[Path] = None,
                  outdir: Optional[Path] = None) -> int:
    def _p(key):
        q = Path(cfg.get("logging", key))
        return q if q.is_absolute() else REPO_ROOT / q
    if log_path is None:
        log_path = (_p("paper_log").with_name("paper_log_backtest.csv") if rehearsal
                    else _p("paper_log"))
    if sessions_path is None:
        sessions_path = _p("sessions_log")
    if outdir is None:
        outdir = _p("paper_log").parent / ("scorecard_rehearsal" if rehearsal else "scorecard")
    outdir.mkdir(parents=True, exist_ok=True)
    label = "REHEARSAL" if rehearsal else "LIVE"
    try:
        rows = stage1_filter(cfg, _read_log(log_path), _read_sessions(sessions_path),
                             rehearsal, d_from, d_to)
    except ScorecardError as e:
        print(f"scorecard {label}: {e}")
        return 1
    rows.to_csv(outdir / "stage1_rows.csv", index=False)
    entries = stage2_entries(rows)
    entries.to_csv(outdir / "stage2_entries.csv", index=False)
    qualify = stage3_qualify(rows)
    qualify.to_csv(outdir / "stage3_qualify.csv", index=False)
    metrics = stage4_metrics(cfg, entries)
    pd.DataFrame([{k: v for k, v in metrics.items() if not isinstance(v, list)}]).to_csv(
        outdir / "stage4_metrics.csv", index=False)
    controls = stage5_controls(cfg, entries)
    pd.DataFrame([controls]).to_csv(outdir / "stage5_controls.csv", index=False)
    days = sorted(rows.session_date.unique())
    table = stage6_criteria(cfg, days, entries, qualify, metrics, controls)
    table.to_csv(outdir / "stage6_criteria.csv", index=False)

    print(f"\n=== SCORECARD [{label}] — CONFIG_HASH {rows.config_hash.iloc[0][:12]}… ===")
    print(f"countable sessions: {len(days)}/10 " + ("(test incomplete)" if len(days) < 10 else ""))
    for w in metrics["warnings"]:
        print("  WARNING:", w)
    with pd.option_context("display.width", 200, "display.max_colwidth", 60):
        print(table.to_string(index=False))
    statuses = set(table.status)
    if len(days) < 10 and not rehearsal:
        verdict = f"IN PROGRESS ({len(days)}/10 sessions)"
    elif "FAIL" in statuses:
        verdict = "FAIL"
    elif "INCONCLUSIVE" in statuses:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS"
    print(f"\nOVERALL: {verdict}")
    print(f"stage frames written to {outdir}/")
    return 0
