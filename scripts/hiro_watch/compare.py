"""hiro_watch W4/W5 — the accounting: candidate logs laid beside the baseline log.

    python hiro_watch/compare.py [--asof YYYY-MM-DD] [--no-marks] [--debug]

Pure pandas over the engine-written event logs. Prints, per candidate: trades/fills/cash per branch
split DISCOVERY | CONFIRMATION (W4.1), the book (W4.2), the candidate-specific detail (W4.3), and
the verdict against the frozen bars (W5.3) — printed only at a checkpoint or on an immediate
REJECT path (W5.2).
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hiro_engine.models import EVENT_FIELDS                    # noqa: E402  read-only library use of v1
from hiro_engine.register import DRAWS, SEED                    # noqa: E402  W4.4: same bootstrap as R9a
from hiro_watch.registry import BASELINE_DIR, Candidate, baseline_data, candidates   # noqa: E402

V1_LOGS = [BASELINE_DIR / "paper_log_backtest.csv"] + sorted(
    Path(p) for p in glob.glob(str(BASELINE_DIR / "paper_log_oos_*.csv")))
V1_SESSIONS = BASELINE_DIR / "sessions_backtest.csv"
MARKS_DIR = Path("~/Dev/central_trade_data/thetadata/spxw_marks").expanduser()   # fetched data lives in the store
USD = 100.0                                                    # SPX option multiplier
CLOSE_MIN = 960                                                # 16:00 ET in minutes
log = logging.getLogger("hiro_watch.compare")

# W5 — frozen with requirements.md v2.1 (2026-09-04; v2.0's $150 per-trade line removed). Change = new requirements version.
CHECKPOINTS = (10, 20, 30, 40)
TERMINAL = CHECKPOINTS[-1]
BARS = dict(
    a_depth=dict(theta=-4.0, signals=20, signal_days=10, passed=10, passed_days=5, day_share=0.25,
                 lb95=0.55, expire_signals=40),
    credit=dict(A=dict(fills=15), B=dict(entries=10, fills=5)),
    diag=dict(episodes=20),
)
THETAS = (-1.0, -2.0, -3.0, -4.0, -5.0)
NUM = ["s0", "k1", "k2", "leg1_fill", "leg2_fill", "pnl_usd", "leg_liq_loss_usd", "outcome_minutes",
       "signal_min", "entry_min", "episode", "trade_id", "r15", "credit"]
SETUP = ["session_date", "branch", "episode"]      # one entry per (day, branch, episode) — R11.1; stable across candidates


# ---- loading -----------------------------------------------------------------------
def load_log(paths: list[Path], expect_hash: str | None = None) -> pd.DataFrame:
    frames = []
    for p in paths:
        if not p.exists():
            raise SystemExit(f"REFUSED: log missing {p}")
        frames.append(pd.read_csv(p, dtype=str, keep_default_na=False))
    ev = pd.concat(frames, ignore_index=True)
    if list(ev.columns) != EVENT_FIELDS:
        raise SystemExit(f"REFUSED: {paths[0]} columns != EVENT_FIELDS")
    banners = ev[(ev.event_type == "banner") & (ev.rule_id == "R8.2")].session_date.value_counts()
    if (banners > 1).any():
        raise SystemExit(f"REFUSED: duplicate sessions in {[p.name for p in paths]}: "
                         f"{banners[banners > 1].index.tolist()} (W0.3 — rebuild the candidate)")
    hashes = set(ev.config_hash.unique())
    if expect_hash is not None and hashes != {expect_hash}:
        raise SystemExit(f"REFUSED: {paths[0]} carries config_hash {sorted(h[:12] for h in hashes)} but the yaml "
                         f"hashes to {expect_hash[:12]} — the yaml changed after the log was written (W0)")
    for c in NUM:
        ev[c] = pd.to_numeric(ev[c], errors="coerce")
    for c in ("signal_min", "entry_min", "episode", "trade_id"):
        ev[c] = ev[c].astype("Int64")
    return ev


def load_sessions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"REFUSED: sessions file missing {path}")
    s = pd.read_csv(path, dtype=str)[["date", "disposition"]]
    if s.date.duplicated().any():
        raise SystemExit(f"REFUSED: duplicate dates in {path}: {s[s.date.duplicated()].date.tolist()}")
    return s


# ---- tables -------------------------------------------------------------------------
def trades(ev: pd.DataFrame) -> pd.DataFrame:
    """One row per trade: entry fields + exit outcome. bomb = both legs filled (outcome 'fill')."""
    en = ev[ev.event_type == "entry"][["session_date", "trade_id", "branch", "side", "signal_min", "entry_min",
                                       "episode", "k1", "k2", "expiry", "leg1_fill"]]
    ex = ev[ev.event_type == "exit"][["session_date", "trade_id", "leg2_fill", "outcome_type", "outcome_minutes",
                                      "pnl_usd", "leg_liq_loss_usd"]]
    t = en.merge(ex, on=["session_date", "trade_id"], how="left", validate="one_to_one")
    if t.outcome_type.isna().any():
        raise SystemExit(f"REFUSED: entries without an exit: {t[t.outcome_type.isna()][SETUP].values.tolist()}")
    if t.duplicated(SETUP).any():
        raise SystemExit(f"REFUSED: two entries for one setup: {t[t.duplicated(SETUP)][SETUP].values.tolist()}")
    t["bomb"] = t.outcome_type == "fill"
    t["mae"] = -t.leg_liq_loss_usd.fillna(0.0)
    t["k_long"], t["k_short"] = t[["k1", "k2"]].max(axis=1), t[["k1", "k2"]].min(axis=1)
    return t.reset_index(drop=True)


def signals(ev: pd.DataFrame) -> pd.DataFrame:
    """One row per baseline signal (first signal minute of the setup); r30 parsed from the A note."""
    s = ev[ev.event_type == "signal"][SETUP + ["signal_min", "r15", "notes"]].copy()
    s["r30"] = pd.to_numeric(s.notes.str.extract(r"r30=(-?\d+\.\d+)")[0], errors="coerce")
    s = s.sort_values("signal_min").drop_duplicates(SETUP, keep="first")
    return s.drop(columns=["notes"]).reset_index(drop=True)


REFUSAL = [("late_no_entry", None, "late"), ("skip", "short blocked: vt_broken", "vt_broken"),
           ("skip", "short blocked: levels_invalid", "levels_invalid"),
           ("skip", "short blocked: flow_veto", "flow_veto"),
           ("skip", "entries/day", "capacity"), ("skip", "one unpaired leg", "capacity")]


def refusals(ev: pd.DataFrame) -> pd.DataFrame:
    """One row per (setup, reason). A setup can carry several reasons (e.g. late AND vt_broken)."""
    rows = ev[ev.event_type.isin(["skip", "late_no_entry"])].copy()
    rows["reason"] = ""
    for et, needle, reason in REFUSAL:
        m = (rows.event_type == et) & (rows.notes.str.contains(needle, regex=False) if needle else True)
        rows.loc[m, "reason"] = reason
    rows = rows[rows.reason != ""]
    return rows[SETUP + ["reason"]].drop_duplicates().reset_index(drop=True)


def confirmation_dates(base_sess: pd.DataFrame, registered: str) -> list[str]:
    """Countable sessions strictly after the registration date, capped at the terminal checkpoint (W5.1/W5.2)."""
    d = base_sess[(base_sess.disposition == "countable") & (base_sess.date > registered)].date.sort_values()
    return d.tolist()[:TERMINAL]


def label(dates: pd.Series, registered: str, conf: list[str]) -> pd.Series:
    """DISCOVERY (<= registered) | CONFIRMATION (countable, within the first 40) | EXCLUDED (after registered, not countable or post-terminal)."""
    return pd.Series(np.where(dates <= registered, "DISCOVERY",
                              np.where(dates.isin(conf), "CONFIRMATION", "EXCLUDED")), index=dates.index)


# ---- book (W4.2) --------------------------------------------------------------------
class MarkCache:
    """Closing quotes for (date, expiry): pulled once through v1's chain client, cached as parquet in the store."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._frames: dict[tuple[str, str], pd.DataFrame | None] = {}
        MARKS_DIR.mkdir(parents=True, exist_ok=True)

    def frame(self, date: str, expiry: str) -> pd.DataFrame | None:
        key = (date, expiry)
        if key in self._frames:
            return self._frames[key]
        p = MARKS_DIR / f"{date}_{expiry}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
        elif not self.enabled:
            df = None
        else:
            from hiro_engine.chains import _sdk_pull_day            # read-only library use of v1
            log.info("pulling marks %s exp %s", date, expiry)
            df = _sdk_pull_day(date, dt.date.fromisoformat(expiry))
            if not len(df) or int(df["min"].max()) < CLOSE_MIN - 5:
                raise SystemExit(f"REFUSED: chain pull {date} exp {expiry} is empty or stops before the close "
                                 f"(last minute {df['min'].max() if len(df) else None}) — not cached; rerun after 16:00 ET")
            df.to_parquet(p, index=False)
        self._frames[key] = df
        return df

    def close_mid(self, date: str, expiry: str, strike: float) -> float | None:
        f = self.frame(date, expiry)
        if f is None:
            return None
        q = f[(f.strike == strike) & (f["min"] <= CLOSE_MIN) & (f.bid > 0) & (f.ask > 0) & (f.ask >= f.bid)]
        if not len(q):
            return None
        last = q.sort_values("min").iloc[-1]
        return float((last.bid + last.ask) / 2)


def spx_close(date: str, spx_dir: Path, require_complete: bool = True) -> float:
    """Last regular-hours SPX 1-min close of `date`. require_complete refuses a session whose bars stop
    before 16:00 (used for `asof`); settlement passes False because an expiry can be a half day."""
    p = spx_dir / f"{date}.parquet"
    if not p.exists():
        raise SystemExit(f"REFUSED: SPX bars for {date} missing: {p}")
    d = pd.read_parquet(p)
    if not len(d):
        raise SystemExit(f"REFUSED: SPX bars for {date} are empty: {p}")
    if require_complete and int(d["min"].max()) < CLOSE_MIN:
        raise SystemExit(f"REFUSED: SPX bars for {date} stop at minute {int(d['min'].max())} — session incomplete")
    return float(d[d["min"] <= CLOSE_MIN].sort_values("min").close.iloc[-1])


def book(t: pd.DataFrame, asof: str, marks: MarkCache, spx_dir: Path) -> dict:
    """cash + marks on open bombs + settled payoffs on expired bombs = MTM, for trades up to `asof`.
    bomb = long k_long / short k_short put."""
    t = t[t.session_date <= asof]
    rows, unmarked = [], []
    for _, b in t[t.bomb].iterrows():
        width = b.k_long - b.k_short
        base = dict(session_date=b.session_date, branch=b.branch, k_long=b.k_long, k_short=b.k_short, expiry=b.expiry)
        if b.expiry <= asof:
            s = spx_close(b.expiry, spx_dir, require_complete=False)
            rows.append(dict(base, state="SETTLED", value_usd=(max(0.0, b.k_long - s) - max(0.0, b.k_short - s)) * USD,
                             spx_settle=s))
        else:
            ml, ms = marks.close_mid(asof, b.expiry, b.k_long), marks.close_mid(asof, b.expiry, b.k_short)
            if ml is None or ms is None:
                unmarked.append(f"{b.session_date} {b.branch} {b.k_long:.0f}/{b.k_short:.0f} exp {b.expiry}")
                rows.append(dict(base, state="UNMARKED", value_usd=np.nan, spx_settle=np.nan))
            else:
                rows.append(dict(base, state="MARKED", value_usd=min(ml - ms, width) * USD, spx_settle=np.nan))
    inv = pd.DataFrame(rows, columns=["session_date", "branch", "k_long", "k_short", "expiry", "state", "value_usd", "spx_settle"])
    cash = float(t.pnl_usd.sum())
    inventory = float(inv.value_usd.sum()) if len(inv) else 0.0
    return dict(cash=cash, inventory=inventory, mtm=cash + inventory, n_bombs=len(inv), unmarked=unmarked, table=inv)


# ---- statistics (W4.4) --------------------------------------------------------------
def per_session(t: pd.DataFrame, sessions: list[str]) -> pd.DataFrame:
    """fills / trades per session over ALL given sessions (zero-trade sessions included in the resampling unit)."""
    g = t.groupby("session_date").agg(fills=("bomb", "sum"), n=("bomb", "size"))
    g = g.reindex(sessions, fill_value=0).reset_index().rename(columns={"index": "session_date"})
    return g


def lb95(fills_by_session: pd.DataFrame) -> float:
    """min(session-bootstrap 5th percentile, Clopper-Pearson lower bound) of the pooled fill rate."""
    n, k = int(fills_by_session.n.sum()), int(fills_by_session.fills.sum())
    if n == 0:
        return 0.0
    cp = float(beta.ppf(0.05, k, n - k + 1)) if k > 0 else 0.0
    rng = np.random.default_rng(SEED)
    f, m = fills_by_session.fills.to_numpy(), fills_by_session.n.to_numpy()
    idx = rng.integers(0, len(f), size=(DRAWS, len(f)))
    draws_n = m[idx].sum(axis=1)
    rates = f[idx].sum(axis=1)[draws_n > 0] / draws_n[draws_n > 0]
    boot = float(np.quantile(rates, 0.05)) if len(rates) else 0.0
    return min(boot, cp)


def checkpoint(n_conf: int) -> bool:
    return n_conf in CHECKPOINTS


# ---- verdicts (W5.3): every function takes CONFIRMATION-only frames and books; returns (text, immediate) ----
def verdict_a_depth(bt: pd.DataFrame, bsig: pd.DataFrame, ct: pd.DataFrame, cb: dict, bb: dict,
                    cbA: dict, bbA: dict, conf: list[str]) -> tuple[str, bool]:
    """bt/bsig: baseline confirmation trades/signals; ct: candidate confirmation trades.
    cb/bb: confirmation whole-portfolio books (MTM terms — the gate's capacity spill into B is part of
    the candidate); cbA/bbA: confirmation A-only books (expectancy terms).
    Scored cohort = candidate A trades whose setup is a PASSED baseline signal (r30 < θ at the
    baseline's first signal minute); candidate A trades outside it are reported, never scored."""
    B = BARS["a_depth"]
    sig = bsig[bsig.branch == "A"]
    passed = sig[sig.r30 < B["theta"]]
    ctA, btA = ct[ct.branch == "A"], bt[bt.branch == "A"]
    ctP = passed[SETUP].merge(ctA, on=SETUP, how="inner")
    stray = len(ctA) - len(ctP)
    note = f" [{stray} candidate A trade(s) outside the passed cohort, unscored]" if stray else ""
    expired = len(sig) >= B["expire_signals"]
    counts_ok = (len(sig) >= B["signals"] and sig.session_date.nunique() >= B["signal_days"]
                 and len(passed) >= B["passed"] and passed.session_date.nunique() >= B["passed_days"]
                 and (passed.session_date.value_counts().max() / max(len(passed), 1)) <= B["day_share"])

    def tail(text: str) -> tuple[str, bool]:        # every non-PROMOTE/REJECT outcome past the budget expires
        if expired:
            return f"REJECT-EXPIRED — {len(sig)} confirmation A signals without PROMOTE or REJECT ({text})", False
        return text, False

    if not counts_ok:
        return tail(f"INCONCLUSIVE — A signals {len(sig)}/{B['signals']} over {sig.session_date.nunique()}/{B['signal_days']} days; "
                    f"passed {len(passed)}/{B['passed']} over {passed.session_date.nunique()}/{B['passed_days']} days{note}")
    if cb["unmarked"] or bb["unmarked"] or cbA["unmarked"] or bbA["unmarked"]:
        return tail(f"DEFERRED — unmarked bombs: {sorted(set(cb['unmarked'] + bb['unmarked']))}")
    lb = lb95(per_session(ctP, conf))
    exp_c = (ctP.pnl_usd.sum() + cbA["inventory"]) / max(len(passed), 1)
    exp_b = (btA.pnl_usd.sum() + bbA["inventory"]) / max(len(sig), 1)
    credits = float(ctP[ctP.bomb].pnl_usd.sum())
    if lb <= B["lb95"]:
        return f"REJECT — passed completion LB95 {lb:.2f} <= {B['lb95']}{note}", False
    if exp_c <= exp_b:
        return f"REJECT — passed expectancy {exp_c:+.0f}/signal <= baseline {exp_b:+.0f}/signal{note}", False
    if cb["mtm"] < bb["mtm"] - credits:
        return f"REJECT — candidate MTM {cb['mtm']:+.0f} < baseline {bb['mtm']:+.0f} − credits {credits:.0f}{note}", False
    if cb["mtm"] < bb["mtm"]:
        return tail(f"INCONCLUSIVE — candidate MTM {cb['mtm']:+.0f} < baseline {bb['mtm']:+.0f}{note}")
    return (f"PROMOTE — LB95 {lb:.2f}, expectancy {exp_c:+.0f} vs {exp_b:+.0f}/signal, "
            f"MTM {cb['mtm']:+.0f} vs {bb['mtm']:+.0f}{note}"), False


def lost_fills(bt: pd.DataFrame, ct: pd.DataFrame, branch: str) -> pd.DataFrame:
    """Baseline bombs of `branch` whose setup did not complete in the candidate run."""
    b = bt[bt.bomb & (bt.branch == branch)].merge(ct[SETUP + ["bomb"]], on=SETUP, how="left", suffixes=("", "_c"))
    return b[~b.bomb_c.fillna(False).astype(bool)]


def verdict_credit(bt: pd.DataFrame, ct: pd.DataFrame, branch: str, cb: dict, bb: dict) -> tuple[str, bool]:
    """bt/ct: confirmation trades; cb/bb: confirmation-only, branch-only books (W1: read per branch)."""
    B = BARS["credit"]
    btB, ctB = bt[bt.branch == branch], ct[ct.branch == branch]
    lost = lost_fills(bt, ct, branch)
    if len(lost):
        return f"REJECT ({branch}) — {len(lost)} baseline fill(s) lost at 0.30: {lost[SETUP].values.tolist()}", True
    need = B[branch]
    if branch == "A":
        counts_ok = int(btB.bomb.sum()) >= need["fills"]
        progress = f"baseline A fills {int(btB.bomb.sum())}/{need['fills']}"
    else:
        counts_ok = len(btB) >= need["entries"] and int(btB.bomb.sum()) >= need["fills"]
        progress = f"B entries {len(btB)}/{need['entries']}, baseline B fills {int(btB.bomb.sum())}/{need['fills']}"
    if not counts_ok:
        return f"INCONCLUSIVE ({branch}) — {progress}", False
    if cb["unmarked"] or bb["unmarked"]:
        return f"DEFERRED ({branch}) — unmarked bombs: {cb['unmarked'] + bb['unmarked']}", False
    if ctB.pnl_usd.sum() < btB.pnl_usd.sum():
        return f"REJECT ({branch}) — net cash {ctB.pnl_usd.sum():+.0f} < baseline {btB.pnl_usd.sum():+.0f}", False
    if cb["mtm"] < bb["mtm"]:
        return f"INCONCLUSIVE ({branch}) — MTM {cb['mtm']:+.0f} < baseline {bb['mtm']:+.0f}", False
    return (f"PROMOTE ({branch}) — zero fills lost, cash {ctB.pnl_usd.sum():+.0f} vs {btB.pnl_usd.sum():+.0f}, "
            f"MTM {cb['mtm']:+.0f} vs {bb['mtm']:+.0f}"), False


def diag_table(base_ref: pd.DataFrame, base_t: pd.DataFrame, cand_ref: pd.DataFrame, cand_t: pd.DataFrame,
               reason: str) -> pd.DataFrame:
    """Sole-blocker attribution (W4.3): a baseline setup refused for `reason` — and never entered by the
    baseline later in the episode — is scored only if the diag run entered it. `other_reasons` = the
    other refusals the setup carried in the baseline log OR in the diag run's own log (the engine logs
    one short-block reason per setup, so a second veto shows up only in the diag run)."""
    r = base_ref[base_ref.reason == reason][SETUP].drop_duplicates()
    r = r.merge(base_t[SETUP], on=SETUP, how="left", indicator=True)
    r = r[r._merge == "left_only"].drop(columns="_merge")            # baseline entered it later → not refused
    pool = pd.concat([base_ref[base_ref.reason != reason], cand_ref[cand_ref.reason != reason]])
    others = (pool.groupby(SETUP).reason.apply(lambda x: ",".join(sorted(set(x))))
              .rename("other_reasons").reset_index())
    j = r.merge(others, on=SETUP, how="left").merge(
        cand_t[SETUP + ["bomb", "pnl_usd", "mae", "outcome_type", "set"]], on=SETUP, how="left")
    j["other_reasons"] = j.other_reasons.fillna("")
    j["scored"] = j.outcome_type.notna()
    return j


DIAG_REASON = {"diag_vt_off": "vt_broken", "diag_levels_off": "levels_invalid", "diag_late_off": "late"}


# ---- report -------------------------------------------------------------------------
def _split(t: pd.DataFrame) -> str:
    lines = []
    for s in ("DISCOVERY", "CONFIRMATION", "EXCLUDED"):
        for br in ("A", "B"):
            x = t[(t.set == s) & (t.branch == br)]
            if not len(x):
                if s != "EXCLUDED":
                    lines.append(f"    {s:<12} {br}  —")
                continue
            med = x[x.bomb].outcome_minutes.median() if x.bomb.any() else float("nan")
            lines.append(f"    {s:<12} {br}  trades {len(x):>2}  bombs {int(x.bomb.sum()):>2}  rate {x.bomb.mean():.2f}  "
                         f"cash {x.pnl_usd.sum():+7.0f}  worst {x.pnl_usd.min():+5.0f}  MAE {x.mae.min():+5.0f}  "
                         f"fill-min med {med:.0f}")
    return "\n".join(lines)


def _books(t: pd.DataFrame, bt: pd.DataFrame, asof: str, marks: MarkCache, spx_dir: Path, branch: str | None = None) -> tuple[dict, dict]:
    sel = lambda df: df[(df.set == "CONFIRMATION") & ((df.branch == branch) if branch else True)]   # noqa: E731
    return book(sel(t), asof, marks, spx_dir), book(sel(bt), asof, marks, spx_dir)


def report_candidate(c: Candidate, base_ev: pd.DataFrame, base_sess: pd.DataFrame, asof: str, marks: MarkCache, spx_dir: Path) -> None:
    ev = load_log([c.paper_log], expect_hash=c.config_hash)
    sess = load_sessions(c.sessions)
    missing = sorted(set(base_sess.date) - set(sess.date))
    if missing:
        raise SystemExit(f"REFUSED: {c.name} lacks sessions {missing} (W0.3 — run.py them)")
    extra = sorted(set(sess.date) - set(base_sess.date))
    if extra:
        raise SystemExit(f"REFUSED: {c.name} has sessions the baseline lacks {extra} (W0.3 — rebuild it)")
    conf = confirmation_dates(base_sess, c.registered)
    n_conf = len(conf)
    asof_v = conf[-1] if n_conf >= TERMINAL else asof          # W5.2: the 40-session verdict stands
    t, bt, bsig, bref, cref = trades(ev), trades(base_ev), signals(base_ev), refusals(base_ev), refusals(ev)
    for df in (t, bt, bsig, bref, cref):
        df["set"] = label(df.session_date, c.registered, conf)
    cb_all, bb_all = book(t, asof, marks, spx_dir), book(bt, asof, marks, spx_dir)
    nxt = next((k for k in CHECKPOINTS if k > n_conf), TERMINAL)
    print(f"\n### {c.name}  [{c.kind}, {c.engine}, {c.config_hash[:12]}…]  {c.change}")
    print(f"  registered {c.registered} | countable confirmation sessions {n_conf} | "
          f"{'CHECKPOINT' if checkpoint(n_conf) else f'next checkpoint at {nxt}'}{' (TERMINAL)' if n_conf >= TERMINAL else ''}")
    print("  candidate:"); print(_split(t))
    print("  baseline: "); print(_split(bt))
    print(f"  book, all sessions (asof {asof}): cash {cb_all['cash']:+.0f} + inventory {cb_all['inventory']:+.0f} "
          f"({cb_all['n_bombs']} bombs) = MTM {cb_all['mtm']:+.0f}   | baseline MTM {bb_all['mtm']:+.0f} ({bb_all['n_bombs']} bombs)"
          + (f"   UNMARKED {len(cb_all['unmarked'])}: {cb_all['unmarked'][:3]}{'…' if len(cb_all['unmarked']) > 3 else ''}"
             if cb_all["unmarked"] else ""))
    conf_t, conf_bt = t[t.set == "CONFIRMATION"], bt[bt.set == "CONFIRMATION"]
    if c.name == "a_depth_m4":
        a = bsig[bsig.branch == "A"].merge(bt[SETUP + ["bomb", "pnl_usd"]], on=SETUP, how="left")
        print("  Θ ladder over baseline A signals that entered (bomb rate | n):")
        for th in THETAS:
            cells = []
            for s in ("DISCOVERY", "CONFIRMATION"):
                x = a[(a.set == s) & (a.r30 < th) & a.bomb.notna()]
                cells.append(f"{s[:4]} {x.bomb.mean() if len(x) else float('nan'):.2f}|{len(x):>2}")
            print(f"    θ {th:+.0f}  " + "   ".join(cells))
        cb, bb = _books(t, bt, asof_v, marks, spx_dir)
        cbA, bbA = _books(t, bt, asof_v, marks, spx_dir, branch="A")
        verdicts = [verdict_a_depth(conf_bt, bsig[bsig.set == "CONFIRMATION"], conf_t, cb, bb, cbA, bbA, conf)]
    elif c.name == "credit030":
        verdicts = []
        for br in ("A", "B"):
            for s in ("DISCOVERY", "CONFIRMATION"):
                lost = lost_fills(bt[bt.set == s], t, br)
                print(f"  {br} {s:<12} baseline fills {int(bt[(bt.set == s) & (bt.branch == br)].bomb.sum()):>2}, "
                      f"lost at 0.30: {len(lost)}" + (f" {lost[SETUP].values.tolist()}" if len(lost) else ""))
            cb, bb = _books(t, bt, asof_v, marks, spx_dir, branch=br)
            verdicts.append(verdict_credit(conf_bt, conf_t, br, cb, bb))
    elif c.kind == "diagnostic":
        if c.name not in DIAG_REASON:
            raise SystemExit(f"REFUSED: diagnostic {c.name} has no refusal reason mapped in compare.py")
        d = diag_table(bref, bt, cref, t, DIAG_REASON[c.name])
        d["set"] = label(d.session_date, c.registered, conf) if len(d) else d.set
        for s in ("DISCOVERY", "CONFIRMATION"):
            x = d[d.set == s]
            sc = x[x.scored]
            print(f"  {s:<12} refused({DIAG_REASON[c.name]}): {len(x)} episodes ({int((x.other_reasons != '').sum())} also "
                  f"blocked otherwise), entered when rule off: {len(sc)}, bombs {int(sc.bomb.sum())}, "
                  f"cash {sc.pnl_usd.sum():+.0f}, worst {sc.pnl_usd.min() if len(sc) else 0:+.0f}, "
                  f"share MAE<-150: {(sc.mae < -150).mean() if len(sc) else 0:.2f}")
        n_ep = int((d.set == "CONFIRMATION").sum()) if len(d) else 0
        verdicts = [(f"INCONCLUSIVE — {n_ep}/{BARS['diag']['episodes']} confirmation refused episodes [never promoted]"
                     if n_ep < BARS["diag"]["episodes"] else "REPORTED (diagnostic, never promoted)", False)]
    elif c.kind == "control":
        verdicts = [("control — no verdict", False)]
    else:
        raise SystemExit(f"REFUSED: promotable candidate {c.name} has no verdict function in compare.py")
    for text, immediate in verdicts:
        if checkpoint(n_conf) or immediate or c.kind != "promotable":
            print(f"  VERDICT: {text}" + ("  [immediate path]" if immediate and not checkpoint(n_conf) else "")
                  + (f"  [terminal — books pinned at {asof_v}]" if n_conf >= TERMINAL else ""))
        else:
            print(f"  status: INCONCLUSIVE ({n_conf}/{nxt}) — verdicts print at checkpoints only")


def run(asof: str | None, with_marks: bool) -> int:
    cands = candidates()
    data = baseline_data()
    era, spx_dir = str(data["hiro_era_start"]), Path(data["spx_dir"]).expanduser()
    base_ev = load_log(V1_LOGS)
    base_ev = base_ev[base_ev.session_date >= era]                 # v1's log also holds pre-era price-tier days
    base_sess = load_sessions(V1_SESSIONS)
    base_sess = base_sess[base_sess.date >= era]
    asof = asof or base_sess.date.max()
    spx_close(asof, spx_dir)                                        # refuse an incomplete asof session
    marks = MarkCache(enabled=with_marks)
    print(f"hiro_watch compare | baseline v1 {base_ev.config_hash.iloc[0][:12]}… | sessions "
          f"{base_sess.date.min()}..{base_sess.date.max()} | asof {asof} | marks {'on' if with_marks else 'OFF'}")
    for c in cands:
        report_candidate(c, base_ev, base_sess, asof, marks, spx_dir)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hiro_watch/compare.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", default=None, help="mark the book at this session's close (default: latest baseline session)")
    ap.add_argument("--no-marks", action="store_true", help="never pull quotes; unmarked bombs stay UNMARKED")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.debug else logging.INFO, format="%(message)s")
    for noisy in ("thetadata", "httpx", "httpcore"):          # the SDK logs its whole auth payload at INFO
        logging.getLogger(noisy).setLevel(logging.WARNING)
    if a.debug:
        print("[debug on]")
    return run(a.asof, not a.no_marks)


if __name__ == "__main__":
    sys.exit(main())
