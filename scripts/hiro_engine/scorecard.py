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
    df = log[(log["mode"] == mode) & (log["tier"] == "full")].copy()   # R9 is a
    # full-rule exam: price-tier rows can never enter the scorecard
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
    if hashes and hashes[0] != cfg.config_hash:
        print("!" * 78)
        print(f"!! WARNING: grading sessions of hash {hashes[0][:12]}… but the CURRENT "
              f"config hash is {cfg.config_hash[:12]}… — a config edit resets the R9 test")
        print("!" * 78)
    sess = sessions[sessions["mode"] == mode]
    countable = set(sess[sess.disposition == "countable"].date)
    dispo = dict(zip(sess.date, sess.disposition))
    df["disposition"] = df.session_date.map(dispo)
    df = df[df.session_date.isin(countable)]
    if not len(df):
        raise ScorecardError("no countable sessions (dispositions: "
                             + str(sorted(set(dispo.values()))) + ")")
    return df


def one_leg_violations(rows: pd.DataFrame) -> int:
    """R9 'one leg at a time': count entries appearing while a trade is open,
    scanning the append-ordered log per session."""
    v = 0
    for _, g in rows.groupby("session_date", sort=False):
        open_trade = False
        for r in g.itertuples():
            if r.event_type == "entry":
                if open_trade:
                    v += 1
                open_trade = True
            elif r.event_type == "exit":
                open_trade = False
    return v


def stage2_entries(rows: pd.DataFrame) -> pd.DataFrame:
    entries = rows[rows.event_type == "entry"]
    exits = rows[rows.event_type == "exit"]
    recs = []
    for r in entries.itertuples():
        x = exits[(exits.session_date == r.session_date) & (exits.trade_id == r.trade_id)]
        x = x.iloc[0] if len(x) else None
        def _f(row, col):
            v = getattr(row, col, None)
            return float(v) if row is not None and pd.notna(v) else None
        recs.append(dict(
            date=r.session_date, trade_id=int(r.trade_id), branch=r.branch, side=r.side,
            signal_min=int(r.signal_min), entry_min=int(r.entry_min), s0=float(r.s0),
            episode=int(r.episode) if pd.notna(r.episode) else None,
            k1=_f(r, "k1"), k2=_f(r, "k2"), leg1_fill=_f(r, "leg1_fill"),
            limit_price=_f(r, "limit_price"),
            exit_type=(x.outcome_type if x is not None else None),
            exit_ref=_f(x, "exit_ref"), minutes=_f(x, "outcome_minutes"),
            adverse=_f(x, "adverse"),
            credit=_f(x, "credit"), pnl_usd=_f(x, "pnl_usd"),
            leg_liq_loss_usd=_f(x, "leg_liq_loss_usd"),
            data_invalid=bool(getattr(x, "data_invalid", False))
                if x is not None and pd.notna(getattr(x, "data_invalid", None)) else False))
    df = pd.DataFrame(recs)
    if len(df):
        df["pnl"] = np.where(df.side == "sell_first", df.exit_ref - df.s0, df.s0 - df.exit_ref)
    return df


def stage3_qualify(rows: pd.DataFrame) -> pd.DataFrame:
    ev = rows[rows.event_type.isin(["signal", "skip", "late_no_entry"])].copy()
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
    """v3 (R9): pure RESTING-LIMIT replay from the pinned chain cache over the
    ORIGINAL 60-min horizon, no other R7 exits; single invalid minutes are
    skipped; a >= 5-consecutive-minute gap -> None (INDETERMINATE, reported
    separately, never guessed)."""
    if tr.limit_price is None or tr.k2 is None:
        return None
    from .chains import ChainError, ChainStore
    try:
        cd = ChainStore().load(tr.date)
    except ChainError:
        return None
    clock = cfg.i("r5_clock", "clock_minutes")
    gap_limit = cfg.i("r1v3_limits", "quote_gap_invalid_after")
    first = int(tr.signal_min) + cfg.i("r1v3_limits", "first_eligible_offset")
    buy = tr.side == "sell_first"
    gap = 0
    for m in range(first, int(tr.entry_min) + clock + 1):
        q = cd.quote(m, tr.k2)
        if q is None or not q.valid:
            gap += 1
            if gap >= gap_limit:
                return None
            continue
        gap = 0
        if (q.ask <= tr.limit_price) if buy else (q.bid >= tr.limit_price):
            return True
    return False


def stage4_metrics(cfg: Config, entries: pd.DataFrame) -> dict:
    """v3: economic $ metrics (R11.3). data_invalid trades stay in entry counts
    (handled in stage6) but leave fills/rates/risk here."""
    m: dict = {"warnings": []}
    if len(entries) and "data_invalid" not in entries.columns:
        entries = entries.assign(data_invalid=False)
    scored = entries[~entries.data_invalid.fillna(False)] if len(entries) else entries
    for br in ("A", "B", "ALL"):
        e = scored if br == "ALL" else scored[scored.branch == br]
        fills = e[e.exit_type == "fill"]
        denom = e[e.exit_type != "censored"]
        m[f"{br}_entries"] = len(entries if br == "ALL" else entries[entries.branch == br])
        m[f"{br}_fills"] = len(fills)
        m[f"{br}_fill_rate"] = len(fills) / len(denom) if len(denom) else float("nan")
        m[f"{br}_censored"] = int((e.exit_type == "censored").sum())
    m["data_invalid_n"] = int(entries.data_invalid.fillna(False).sum()) if len(entries) else 0
    scr = scored[scored.exit_type == "scratch"] if len(scored) else scored
    m["median_scratch_loss_usd"] = float((-scr.pnl_usd).median()) if len(scr) else float("nan")
    losses = (-scored.pnl_usd).clip(lower=0) if len(scored) else pd.Series(dtype=float)
    m["max_single_trade_loss_usd"] = float(losses.max()) if len(losses) else 0.0
    m["credits_usd"] = float(scored[scored.exit_type == "fill"].pnl_usd.sum())         if len(scored) else 0.0
    m["realized_pnl_usd"] = float(scored.pnl_usd.sum()) if len(scored) else 0.0
    whf, indet = [], 0
    for tr in scr.itertuples():
        r = _would_have_filled(cfg, tr)
        if r is None:
            indet += 1
        elif r:
            whf.append(tr.date)
    m["would_have_filled_scratches"] = len(whf)
    m["would_have_filled_indeterminate"] = indet
    return m


def stage5_controls(cfg: Config, entries: pd.DataFrame) -> dict:
    """v3: limit-fill controls from the PINNED derived frame (R11.4/R11.5)."""
    from .control import clock_matched_v3, load_control_frame, midpoint_matched_v3
    frame = load_control_frame(cfg)      # verifies the frame pin (R8.2)
    out = {}
    b = entries[entries.branch == "B"]
    a = entries[entries.branch == "A"]
    out["B_control"] = clock_matched_v3(cfg, b.signal_min, frame) if len(b) else float("nan")
    out["A_control"] = midpoint_matched_v3(cfg, a.signal_min, frame) if len(a) else float("nan")
    return out


def _best_session(entries: pd.DataFrame) -> Optional[str]:
    """best = most fills; ties -> highest summed pnl; ties -> earliest date (R9)."""
    if not len(entries):
        return None
    g = entries.groupby("date").agg(
        fills=("exit_type", lambda s: (s == "fill").sum()),
        pnl=("pnl_usd", "sum")).reset_index()
    g = g.sort_values(["fills", "pnl", "date"], ascending=[False, False, True])
    return str(g.iloc[0].date)


def _r9_thresholds(cfg: Config) -> Optional[dict]:
    """Registered thresholds from CONFIG (populated at task 18); None = pending."""
    try:
        t = cfg.section("r9_thresholds")
        return t if t else None
    except Exception:
        return None


def stage6_criteria(cfg: Config, sessions_countable: list[str], entries: pd.DataFrame,
                    qualify: pd.DataFrame, metrics: dict, controls: dict) -> pd.DataFrame:
    n_sess = len(sessions_countable)
    rows = []
    th = _r9_thresholds(cfg)
    pending = th is None

    def crit(name, measured, threshold, ok, inconclusive=False):
        status = ("PENDING (R9a unregistered)" if pending and "«16b»" in str(threshold)
                  else "INCONCLUSIVE" if inconclusive
                  else ("PASS" if ok else "FAIL"))
        rows.append(dict(criterion=name, measured=measured, threshold=threshold,
                         status=status))

    def _t(key, default_marker="«16b»"):
        return (th[key] if th and key in th else default_marker)

    q_days = qualify.groupby("date").size() if len(qualify) else pd.Series(dtype=int)
    crit("qualifying signals on >=7/10 sessions", f"{(q_days > 0).sum()}/{n_sess}",
         ">=7 of 10", (q_days > 0).sum() >= 7)
    e_per_day = entries.groupby("date").size() if len(entries) else pd.Series(dtype=int)
    d13 = int(((e_per_day >= 1) & (e_per_day <= 3)).sum())
    crit("1-3 executable entries on >=6/10 sessions", f"{d13}/{n_sess}", ">=6 of 10", d13 >= 6)
    fills_by_day = (entries[entries.exit_type == "fill"].groupby("date").size()
                    if len(entries) else pd.Series(dtype=int))
    ft = _t("fills_total_floor")
    crit("limit fills total", metrics["ALL_fills"], f">={ft}",
         isinstance(ft, int) and metrics["ALL_fills"] >= ft)
    sf = _t("sessions_with_fill_floor")
    crit("sessions with >=1 fill", f"{(fills_by_day > 0).sum()}/{n_sess}", f">={sf} of 10",
         isinstance(sf, int) and (fills_by_day > 0).sum() >= sf)
    max_per_day = int(e_per_day.max()) if len(e_per_day) else 0
    crit("<=3 entries/session", max_per_day, "<=3", max_per_day <= 3)
    crit("one leg at a time", metrics.get("one_leg_violations", 0),
         "0 overlapping entries", metrics.get("one_leg_violations", 0) == 0)

    qb = int((qualify.branch == "B").sum()) if len(qualify) else 0
    b_inc = qb < 20
    crit("Branch B qualifying signals", qb, ">=20 (else INCONCLUSIVE)", qb >= 20,
         inconclusive=b_inc)
    bf = _t("b_fill_rate_floor")
    crit("Branch B fill rate", round(metrics["B_fill_rate"], 3) if metrics["B_fill_rate"] == metrics["B_fill_rate"] else "n/a",
         f">={bf}", (isinstance(bf, float) or isinstance(bf, int))
         and metrics["B_fill_rate"] >= float(bf) if not b_inc and not pending else False,
         inconclusive=b_inc)
    crit("Branch B vs clock-matched control",
         f"{metrics['B_fill_rate']:.3f} vs {controls['B_control']:.3f}"
         if metrics["B_fill_rate"] == metrics["B_fill_rate"] else "n/a",
         "not below control",
         metrics["B_fill_rate"] >= controls["B_control"] if not b_inc else False,
         inconclusive=b_inc)
    qa = int((qualify.branch == "A").sum()) if len(qualify) else 0
    a_inc = qa < 8
    crit("Branch A qualifying episodes", qa, ">=8 (else INCONCLUSIVE)", qa >= 8,
         inconclusive=a_inc)
    af = _t("a_fill_rate_floor")
    crit("Branch A fill rate", round(metrics["A_fill_rate"], 3) if metrics["A_fill_rate"] == metrics["A_fill_rate"] else "n/a",
         f">={af}", (isinstance(af, float) or isinstance(af, int))
         and metrics["A_fill_rate"] >= float(af) if not a_inc and not pending else False,
         inconclusive=a_inc)
    crit("Branch A vs midpoint-matched control (+10pp)",
         f"{metrics['A_fill_rate']:.3f} vs {controls['A_control']:.3f}"
         if metrics["A_fill_rate"] == metrics["A_fill_rate"] else "n/a",
         ">= control + 0.10",
         (metrics["A_fill_rate"] >= controls["A_control"] + 0.10) if not a_inc else False,
         inconclusive=a_inc)

    ml = _t("max_single_trade_loss_usd")
    crit("max single-trade realized loss ($)", f"${metrics['max_single_trade_loss_usd']:,.0f}",
         f"<=${ml}", isinstance(ml, int) and metrics["max_single_trade_loss_usd"] <= ml)
    msl = metrics["median_scratch_loss_usd"]
    mc = _t("median_scratch_loss_cap_usd")
    crit("median scratch loss ($)", f"${msl:,.0f}" if msl == msl else "no scratches",
         f"<=${mc}", (isinstance(mc, int) and msl <= mc) if msl == msl else True)
    crit("would-have-filled scratches (limit replay)",
         f"{metrics['would_have_filled_scratches']}"
         + (f" (+{metrics['would_have_filled_indeterminate']} indeterminate)"
            if metrics.get("would_have_filled_indeterminate") else ""),
         "<=1", metrics["would_have_filled_scratches"] <= 1)
    crit("data_invalid trades (reported, unscored)", metrics.get("data_invalid_n", 0),
         "report only", True)

    # RISK RE-CHECK: best session removed, thresholds unchanged, denominators reduced
    best = _best_session(entries)
    if best is not None:
        e2 = entries[entries.date != best]
        m2 = stage4_metrics(cfg, e2)
        crit(f"re-check (drop {best}): max single loss ($)",
             f"${m2['max_single_trade_loss_usd']:,.0f}", f"<=${ml}",
             isinstance(ml, int) and m2["max_single_trade_loss_usd"] <= ml)
        msl2 = m2["median_scratch_loss_usd"]
        crit(f"re-check (drop {best}): median scratch loss ($)",
             f"${msl2:,.0f}" if msl2 == msl2 else "no scratches", f"<=${mc}",
             (isinstance(mc, int) and msl2 <= mc) if msl2 == msl2 else True)
        crit(f"re-check (drop {best}): would-have-filled scratches",
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
        if rehearsal:
            sessions_path = sessions_path.with_name("sessions_backtest.csv")
    if outdir is None:
        outdir = _p("paper_log").parent / ("scorecard_rehearsal" if rehearsal else "scorecard")
    outdir.mkdir(parents=True, exist_ok=True)
    label = "REHEARSAL" if rehearsal else "LIVE"
    if not rehearsal and _r9_thresholds(cfg) is None:
        print("scorecard LIVE: REFUSED — R9 thresholds are not registered "
              "(r9a pending, task 18). Rehearsal grading is allowed.")
        return 1
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
    metrics["one_leg_violations"] = one_leg_violations(rows)
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
