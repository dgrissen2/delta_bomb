"""FeatureEngine (R3) — pure computation, no I/O.

The trough-anchored run machine is the SINGLE HOME of the research logic from
hiro_setup_dashboard.detect() (ported verbatim; the dashboard now imports
`apply_run_machine` from here). The incremental RunMachine reproduces the frame
function bar-for-bar (tested equal).

Ownership (design.md): FeatureEngine computes ONLY market-derived fields.
`vetoes` and `health` on FeatureRow are attached by Session — never here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from .config import Config
from .models import Bar, FeatureRow, SpyBar, TierPolicy
from . import rules as _rules


# ---------------------------------------------------------------------------
# R3.2 run machine — frame form, VERBATIM port of hiro_setup_dashboard.detect()
# ---------------------------------------------------------------------------
def apply_run_machine(df: pd.DataFrame, rev: float) -> pd.DataFrame:
    """Adds run/dur/dC/dP/dN/dd/broke/rate/cpr/share to a frame with
    all_L/all_Lc/all_Lp/nextExp_L/min columns. Logic identical to the reviewed
    research detect() — do not 'improve' (task 3a artifact-rot guard)."""
    L, Lc, Lp, N, t = (df.all_L.values, df.all_Lc.values, df.all_Lp.values,
                       df.nextExp_L.values, df["min"].values)
    n = len(df)
    lo = hi = 0
    run = np.zeros(n); dur = np.zeros(n); dC = np.zeros(n); dP = np.zeros(n)
    dN = np.zeros(n); dd = np.zeros(n); broke = np.zeros(n, bool)
    for i in range(n):
        if L[i] < L[lo]:
            lo = hi = i
        if L[i] > L[hi]:
            hi = i
        d = L[hi] - L[i]
        if d >= rev:
            lo = hi = i; d = 0.0; broke[i] = True
        run[i] = L[i] - L[lo]; dur[i] = t[i] - t[lo]
        dC[i] = Lc[i] - Lc[lo]; dP[i] = Lp[i] - Lp[lo]; dN[i] = N[i] - N[lo]; dd[i] = d
    df = df.assign(run=run, dur=dur, dC=dC, dP=dP, dN=dN, dd=dd, broke=broke)
    df["rate"] = df.run / df.dur.clip(lower=1) * 60
    df["cpr"] = np.minimum(df.dC, df.dP) / np.maximum(df.dC, df.dP).replace(0, np.nan)
    df["share"] = df.dN / df.run.replace(0, np.nan)
    return df


class RunMachine:
    """Incremental equivalent of apply_run_machine — one bar at a time."""

    def __init__(self, rev: float):
        self.rev = rev
        self.L: list[float] = []; self.Lc: list[float] = []
        self.Lp: list[float] = []; self.N: list[float] = []; self.t: list[int] = []
        self.lo = self.hi = 0

    def update(self, m: int, L: float, Lc: float, Lp: float, N: float) -> dict:
        self.L.append(L); self.Lc.append(Lc); self.Lp.append(Lp); self.N.append(N); self.t.append(m)
        i = len(self.L) - 1
        broke = False
        if self.L[i] < self.L[self.lo]:
            self.lo = self.hi = i
        if self.L[i] > self.L[self.hi]:
            self.hi = i
        d = self.L[self.hi] - self.L[i]
        if d >= self.rev:
            self.lo = self.hi = i; d = 0.0; broke = True
        lo = self.lo
        run = L - self.L[lo]; dur = m - self.t[lo]
        dC = Lc - self.Lc[lo]; dP = Lp - self.Lp[lo]; dN = N - self.N[lo]
        rate = run / max(dur, 1) * 60
        mx = max(dC, dP)
        cpr = (min(dC, dP) / mx) if mx != 0 else float("nan")
        share = (dN / run) if run != 0 else None
        return dict(run=run, dur=float(dur), rate=rate, dC=dC, dP=dP, dN=dN,
                    dd=d, broke=broke, cpr=cpr, share=share,
                    weak_side=min(dC, dP))


# ---------------------------------------------------------------------------
# FeatureEngine
# ---------------------------------------------------------------------------
@dataclass
class _EpisodeTracker:
    """R3.5 — one tracker per branch."""
    lapse_min: int
    next_id: int = 1
    active: Optional[int] = None
    false_streak: int = 0

    def update(self, conditions_true: bool, hard_break: bool = False) -> Optional[int]:
        if hard_break:
            self.active = None
            self.false_streak = 0
            return self.active if conditions_true else None
        if conditions_true:
            if self.active is None:
                self.active = self.next_id
                self.next_id += 1
            self.false_streak = 0
        else:
            if self.active is not None:
                self.false_streak += 1
                if self.false_streak >= self.lapse_min:
                    self.active = None
                    self.false_streak = 0
        return self.active


class FeatureEngine:
    """Consumes bars + HIRO frame + SPY bars; emits one immutable FeatureRow per bar."""

    def __init__(self, cfg: Config, tier: TierPolicy,
                 range60_history: Optional[list[float]] = None,
                 im: Optional[float] = None):
        self.cfg = cfg
        self.tier = tier
        self.rev = cfg.num("r3_derived", "run_break_dd")
        self.roll = cfg.i("r3_derived", "roll_window")
        self.r60w = cfg.i("r3_derived", "range60_window")
        self.r60_pctile = cfg.num("r3_derived", "range60_pctile")
        self.r60_min_obs = cfg.i("r3_derived", "range60_min_obs")
        self.im = im
        self.reads = [int(x) for x in cfg.get("r3_derived", "context_reads_min")]
        self.im_frac = cfg.num("r3_derived", "context_im_frac")
        self.vwap_share = cfg.num("r3_derived", "context_vwap_share")
        self.vwap_bars = cfg.i("r3_derived", "context_vwap_bars")
        self.rm = RunMachine(self.rev)
        self.closes: list[float] = []
        self.highs: list[float] = []
        self.mins: list[int] = []
        self.Ls: list[float] = []
        self.Ns: list[float] = []
        # pooled causal range60 history from PRIOR sessions (R3.3)
        self.r60_history: list[float] = list(range60_history or [])
        self.r60_today: list[float] = []
        self.open_0930: Optional[float] = None
        self.ema = {5: None, 9: None, 20: None}
        self.vwap_num = 0.0
        self.vwap_den = 0.0
        self.spy_closes: list[float] = []
        self.vwaps: list[float] = []
        self.context_1030: Optional[str] = None
        self.context_1300: Optional[str] = None
        self.ep_a = _EpisodeTracker(cfg.i("r3_derived", "episode_lapse_min"))
        self.ep_b = _EpisodeTracker(cfg.i("r3_derived", "episode_lapse_min"))
        self.last_hiro: Optional[tuple[float, float, float, float]] = None

    # -- helpers -------------------------------------------------------------
    def _diff(self, series: list[float], k: int) -> Optional[float]:
        i = len(series) - 1
        return series[i] - series[i - k] if i >= k else None

    def _context(self, bar: Bar) -> str:
        """R3.4 at read minutes only. IM missing -> CHOP. SPY VWAP missing -> CHOP."""
        if self.im is None or self.open_0930 is None or self.vwap_den == 0:
            return "CHOP"
        move = bar.close - self.open_0930
        n = min(self.vwap_bars, len(self.spy_closes))
        if n < self.vwap_bars:
            return "CHOP"
        above = sum(1 for c, v in zip(self.spy_closes[-n:], self.vwaps[-n:]) if c > v) / n
        below = sum(1 for c, v in zip(self.spy_closes[-n:], self.vwaps[-n:]) if c < v) / n
        e5, e9, e20 = self.ema[5], self.ema[9], self.ema[20]
        if (move >= self.im_frac * self.im and above >= self.vwap_share and e5 > e9 > e20):
            return "UP"
        if (move <= -self.im_frac * self.im and below >= self.vwap_share and e5 < e9 < e20):
            return "DOWN"
        return "CHOP"

    # -- main ----------------------------------------------------------------
    def update(self, bar: Bar, hiro: Optional[pd.DataFrame],
               spy_bar: Optional[SpyBar]) -> FeatureRow:
        m = bar.min
        if self.open_0930 is None:
            self.open_0930 = bar.open
        self.mins.append(m)
        self.closes.append(bar.close)
        self.highs.append(bar.high)
        # EMAs (1-min closes, adjust=False semantics)
        for span in self.ema:
            a = 2.0 / (span + 1)
            self.ema[span] = bar.close if self.ema[span] is None else \
                a * bar.close + (1 - a) * self.ema[span]
        # SPY VWAP (R2.6)
        vwap = None
        if spy_bar is not None:
            tp = (spy_bar.high + spy_bar.low + spy_bar.close) / 3.0
            self.vwap_num += tp * spy_bar.volume
            self.vwap_den += spy_bar.volume
        if self.vwap_den > 0:
            vwap = self.vwap_num / self.vwap_den
        if spy_bar is not None and vwap is not None:
            self.spy_closes.append(spy_bar.close)
            self.vwaps.append(vwap)
        # HIRO lines (R3.1): value at this bar's minute from the causal frame
        hiro_fresh = hiro is not None and len(hiro) > 0 and hiro["min"].max() >= m
        if hiro is not None and len(hiro):
            hrow = hiro[hiro["min"] <= m].iloc[-1]
            vals = (float(hrow.all_L), float(hrow.all_Lc), float(hrow.all_Lp),
                    float(hrow.nextExp_L))
            self.last_hiro = vals
        if self.last_hiro is None:
            L = Lc = Lp = N = 0.0
        else:
            L, Lc, Lp, N = self.last_hiro
        self.Ls.append(L)
        self.Ns.append(N)
        r5 = self._diff(self.Ls, 5); r15 = self._diff(self.Ls, 15)
        r30 = self._diff(self.Ls, 30); r15n = self._diff(self.Ns, 15)
        rm = self.rm.update(m, L, Lc, Lp, N)
        # R3.3 price windows (strict 30-bar)
        pull30 = bounce30 = mid30 = None
        ref_low_bar = None
        bh_level = None
        if len(self.closes) >= self.roll:
            w = self.closes[-self.roll:]
            pull30 = max(w) - bar.close
            bounce30 = bar.close - min(w)
            mid30 = (max(w) + min(w)) / 2.0
            ref_idx = len(self.closes) - self.roll + int(np.argmin(w))
            ref_low_bar = self.mins[ref_idx]
            bh_level = max(self.highs[ref_idx:])   # highest HIGH from the 30-bar low through this bar
        range60 = None
        if len(self.closes) > self.r60w:
            # prior-60-min high - low (the 60 bars BEFORE this one)
            w60 = self.closes[-self.r60w - 1:-1]
            range60 = max(w60) - min(w60)
        # causal expanding percentile, shifted one bar (history excludes current range60)
        pool = self.r60_history + self.r60_today
        warmup = len(pool) < self.r60_min_obs
        range60_pct = None
        if not warmup:
            range60_pct = float(np.quantile(np.asarray(pool), self.r60_pctile))
        if range60 is not None:
            self.r60_today.append(range60)
        # context (R3.4) at read minutes only
        if m == self.reads[0]:
            self.context_1030 = self._context(bar)
        if m == self.reads[1]:
            self.context_1300 = self._context(bar)
        # condition predicates (single home: rules.py)
        core = _rules.Core(
            min=m, close=bar.close, r15=r15, r30=r30, r15n=r15n,
            run=rm["run"], dur=rm["dur"], rate=rm["rate"], dC=rm["dC"], dP=rm["dP"],
            dN=rm["dN"], cpr=rm["cpr"], share=rm["share"], dd=rm["dd"],
            weak_side=rm["weak_side"],
            pull30=pull30, bounce30=bounce30, mid30=mid30,
            range60=range60, range60_pct=range60_pct, warmup=warmup,
            hiro_fresh=hiro_fresh,
        )
        a_conditions = _rules.a_conditions(core, self.cfg, self.tier)
        b_armed = _rules.b_arm(core, self.cfg) if self.tier.branch_b_enabled else False
        b_gates = _rules.b_gates(core, self.cfg) if b_armed else False
        late_state = _rules.late_state(core, self.cfg)
        episode_a = self.ep_a.update(a_conditions)
        episode_b = self.ep_b.update(b_armed, hard_break=rm["broke"])
        n10 = min(self.vwap_bars, len(self.spy_closes))
        vshare = (sum(1 for c, v in zip(self.spy_closes[-n10:], self.vwaps[-n10:]) if c > v) / n10
                  if n10 else None)
        return FeatureRow(
            min=m, bar=bar, open_0930=self.open_0930,
            L=L, Lc=Lc, Lp=Lp, N=N, r5=r5, r15=r15, r30=r30, r15n=r15n,
            run=rm["run"], dur=rm["dur"], rate=rm["rate"], dC=rm["dC"], dP=rm["dP"],
            dN=rm["dN"], weak_side=rm["weak_side"], share=rm["share"],
            drawdown=rm["dd"], run_broke=rm["broke"],
            pull30=pull30, bounce30=bounce30, mid30=mid30, ref_low_bar=ref_low_bar,
            bh_level=bh_level,
            range60=range60, range60_pct=range60_pct, warmup=warmup,
            ema5=self.ema[5], ema9=self.ema[9], ema20=self.ema[20],
            vwap=vwap, spy_close=(spy_bar.close if spy_bar else None), vwap_share10=vshare,
            context_1030=self.context_1030, context_1300=self.context_1300,
            episode_a=episode_a, episode_b=episode_b,
            a_conditions=a_conditions, b_armed=b_armed, b_gates=b_gates,
            late_state=late_state, hiro_fresh=hiro_fresh,
        )
