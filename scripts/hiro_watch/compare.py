"""hiro_watch W4/W5 — the accounting: candidate logs laid beside the baseline log.

    python hiro_watch/compare.py [--asof YYYY-MM-DD] [--no-marks] [--debug]

Pure pandas over the engine-written event logs. Prints, per candidate: trades/fills/cash per branch
split DISCOVERY | CONFIRMATION (W4.1), the book (W4.2), the candidate-specific detail (W4.3), and —
only at a checkpoint (W5.2) — the verdict line against the frozen bars (W5.3).
"""
from __future__ import annotations

import argparse
import glob
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import beta

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from hiro_engine.models import EVENT_FIELDS          # noqa: E402  (read-only library use of v1)
from hiro_engine.register import DRAWS, SEED           # noqa: E402  (W4.4: same bootstrap as R9a)

REPO_ROOT = SCRIPTS.parent
CONFIGS = REPO_ROOT / "docs/hiro_watch/configs"
V1_LOGS = [REPO_ROOT / "docs/replay/hiro/paper_log_backtest.csv"] + sorted(
    Path(p) for p in glob.glob(str(REPO_ROOT / "docs/replay/hiro/paper_log_oos_*.csv")))
V1_SESSIONS = REPO_ROOT / "docs/replay/hiro/sessions_backtest.csv"
MARKS_DIR = REPO_ROOT / "docs/replay/hiro_watch/marks"
USD = 100.0                                            # SPX option multiplier
log = logging.getLogger("hiro_watch.compare")

# W5 — frozen with requirements.md v2.0 (2026-09-04). Change = new requirements version.
CHECKPOINTS = (10, 20, 30, 40)
BARS = dict(
    a_depth=dict(signals=20, signal_days=10, passed=10, passed_days=5, day_share=0.25,
                 lb95=0.55, max_loss=-150.0, expire_signals=40),
    credit=dict(A=dict(fills=15), B=dict(entries=10, fills=5), max_loss=-150.0, max_mae=-350.0),
    diag=dict(episodes=20),
)
NUM = ["s0", "k1", "k2", "leg1_fill", "leg2_fill", "pnl_usd", "leg_liq_loss_usd", "outcome_minutes",
       "signal_min", "entry_min", "episode", "trade_id", "r15", "credit"]


# ---- loading -----------------------------------------------------------------------
def candidates() -> list[dict]:
    out = []
    for p in sorted(CONFIGS.glob("*.yaml")):
        raw = yaml.safe_load(p.read_text())
        w = raw["watch"]
        d = REPO_ROOT / Path(raw["logging"]["paper_log"]).parent
        out.append(dict(name=w["name"], engine=w["engine"], kind=w["kind"], registered=str(w["registered"]),
                        change=w["change"], log=d / "paper_log_backtest.csv", sessions=d / "sessions_backtest.csv"))
    return out


def load_log(paths: list[Path]) -> pd.DataFrame:
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
        raise SystemExit(f"REFUSED: duplicate sessions in {paths}: {banners[banners > 1].index.tolist()} "
                         "(W0.3 — rebuild the candidate)")
    for c in NUM:
        ev[c] = pd.to_numeric(ev[c], errors="coerce")
    for c in ("signal_min", "entry_min", "episode", "trade_id"):
        ev[c] = ev[c].astype("Int64")
    return ev


def load_sessions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"REFUSED: sessions file missing {path}")
    return pd.read_csv(path, dtype=str)[["date", "disposition"]]


# ---- tables -------------------------------------------------------------------------
SETUP = ["session_date", "branch", "signal_min", "episode"]


def trades(ev: pd.DataFrame) -> pd.DataFrame:
    """One row per trade: entry fields + exit outcome. bomb = both legs filled (outcome 'fill')."""
    en = ev[ev.event_type == "entry"][["session_date", "trade_id", "branch", "side", "signal_min", "entry_min",
                                       "episode", "k1", "k2", "expiry", "leg1_fill"]]
    ex = ev[ev.event_type == "exit"][["session_date", "trade_id", "leg2_fill", "outcome_type", "outcome_minutes",
                                      "pnl_usd", "leg_liq_loss_usd"]]
    t = en.merge(ex, on=["session_date", "trade_id"], how="left", validate="one_to_one")
    if t.outcome_type.isna().any():
        raise SystemExit(f"REFUSED: entries without an exit: {t[t.outcome_type.isna()][SETUP].values.tolist()}")
    t["bomb"] = t.outcome_type == "fill"
    t["mae"] = -t.leg_liq_loss_usd.fillna(0.0)
    t["k_long"], t["k_short"] = t[["k1", "k2"]].max(axis=1), t[["k1", "k2"]].min(axis=1)
    return t.reset_index(drop=True)


def signals(ev: pd.DataFrame) -> pd.DataFrame:
    s = ev[ev.event_type == "signal"][SETUP + ["r15", "notes"]].copy()
    s["r30"] = pd.to_numeric(s.notes.str.extract(r"r30=(-?\d+\.\d+)")[0], errors="coerce")
    return s.drop(columns=["notes"]).reset_index(drop=True)


REFUSAL = [("late_no_entry", None, "late"), ("skip", "short blocked: vt_broken", "vt_broken"),
           ("skip", "short blocked: levels_invalid", "levels_invalid"),
           ("skip", "entries/day", "capacity"), ("skip", "one unpaired leg", "capacity")]


def refusals(ev: pd.DataFrame) -> pd.DataFrame:
    rows = ev[ev.event_type.isin(["skip", "late_no_entry"])].copy()
    rows["reason"] = ""
    for et, needle, reason in REFUSAL:
        m = (rows.event_type == et) & (rows.notes.str.contains(needle, regex=False) if needle else True)
        rows.loc[m, "reason"] = reason
    rows = rows[rows.reason != ""]
    return rows[SETUP + ["reason"]].drop_duplicates(SETUP).reset_index(drop=True)


def label(dates: pd.Series, registered: str) -> pd.Series:
    return np.where(dates <= registered, "DISCOVERY", "CONFIRMATION")     # W5.1


# ---- book (W4.2) --------------------------------------------------------------------
class MarkCache:
    """Closing quotes for (date, expiry): pulled once through v1's chain client, cached as parquet."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        MARKS_DIR.mkdir(parents=True, exist_ok=True)

    def frame(self, date: str, expiry: str) -> pd.DataFrame | None:
        p = MARKS_DIR / f"{date}_{expiry}.parquet"
        if p.exists():
            return pd.read_parquet(p)
        if not self.enabled:
            return None
        import datetime as dt
        from hiro_engine.chains import _sdk_pull_day             # read-only library use of v1
        log.info("pulling marks %s exp %s", date, expiry)
        df = _sdk_pull_day(date, dt.date.fromisoformat(expiry))
        df.to_parquet(p, index=False)
        return df

    def close_mid(self, date: str, expiry: str, strike: float) -> float | None:
        f = self.frame(date, expiry)
        if f is None:
            return None
        q = f[(f.strike == strike) & (f["min"] <= 960) & (f.bid > 0) & (f.ask > 0) & (f.ask >= f.bid)]
        if not len(q):
            return None
        last = q.sort_values("min").iloc[-1]
        return float((last.bid + last.ask) / 2)


def spx_close(date: str, spx_dir: Path) -> float:
    p = spx_dir / f"{date}.parquet"
    if not p.exists():
        raise SystemExit(f"REFUSED: SPX bars for settlement day {date} missing: {p}")
    d = pd.read_parquet(p)
    return float(d[d["min"] <= 960].sort_values("min").close.iloc[-1])


def book(t: pd.DataFrame, asof: str, marks: MarkCache, spx_dir: Path) -> dict:
    """cash + marks on open bombs + settled payoffs on expired bombs = MTM. bomb = long k_long / short k_short put."""
    bombs = t[t.bomb].copy()
    rows, unmarked = [], []
    for _, b in bombs.iterrows():
        width = b.k_long - b.k_short
        if b.expiry <= asof:
            s = spx_close(b.expiry, spx_dir)
            val = (max(0.0, b.k_long - s) - max(0.0, b.k_short - s)) * USD
            rows.append(dict(session_date=b.session_date, branch=b.branch, k_long=b.k_long, k_short=b.k_short,
                             expiry=b.expiry, state="SETTLED", value_usd=val, spx_settle=s))
        else:
            ml, ms = marks.close_mid(asof, b.expiry, b.k_long), marks.close_mid(asof, b.expiry, b.k_short)
            if ml is None or ms is None:
                unmarked.append(f"{b.session_date} {b.branch} {b.k_long:.0f}/{b.k_short:.0f} exp {b.expiry}")
                rows.append(dict(session_date=b.session_date, branch=b.branch, k_long=b.k_long, k_short=b.k_short,
                                 expiry=b.expiry, state="UNMARKED", value_usd=np.nan, spx_settle=np.nan))
            else:
                rows.append(dict(session_date=b.session_date, branch=b.branch, k_long=b.k_long, k_short=b.k_short,
                                 expiry=b.expiry, state="MARKED", value_usd=min(ml - ms, width) * USD, spx_settle=np.nan))
    inv = pd.DataFrame(rows)
    cash = float(t.pnl_usd.sum())
    inventory = float(inv.value_usd.sum()) if len(inv) else 0.0
    return dict(cash=cash, inventory=inventory, mtm=cash + inventory, n_bombs=len(inv),
                unmarked=unmarked, table=inv)


# ---- statistics (W4.4) --------------------------------------------------------------
def lb95(fills_by_session: pd.DataFrame) -> float:
    """fills_by_session: columns session_date, fills, n. min(session-bootstrap p5, Clopper-Pearson lower)."""
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


def per_session(t: pd.DataFrame) -> pd.DataFrame:
    g = t.groupby("session_date").agg(fills=("bomb", "sum"), n=("bomb", "size")).reset_index()
    return g


# ---- verdicts (W5.3) ----------------------------------------------------------------
def checkpoint(n_conf: int) -> bool:
    return n_conf in CHECKPOINTS


def verdict_a_depth(base_t, base_sig, cand_t, cand_book, base_book) -> str:
    """Passed cohort = confirmation A signals with r30 <= -4 (from the baseline log); its economics from the candidate run."""
    B = BARS["a_depth"]
    sig = base_sig[(base_sig.set == "CONFIRMATION") & (base_sig.branch == "A")]
    passed = sig[sig.r30 <= -4.0]
    ct = cand_t[(cand_t.set == "CONFIRMATION") & (cand_t.branch == "A")]
    bt = base_t[(base_t.set == "CONFIRMATION") & (base_t.branch == "A")]
    if len(ct) and ct.pnl_usd.min() < B["max_loss"]:
        return f"REJECT — passed loss {ct.pnl_usd.min():+.0f} < {B['max_loss']:+.0f} (immediate)"
    counts_ok = (len(sig) >= B["signals"] and sig.session_date.nunique() >= B["signal_days"]
                 and len(passed) >= B["passed"] and passed.session_date.nunique() >= B["passed_days"]
                 and (passed.session_date.value_counts().max() / max(len(passed), 1)) <= B["day_share"])
    if not counts_ok:
        if len(sig) >= B["expire_signals"]:
            return f"REJECT-EXPIRED — {len(sig)} confirmation A signals without meeting the count bars"
        return (f"INCONCLUSIVE — A signals {len(sig)}/{B['signals']} over {sig.session_date.nunique()}/{B['signal_days']} days; "
                f"passed {len(passed)}/{B['passed']} over {passed.session_date.nunique()}/{B['passed_days']} days")
    if cand_book["unmarked"] or base_book["unmarked"]:
        return f"DEFERRED — unmarked bombs: {cand_book['unmarked'] + base_book['unmarked']}"
    lb = lb95(per_session(ct))
    exp_c = (ct.pnl_usd.sum() + cand_book["inventory"]) / max(len(passed), 1)
    exp_b = (bt.pnl_usd.sum() + base_book["inventory"]) / max(len(sig), 1)
    credits = float(ct[ct.bomb].pnl_usd.sum())
    if lb <= B["lb95"]:
        return f"REJECT — passed completion LB95 {lb:.2f} <= {B['lb95']}"
    if exp_c <= exp_b:
        return f"REJECT — passed expectancy {exp_c:+.0f}/signal <= baseline {exp_b:+.0f}/signal"
    if cand_book["mtm"] < base_book["mtm"] - credits:
        return f"REJECT — candidate MTM {cand_book['mtm']:+.0f} < baseline {base_book['mtm']:+.0f} − credits {credits:.0f}"
    if cand_book["mtm"] < base_book["mtm"]:
        return f"INCONCLUSIVE — candidate MTM {cand_book['mtm']:+.0f} < baseline {base_book['mtm']:+.0f}"
    return f"PROMOTE — LB95 {lb:.2f}, expectancy {exp_c:+.0f} vs {exp_b:+.0f}/signal, MTM {cand_book['mtm']:+.0f} vs {base_book['mtm']:+.0f}"


def verdict_credit(base_t, cand_t, branch, cand_book, base_book) -> str:
    B = BARS["credit"]
    bt = base_t[(base_t.set == "CONFIRMATION") & (base_t.branch == branch)]
    ct = cand_t[(cand_t.set == "CONFIRMATION") & (cand_t.branch == branch)]
    lost = bt[bt.bomb].merge(ct[SETUP + ["bomb"]], on=SETUP, how="left", suffixes=("", "_c"))
    lost = lost[lost.bomb_c.fillna(False) != True]                      # noqa: E712
    if len(lost):
        return f"REJECT — {len(lost)} baseline {branch} fill(s) lost at 0.30: {lost[SETUP].values.tolist()} (immediate)"
    if len(ct) and ct.pnl_usd.min() < B["max_loss"]:
        return f"REJECT — trade P&L {ct.pnl_usd.min():+.0f} < {B['max_loss']:+.0f} (immediate)"
    need = B[branch]
    if branch == "A":
        counts_ok = int(bt.bomb.sum()) >= need["fills"]
        progress = f"baseline A fills {int(bt.bomb.sum())}/{need['fills']}"
    else:
        counts_ok = len(bt) >= need["entries"] and int(bt.bomb.sum()) >= need["fills"]
        progress = f"B entries {len(bt)}/{need['entries']}, baseline B fills {int(bt.bomb.sum())}/{need['fills']}"
    if not counts_ok:
        return f"INCONCLUSIVE — {progress}"
    if cand_book["unmarked"] or base_book["unmarked"]:
        return f"DEFERRED — unmarked bombs: {cand_book['unmarked'] + base_book['unmarked']}"
    if ct.mae.min() < B["max_mae"]:
        return f"REJECT — MAE {ct.mae.min():+.0f} < {B['max_mae']:+.0f}"
    if ct.pnl_usd.sum() < bt.pnl_usd.sum():
        return f"REJECT — net cash {ct.pnl_usd.sum():+.0f} < baseline {bt.pnl_usd.sum():+.0f}"
    if cand_book["mtm"] < base_book["mtm"]:
        return f"INCONCLUSIVE — MTM {cand_book['mtm']:+.0f} < baseline {base_book['mtm']:+.0f}"
    return f"PROMOTE ({branch}) — zero fills lost, cash {ct.pnl_usd.sum():+.0f} vs {bt.pnl_usd.sum():+.0f}, MTM {cand_book['mtm']:+.0f} vs {base_book['mtm']:+.0f}"


def diag_table(base_ref: pd.DataFrame, cand_t: pd.DataFrame, reason: str) -> pd.DataFrame:
    """Sole-blocker attribution (W4.3): a refused baseline setup is scored only if the diag run entered it."""
    r = base_ref[base_ref.reason == reason]
    j = r.merge(cand_t[SETUP + ["bomb", "pnl_usd", "mae", "outcome_type", "set"]], on=SETUP, how="left")
    j["scored"] = j.outcome_type.notna()
    return j


# ---- report -------------------------------------------------------------------------
def _split(t: pd.DataFrame) -> str:
    lines = []
    for s in ("DISCOVERY", "CONFIRMATION"):
        for br in ("A", "B"):
            x = t[(t.set == s) & (t.branch == br)]
            if not len(x):
                lines.append(f"    {s:<12} {br}  —")
                continue
            lines.append(f"    {s:<12} {br}  trades {len(x):>2}  bombs {int(x.bomb.sum()):>2}  rate {x.bomb.mean():.2f}  "
                         f"cash {x.pnl_usd.sum():+7.0f}  worst {x.pnl_usd.min():+5.0f}  MAE {x.mae.min():+5.0f}  "
                         f"fill-min med {x[x.bomb].outcome_minutes.median() if x.bomb.any() else float('nan'):.0f}")
    return "\n".join(lines)


def run(asof: str | None, with_marks: bool) -> int:
    cands = candidates()
    data = yaml.safe_load((CONFIGS / "baseline_v2.yaml").read_text())["data"]
    era, spx_dir = str(data["hiro_era_start"]), Path(data["spx_dir"]).expanduser()
    base_ev = load_log(V1_LOGS)
    base_ev = base_ev[base_ev.session_date >= era]                     # v1's log also holds pre-era price-tier days
    base_sess = load_sessions(V1_SESSIONS)
    base_sess = base_sess[base_sess.date >= era]
    asof = asof or base_sess.date.max()
    marks = MarkCache(enabled=with_marks)
    base_t, base_sig, base_ref = trades(base_ev), signals(base_ev), refusals(base_ev)
    print(f"hiro_watch compare | baseline v1 {base_ev.config_hash.iloc[0][:12]}… | sessions {base_sess.date.min()}..{asof} | asof {asof}")
    for c in cands:
        ev = load_log([c["log"]])
        sess = load_sessions(c["sessions"])
        missing = sorted(set(base_sess.date) - set(sess.date))
        if missing:
            raise SystemExit(f"REFUSED: {c['name']} lacks sessions {missing} (W0.3 — run.py them)")
        t, ref = trades(ev), refusals(ev)
        for df in (t, ref):
            df["set"] = label(df.session_date, c["registered"])
        bt, bsig, bref = base_t.copy(), base_sig.copy(), base_ref.copy()
        for df in (bt, bsig, bref):
            df["set"] = label(df.session_date, c["registered"])
        countable_conf = base_sess[(base_sess.disposition == "countable") & (base_sess.date > c["registered"])]
        n_conf = len(countable_conf)
        cb, bb = book(t, asof, marks, spx_dir), book(bt, asof, marks, spx_dir)
        print(f"\n### {c['name']}  [{c['kind']}, {c['engine']}, {ev.config_hash.iloc[0][:12]}…]  {c['change']}")
        print(f"  registered {c['registered']} | confirmation sessions {n_conf} | "
              f"{'CHECKPOINT' if checkpoint(n_conf) else f'next checkpoint at {next((k for k in CHECKPOINTS if k > n_conf), 40)}'}")
        print("  candidate:"); print(_split(t))
        print("  baseline: "); print(_split(bt))
        print(f"  book (asof {asof}): cash {cb['cash']:+.0f} + inventory {cb['inventory']:+.0f} ({cb['n_bombs']} bombs) = MTM {cb['mtm']:+.0f}"
              f"   | baseline MTM {bb['mtm']:+.0f} ({bb['n_bombs']} bombs)"
              + (f"   UNMARKED {len(cb['unmarked'])}: {cb['unmarked'][:3]}{'…' if len(cb['unmarked']) > 3 else ''}" if cb["unmarked"] else ""))
        if c["name"] == "a_depth_m4":
            a = bsig[bsig.branch == "A"].merge(bt[SETUP + ["bomb", "pnl_usd"]], on=SETUP, how="left")
            print("  Θ ladder over baseline A signals (entered ones; bomb rate | n):")
            for th in (-1.0, -2.0, -3.0, -4.0, -5.0):
                for s in ("DISCOVERY", "CONFIRMATION"):
                    x = a[(a.set == s) & (a.r30 <= th) & a.bomb.notna()]
                    print(f"    θ {th:+.0f} {s:<12} {x.bomb.mean() if len(x) else float('nan'):.2f} | {len(x)}")
            v = verdict_a_depth(bt, bsig, t, cb, bb)
        elif c["name"] == "credit030":
            for br in ("A", "B"):
                lost = bt[bt.bomb & (bt.branch == br)].merge(t[SETUP + ["bomb"]], on=SETUP, how="left", suffixes=("", "_c"))
                lost = lost[lost.bomb_c.fillna(False) != True]           # noqa: E712
                print(f"  {br}: baseline fills {int(bt[bt.branch == br].bomb.sum())}, lost at 0.30: {len(lost)}"
                      + (f" {lost[SETUP].values.tolist()}" if len(lost) else ""))
            v = " | ".join(verdict_credit(bt, t, br, cb, bb) for br in ("A", "B"))
        elif c["kind"] == "diagnostic":
            reason = {"diag_vt_off": "vt_broken", "diag_levels_off": "levels_invalid", "diag_late_off": "late"}[c["name"]]
            d = diag_table(bref, t, reason)
            sc = d[d.scored]
            print(f"  refused({reason}): {len(d)} episodes, entered when rule off: {len(sc)}, bombs {int(sc.bomb.sum())}, "
                  f"cash {sc.pnl_usd.sum():+.0f}, worst {sc.pnl_usd.min() if len(sc) else 0:+.0f}, "
                  f"share MAE<-150: {(sc.mae < -150).mean() if len(sc) else 0:.2f}  [never promoted]")
            v = f"INCONCLUSIVE — {len(d)}/{BARS['diag']['episodes']} refused episodes" if len(d) < BARS["diag"]["episodes"] else "REPORTED (diagnostic)"
        else:
            v = "control — no verdict"
        if checkpoint(n_conf) or v.startswith("REJECT") or c["kind"] != "promotable":
            print(f"  VERDICT: {v}")
        else:
            print(f"  status: INCONCLUSIVE ({n_conf}/{next((k for k in CHECKPOINTS if k > n_conf), 40)}) — verdicts print at checkpoints only")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="hiro_watch/compare.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--asof", default=None, help="mark the book at this session's close (default: latest baseline session)")
    ap.add_argument("--no-marks", action="store_true", help="never pull quotes; unmarked bombs stay UNMARKED")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.debug else logging.INFO, format="%(message)s")
    if a.debug:
        print("[debug on]")
    return run(a.asof, not a.no_marks)


if __name__ == "__main__":
    sys.exit(main())
