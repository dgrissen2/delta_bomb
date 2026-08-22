"""Stress-test the "delta bomb second leg needs ~3 SPX points" claim.

Claim under test
----------------
For a 5-wide SPX put vertical struck around 20 delta at 20-40 DTE, the price
gap between adjacent strikes -- ``mid(K+5) - mid(K)`` -- divided by the local
option delta approximates the SPX move required to leg the second (short) side
at breakeven, and that quantity is roughly 3 index points.

Method
------
1. Build the session universe from the SPXW 5-minute greeks store, keep sessions
   where the SPX cash open is above that day's SpotGamma Vol Trigger, then draw a
   seeded random sample.
2. At the 10:00 ET bar (13:00 ET as robustness check) locate the put strike whose
   ``|delta|`` is closest to each target (0.15 / 0.20 / 0.25).
3. ``gap = mid(K+5) - mid(K)`` where mid = (bid + ask) / 2.
   ``required_move = gap / delta_ref`` with ``delta_ref`` the AVERAGE of
   ``|delta(K)|`` and ``|delta(K+5)|`` (the task-specified convention; using
   ``|delta(K)|`` alone shifts results by well under 2%, also emitted for audit).
4. Emit one row per (date, bar, delta target) to CSV.

Quote-noise caveat
------------------
A two-point difference of mids is a noise amplifier: the true gap is ~0.70 and
some sessions carry 5-15 point wide bid/ask on the wing puts, so a single stale
quote can swamp it. Each row therefore also carries ``required_move_smooth``,
built from an OLS slope of mid-vs-strike over a local strike window, plus
``rel_spread_k`` and a ``quality_ok`` flag so noisy quotes can be excluded.

Schema surprise worth knowing: the greeks store does NOT carry a dense 5-wide
strike ladder at the 20-delta wing. Native spacing out there is typically 25
points (10 points nearer the money). So ``mid(K+5)`` and ``delta(K+5)`` are
obtained by linear interpolation of the mid-vs-strike and delta-vs-strike
curves. The interpolated gap is therefore ``5 * dMid/dK`` measured over the
nearest available bracket. ``native_spacing`` is recorded per row so the
sensitivity can be checked.

Usage
-----
    /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python \
        /Users/dgrissen/Dev/delta_bomb/scripts/stress_gap_delta.py
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

GREEKS_ROOT = (
    "/Users/dgrissen/Dev/central_trade_data/thetadata/"
    "lrrf_spxw_1550_5m_2026-08-10-v1/raw/greeks"
)
SPX_1M_ROOT = "/Users/dgrissen/Dev/central_trade_data/thetadata/spx_index_1m_ohlc"
SPOTGAMMA_CSV = (
    "/Users/dgrissen/Dev/central_trade_data/spotgamma_fixed/"
    "offset_historical_FIXED_2026-06-14.csv"
)
OUT_CSV = "/Users/dgrissen/Dev/delta_bomb/docs/replay/gap_delta_stress.csv"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
YEAR_LO, YEAR_HI = "2024-01-01", "2025-12-31"
BARS = ("10:00", "13:00")
DELTA_TARGETS = (0.15, 0.20, 0.25)
WIDTH = 5.0
SMOOTH_WINDOW = 30.0  # +/- strike points used for the local OLS slope
MAX_REL_SPREAD = 0.15  # bid/ask width as a fraction of mid for quality_ok
SAMPLE_N = 50
SEED = 42
OPEN_MINUTE = 570  # 09:30 ET expressed as minutes past midnight


class DataUnavailableError(RuntimeError):
    """Raised when a required input file is missing or unusable."""


@dataclass(frozen=True)
class SessionContext:
    """Per-session cash-open context used for the Vol Trigger filter."""

    date: str
    spx_open: float
    vol_trigger: float

    @property
    def above_vol_trigger(self) -> bool:
        return self.spx_open > self.vol_trigger


def list_greeks_dates(lo: str = YEAR_LO, hi: str = YEAR_HI) -> list[str]:
    """Return sorted session dates that have a non-empty greeks parquet."""
    dates: list[str] = []
    for name in sorted(os.listdir(GREEKS_ROOT)):
        if not DATE_RE.match(name) or not (lo <= name <= hi):
            continue
        if glob.glob(os.path.join(GREEKS_ROOT, name, "*.parquet")):
            dates.append(name)
    return dates


def load_vol_triggers() -> dict[str, float]:
    """Map session date -> SpotGamma Vol Trigger level."""
    sg = pd.read_csv(SPOTGAMMA_CSV, usecols=["Date", "Vol Trigger"])
    sg = sg.dropna(subset=["Vol Trigger"])
    return dict(zip(sg["Date"].astype(str), sg["Vol Trigger"].astype(float)))


def spx_session_open(date: str) -> float | None:
    """Cash SPX open for the session, from the 1-minute OHLC store."""
    path = os.path.join(SPX_1M_ROOT, f"{date}.parquet")
    if not os.path.exists(path):
        return None
    df = pq.read_table(path, columns=["min", "open"]).to_pandas()
    if df.empty:
        return None
    at_open = df.loc[df["min"] == OPEN_MINUTE, "open"]
    if not at_open.empty:
        return float(at_open.iloc[0])
    return float(df.sort_values("min")["open"].iloc[0])


def build_universe() -> tuple[list[SessionContext], dict[str, int]]:
    """Sessions with greeks + SPX open + Vol Trigger, plus drop-reason counts."""
    triggers = load_vol_triggers()
    kept: list[SessionContext] = []
    drops = {"no_spx_1m": 0, "no_vol_trigger": 0, "below_vol_trigger": 0}
    for date in list_greeks_dates():
        vt = triggers.get(date)
        if vt is None:
            drops["no_vol_trigger"] += 1
            continue
        spx_open = spx_session_open(date)
        if spx_open is None:
            drops["no_spx_1m"] += 1
            continue
        ctx = SessionContext(date=date, spx_open=spx_open, vol_trigger=vt)
        if not ctx.above_vol_trigger:
            drops["below_vol_trigger"] += 1
            continue
        kept.append(ctx)
    return kept, drops


def load_put_chain(date: str) -> pd.DataFrame:
    """Load the session's SPXW put greeks, cleaned of unquoted rows."""
    files = glob.glob(os.path.join(GREEKS_ROOT, date, "*.parquet"))
    if not files:
        raise DataUnavailableError(f"no greeks parquet for {date}")
    df = pq.read_table(files[0]).to_pandas()
    df = df[df["right"].astype(str).str.upper() == "PUT"]
    df = df[(df["bid"] > 0) & (df["ask"] > df["bid"]) & (df["delta"] < 0)]
    df = df[df["implied_vol"] > 0]
    df["mid"] = (df["bid"] + df["ask"]) / 2.0
    df["abs_delta"] = df["delta"].abs()
    df["bar"] = df["timestamp"].dt.strftime("%H:%M")
    return df


def bar_slice(chain: pd.DataFrame, bar: str) -> pd.DataFrame:
    """One timestamp's put ladder, sorted and de-duplicated by strike."""
    snap = chain[chain["bar"] == bar]
    if snap.empty:
        return snap
    snap = snap.sort_values("strike").drop_duplicates("strike", keep="last")
    return snap.reset_index(drop=True)


def measure(snap: pd.DataFrame, target: float) -> dict[str, float] | None:
    """Gap / delta measurement at the strike closest to ``target`` delta.

    Returns None when the ladder cannot support the measurement (no OTM strike
    near the target, or K+5 falls outside the quoted strike range).
    """
    spot = float(snap["underlying_price"].dropna().iloc[0]) if snap[
        "underlying_price"
    ].notna().any() else np.nan
    otm = snap[snap["strike"] < spot] if np.isfinite(spot) else snap
    otm = otm[(otm["abs_delta"] > 0.02) & (otm["abs_delta"] < 0.60)]
    if len(otm) < 3:
        return None

    idx = (otm["abs_delta"] - target).abs().idxmin()
    row = otm.loc[idx]
    k = float(row["strike"])
    k_up = k + WIDTH

    strikes = snap["strike"].to_numpy(dtype=float)
    if k_up > strikes.max():
        return None

    mid_up = float(np.interp(k_up, strikes, snap["mid"].to_numpy(dtype=float)))
    delta_up = float(
        np.interp(k_up, strikes, snap["abs_delta"].to_numpy(dtype=float))
    )
    iv_up = float(
        np.interp(k_up, strikes, snap["implied_vol"].to_numpy(dtype=float))
    )

    # Local OLS slope of mid vs strike -- robust to a single stale quote.
    win = snap[(snap["strike"] >= k - SMOOTH_WINDOW)
               & (snap["strike"] <= k + SMOOTH_WINDOW)]
    if len(win) >= 3:
        slope = float(np.polyfit(win["strike"].to_numpy(dtype=float),
                                 win["mid"].to_numpy(dtype=float), 1)[0])
    else:
        slope = np.nan

    higher = strikes[strikes > k]
    native_spacing = float(higher.min() - k) if higher.size else np.nan

    gap = mid_up - float(row["mid"])
    delta_k = float(row["abs_delta"])
    delta_avg = (delta_k + delta_up) / 2.0
    if delta_avg <= 0:
        return None

    return {
        "strike": k,
        "delta_k": delta_k,
        "delta_kp5": delta_up,
        "delta_avg": delta_avg,
        "mid_k": float(row["mid"]),
        "mid_kp5": mid_up,
        "gap": gap,
        "required_move": gap / delta_avg,
        "gap_smooth": slope * WIDTH,
        "required_move_smooth": slope * WIDTH / delta_avg,
        "rel_spread_k": float(row["ask"] - row["bid"]) / float(row["mid"]),
        "quality_ok": bool(
            (float(row["ask"] - row["bid"]) / float(row["mid"]))
            <= MAX_REL_SPREAD
        ),
        "required_move_delta_k_only": gap / delta_k,
        "iv_k": float(row["implied_vol"]),
        "iv_kp5": iv_up,
        "native_spacing": native_spacing,
        "underlying_price": spot,
    }


def atm_iv(snap: pd.DataFrame) -> float:
    """Implied vol of the put nearest the underlying (ATM IV proxy)."""
    if snap.empty or not snap["underlying_price"].notna().any():
        return float("nan")
    spot = float(snap["underlying_price"].dropna().iloc[0])
    i = (snap["strike"] - spot).abs().idxmin()
    return float(snap.loc[i, "implied_vol"])


def iter_rows(sessions: list[SessionContext]) -> Iterator[dict]:
    """Yield one output record per (session, bar, delta target)."""
    for ctx in sessions:
        try:
            chain = load_put_chain(ctx.date)
        except DataUnavailableError:
            continue
        if chain.empty:
            continue
        expiry = str(chain["expiration"].iloc[0])
        dte = (pd.Timestamp(expiry) - pd.Timestamp(ctx.date)).days
        for bar in BARS:
            snap = bar_slice(chain, bar)
            if snap.empty:
                yield {
                    "date": ctx.date,
                    "bar": bar,
                    "status": "no_bar",
                    "expiration": expiry,
                    "dte": dte,
                    "spx_open": ctx.spx_open,
                    "vol_trigger": ctx.vol_trigger,
                }
                continue
            iv_atm = atm_iv(snap)
            for target in DELTA_TARGETS:
                res = measure(snap, target)
                base = {
                    "date": ctx.date,
                    "bar": bar,
                    "delta_target": target,
                    "expiration": expiry,
                    "dte": dte,
                    "spx_open": ctx.spx_open,
                    "vol_trigger": ctx.vol_trigger,
                    "iv_atm": iv_atm,
                    "year": ctx.date[:4],
                }
                if res is None:
                    base["status"] = "no_measure"
                else:
                    base["status"] = "ok"
                    base.update(res)
                yield base


def describe(series: pd.Series) -> dict[str, float]:
    """min / p10 / median / mean / p90 / max summary."""
    s = series.dropna()
    if s.empty:
        return {k: float("nan") for k in
                ("n", "min", "p10", "median", "mean", "p90", "max")}
    return {
        "n": float(len(s)),
        "min": float(s.min()),
        "p10": float(s.quantile(0.10)),
        "median": float(s.median()),
        "mean": float(s.mean()),
        "p90": float(s.quantile(0.90)),
        "max": float(s.max()),
    }


def main() -> None:
    sessions, drops = build_universe()
    print(f"qualifying sessions (open > Vol Trigger, {YEAR_LO}..{YEAR_HI}): "
          f"{len(sessions)}  drops={drops}")

    rng = np.random.default_rng(SEED)
    if len(sessions) <= SAMPLE_N:
        sample = sessions
        print(f"NOTE: fewer than {SAMPLE_N} qualified; using all {len(sample)}")
    else:
        pick = rng.choice(len(sessions), size=SAMPLE_N, replace=False)
        sample = [sessions[i] for i in sorted(pick)]
    print(f"sampled sessions: {len(sample)}  "
          f"({sample[0].date} .. {sample[-1].date})")

    out = pd.DataFrame(list(iter_rows(sample)))
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}  rows={len(out)}")

    ok = out[out["status"] == "ok"]
    for bar in BARS:
        for target in DELTA_TARGETS:
            sub = ok[(ok["bar"] == bar) & (ok["delta_target"] == target)]
            d = describe(sub["required_move"])
            e = describe(sub["required_move_smooth"])
            print(f"{bar} {target:.2f}D raw    n={d['n']:.0f}  min={d['min']:.2f} "
                  f"p10={d['p10']:.2f} med={d['median']:.2f} mean={d['mean']:.2f} "
                  f"p90={d['p90']:.2f} max={d['max']:.2f}")
            print(f"{bar} {target:.2f}D smooth n={e['n']:.0f}  min={e['min']:.2f} "
                  f"p10={e['p10']:.2f} med={e['median']:.2f} mean={e['mean']:.2f} "
                  f"p90={e['p90']:.2f} max={e['max']:.2f}")

    core = ok[(ok["bar"] == "10:00") & (ok["delta_target"] == 0.20)]
    print("\nquote quality (20D, 10:00): "
          f"quality_ok={int(core['quality_ok'].sum())}/{len(core)}  "
          f"median rel_spread={core['rel_spread_k'].median():.3f}")
    q = core[core["quality_ok"]]
    dq = describe(q["required_move"])
    print(f"  raw, quality_ok only: n={dq['n']:.0f} p10={dq['p10']:.2f} "
          f"med={dq['median']:.2f} p90={dq['p90']:.2f} max={dq['max']:.2f}")
    hit = core["required_move"].between(2.5, 3.5).mean()
    print(f"\n20D 10:00 within 2.5-3.5 pts: {hit:.1%} of {len(core)} days")
    print(f"20D 10:00 within 2.0-4.0 pts: "
          f"{core['required_move'].between(2.0, 4.0).mean():.1%}")
    print("\nby year (20D, 10:00):")
    print(core.groupby("year")["required_move"].describe()[
        ["count", "mean", "50%", "min", "max"]].to_string())
    print("\nIV tercile (20D, 10:00) by iv_atm:")
    core = core.copy()
    core["iv_bucket"] = pd.qcut(core["iv_atm"], 3,
                                labels=["low IV", "mid IV", "high IV"])
    print(core.groupby("iv_bucket", observed=True).agg(
        n=("required_move", "size"),
        iv_lo=("iv_atm", "min"), iv_hi=("iv_atm", "max"),
        med=("required_move", "median"),
        mean=("required_move", "mean")).to_string())
    print("smooth within 2.5-3.5 pts: "
          f"{core['required_move_smooth'].between(2.5, 3.5).mean():.1%}")
    print("\ndays with required_move > 4.5 pts (20D, 10:00):")
    hot = core[core["required_move"] > 4.5].sort_values("required_move")
    cols = ["date", "underlying_price", "strike", "delta_avg", "gap",
            "required_move", "required_move_smooth", "iv_k", "iv_atm",
            "rel_spread_k", "native_spacing", "dte"]
    print(hot[cols].to_string(index=False) if len(hot) else "  (none)")
    print("\nnative strike spacing at the 20D strike (10:00):")
    print(core["native_spacing"].value_counts().to_string())
    print("\ndelta convention sensitivity (20D, 10:00): median req_move "
          f"avg-delta={core['required_move'].median():.3f} vs "
          f"delta(K)-only={core['required_move_delta_k_only'].median():.3f}")
    print(f"\nDTE range in sample: {ok['dte'].min()}..{ok['dte'].max()}")
    print(f"missing 13:00 bars: {(out['status'] == 'no_bar').sum()}")


if __name__ == "__main__":
    main()
