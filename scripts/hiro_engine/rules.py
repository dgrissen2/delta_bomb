"""RuleEngine (R4-R7) — the ONLY owner of ALL condition logic.

Pure: no I/O, no clock access. evaluate(row, state) -> list[Event].
Module-level predicates are the single home of the R6 condition sets; the
FeatureEngine imports them for episode tracking (R3.5) so conditions are never
defined twice.

Interpretation notes (frozen decisions, see docs/hiro_engine/build_notes.md):
- R5.2 windows bind the SIGNAL minute (research convention: B fires t <= 14:30,
  executes next open). Signals need t >= 10:00 (A: >= 10:35).
- R7.3 spot-proxy cap compares the bar CLOSE to S0 (evaluated at bar close).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import Config
from .models import EngineState, Event, FeatureRow, PendingEntry, TierPolicy


# ---------------------------------------------------------------------------
# Condition predicates (single home)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Core:
    """The minimal field set the predicates need (FeatureEngine supplies it)."""
    min: int
    close: float
    r15: Optional[float]
    r30: Optional[float]
    r15n: Optional[float]
    run: float
    dur: float
    rate: float
    dC: float
    dP: float
    dN: float
    cpr: float
    share: Optional[float]
    dd: float
    weak_side: float
    pull30: Optional[float]
    bounce30: Optional[float]
    mid30: Optional[float]
    range60: Optional[float]
    range60_pct: Optional[float]
    warmup: bool
    hiro_fresh: bool


def a_conditions(c: Core, cfg: Config, tier: TierPolicy) -> bool:
    """R6.1 (i)-(iv); price tier drops (ii) r30<0 (R13.1)."""
    if c.warmup or c.range60 is None or c.range60_pct is None:
        return False
    if c.bounce30 is None or c.mid30 is None:
        return False
    cond = (c.range60 >= c.range60_pct
            and c.bounce30 >= cfg.num("r6_entries", "a_bounce_min_pts")
            and c.close < c.mid30)
    if not tier.price_a_conditions:
        cond = cond and (c.r30 is not None and c.r30 < 0) and c.hiro_fresh
    return bool(cond)


def b_aligned(c: Core, cfg: Config) -> bool:
    """R6.2 run conditions (research 'aligned'), without the pullback."""
    if not c.hiro_fresh:
        return False
    e = cfg.section("r6_entries")
    return bool(c.dur >= e["b_dur_min"] and c.rate >= e["b_rate_min"]
                and c.dC > 0 and c.dP > 0
                and c.cpr == c.cpr and c.cpr >= e["b_cpr_min"]   # cpr==cpr filters NaN
                and c.dN > 0 and c.share is not None and c.share >= e["b_share_min"]
                and c.dd < cfg.num("r3_derived", "run_break_dd"))


def b_arm(c: Core, cfg: Config) -> bool:
    """R6.2 ARM = aligned run + pullback >= 3 (strict 30-bar pull30)."""
    return bool(b_aligned(c, cfg) and c.pull30 is not None
                and c.pull30 >= cfg.num("r6_entries", "b_pull_min_pts"))


def b_gates(c: Core, cfg: Config) -> bool:
    """R6.2 GATES: r15 > 0; time <= 14:30; weak side >= 0.15."""
    e = cfg.section("r6_entries")
    return bool(c.r15 is not None and c.r15 > 0
                and c.min <= cfg.i("r5_clock", "entry_end_min")
                and c.weak_side >= e["b_weak_side_min"])


def late_state(c: Core, cfg: Config) -> bool:
    """R6.3 suppression state: rate >= 4 $B/hr AND r30 >= 1.0 $B."""
    e = cfg.section("r6_entries")
    return bool(c.hiro_fresh and c.rate >= e["late_rate"]
                and c.r30 is not None and c.r30 >= e["late_r30"])


# ---------------------------------------------------------------------------
# RuleEngine
# ---------------------------------------------------------------------------
EXIT_PRECEDENCE = ["fill", "scratch", "cap", "veto_exit", "state_flip", "clock", "resolution"]


class RuleEngine:
    """Per-session instance. evaluate() is called once per completed bar, after
    Session attached vetoes/health to the row and after the Executor executed
    any pending entry at this bar's open."""

    def __init__(self, cfg: Config, tier: TierPolicy, selector=None):
        self.cfg = cfg
        self.tier = tier
        self.selector = selector           # InstrumentSelector for R1.2 hints (optional)
        self.k = dict(cfg.section("r5_clock"))
        self.reads = [int(x) for x in cfg.get("r3_derived", "context_reads_min")]
        self.e6 = cfg.section("r6_entries")
        self.e7 = cfg.section("r7_exits")
        self._last_vetoes = None
        self._late_logged_episode: Optional[int] = None
        self._gatefail_logged_episode: Optional[int] = None
        self._warmup_logged = False
        self._skip_logged: set = set()             # (branch, episode, reason) dedup
        self._scratch_unavail_trade: Optional[int] = None

    # -- entries --------------------------------------------------------------
    def _entry_events(self, row: FeatureRow, state: EngineState) -> list[Event]:
        out: list[Event] = []
        m = row.min
        in_window = self.k["observe_end_min"] <= m <= self.k["entry_end_min"]
        a_ok_time = m >= self.k["branch_a_start_min"]
        short_blocked = (row.vetoes.vt_broken or row.vetoes.levels_invalid
                         or (row.vetoes.flow_veto and self.tier.r43_enabled))

        # R11.1: an A episode qualifies only if its FIRST minute is inside the
        # A window (>= 10:35); an episode that started earlier never fires
        a_fires = (row.a_conditions and row.episode_a is not None
                   and state.entered_episode_a != row.episode_a and in_window and a_ok_time
                   and row.episode_a_start is not None
                   and row.episode_a_start >= self.k["branch_a_start_min"])
        b_qualifies = (self.tier.branch_b_enabled and row.b_armed and row.b_gates
                       and row.episode_b is not None
                       and state.entered_episode_b != row.episode_b and in_window)
        # R6.3 late suppression: one line per episode
        if (self.tier.branch_b_enabled and row.b_armed and row.late_state
                and row.episode_b is not None
                and self._late_logged_episode != row.episode_b and in_window):
            ev = Event(event_type="late_no_entry", rule_id="R6.3", branch="B",
                       episode=row.episode_b, signal_min=m, notes="LATE — NO ENTRY")
            ev.run, ev.rate, ev.r15 = row.run, row.rate, row.r15
            out.append(ev)
            self._late_logged_episode = row.episode_b
        # armed-episode gate failure: one line per episode (R8.1)
        if (self.tier.branch_b_enabled and row.b_armed and not row.b_gates
                and row.episode_b is not None
                and self._gatefail_logged_episode != row.episode_b and in_window):
            fails = []
            if not (row.r15 is not None and row.r15 > 0):
                fails.append("r15<=0")
            if m > self.k["entry_end_min"]:
                fails.append("t>14:30")
            if row.weak_side < self.e6["b_weak_side_min"]:
                fails.append("weak_side<0.15")
            ev = Event(event_type="gate_fail", rule_id="R6.2", branch="B",
                       episode=row.episode_b, signal_min=m,
                       notes="gates failed: " + ",".join(fails))
            ev.run, ev.rate, ev.dC, ev.dP, ev.share, ev.r15 =                 row.run, row.rate, row.dC, row.dP, row.share, row.r15
            out.append(ev)
            self._gatefail_logged_episode = row.episode_b

        b_fires = b_qualifies and not row.late_state and not short_blocked

        def _stamp_conditions(ev: Event) -> Event:
            ev.run, ev.rate, ev.dC, ev.dP = row.run, row.rate, row.dC, row.dP
            ev.share, ev.r15 = row.share, row.r15
            ev.pull30, ev.bounce30 = row.pull30, row.bounce30
            return ev

        def _skip(branch: str, episode: Optional[int], reason: str) -> Optional[Event]:
            key = (branch, episode, reason)
            if key in self._skip_logged:
                return None
            self._skip_logged.add(key)
            return _stamp_conditions(Event(event_type="skip", rule_id="R6.4", branch=branch,
                                           episode=episode, signal_min=m,
                                           notes=f"skip: {reason}"))

        # blocking reasons shared by both branches
        def _blocked_reason() -> Optional[str]:
            if state.open_trade is not None or state.pending_entry is not None:
                return "one unpaired leg at a time"
            if state.entries_today >= self.e6["entries_per_day"]:
                return "3 entries/day reached"
            return None

        chosen: Optional[str] = None
        if a_fires:
            reason = _blocked_reason()
            if reason:
                ev = _skip("A", row.episode_a, reason)
                if ev: out.append(ev)
            else:
                chosen = "A"
        if b_qualifies and chosen != "A":
            if b_fires:
                reason = _blocked_reason()
                if reason:
                    ev = _skip("B", row.episode_b, reason)
                    if ev: out.append(ev)
                else:
                    chosen = "B"
            elif short_blocked:
                why = ("vt_broken" if row.vetoes.vt_broken else
                       "levels_invalid" if row.vetoes.levels_invalid else "flow_veto")
                ev = _skip("B", row.episode_b, f"short blocked: {why} (R4)")
                if ev: out.append(ev)
        elif b_fires and chosen == "A":
            ev = _skip("B", row.episode_b, "A beats B on the same bar")
            if ev: out.append(ev)

        if chosen == "A":
            hint = f" | {self.selector.hint('long_first')}" if self.selector else ""
            out.append(_stamp_conditions(Event(
                event_type="signal", rule_id="R6.1", branch="A",
                side="long_first", signal_min=m, episode=row.episode_a,
                notes=(f"SIGNAL A LONG-FIRST{hint} | range60={row.range60:.2f}"
                       f">=p75 {row.range60_pct:.2f} r30={row.r30:.2f} "
                       f"bounce30={row.bounce30:.2f} close<mid30={row.mid30:.2f}"))))
            out.append(Event(event_type="pending_entry", rule_id="R6.1", branch="A",
                             side="long_first", signal_min=m, episode=row.episode_a,
                             bh_level=row.bh_level))
        elif chosen == "B":
            hint = f" | {self.selector.hint('sell_first')}" if self.selector else ""
            out.append(_stamp_conditions(Event(
                event_type="signal", rule_id="R6.2", branch="B",
                side="sell_first", signal_min=m, episode=row.episode_b,
                notes=(f"SIGNAL B SELL-FIRST{hint} | run={row.run:.2f}$B/"
                       f"{row.dur:.0f}m rate={row.rate:.1f} weak={row.weak_side:.2f} "
                       f"share={row.share:.2f} r15={row.r15:.2f} pull30={row.pull30:.2f}"))))
            out.append(Event(event_type="pending_entry", rule_id="R6.2", branch="B",
                             side="sell_first", signal_min=m, episode=row.episode_b,
                             entry_L=row.L))
        return out

    # -- exits ------------------------------------------------------------------
    def _exit_decision(self, row: FeatureRow, state: EngineState) -> Optional[Event]:
        tr = state.open_trade
        if tr is None:
            return None
        m, bar = row.min, row.bar
        sell = tr.side == "sell_first"

        def ev(kind: str, rule: str, **kw) -> Event:
            return Event(event_type="exit_decision", rule_id=rule, branch=tr.branch,
                         side=tr.side, trade_id=tr.id, outcome_type=kind, **kw)

        # R7.1 fill (highest precedence)
        if (sell and bar.high >= tr.target) or (not sell and bar.low <= tr.target):
            return ev("fill", "R7.1")
        # R7.2 scratch
        if tr.branch == "B" and self.tier.r72_enabled and row.hiro_fresh:
            if (m - tr.entry_min) <= self.e7["scratch_window_min"] and tr.entry_L is not None:
                if row.L <= tr.entry_L - self.e7["scratch_drop_bps"] or row.run_broke:
                    return ev("scratch", "R7.2")
        if tr.branch == "A" and tr.bh_level is not None and bar.high > tr.bh_level:
            return ev("scratch", "R7.2")

        # R7.3 cap: chain path uses the option-mid move Session attaches live;
        # proxy path uses SPX vs S0 at the bar close
        adverse_move = (tr.s0 - bar.close) if sell else (bar.close - tr.s0)
        if tr.cap_source == "chain":
            if row.option_mid_move is not None:
                if row.option_mid_move >= tr.cap_value:
                    return ev("cap", "R7.3", cap_source="chain")
            elif adverse_move >= self.e7["cap_spot_pts"]:
                # chain quote unavailable this bar -> spot-proxy fallback so a
                # live trade is NEVER capless (R2.5 "chain call fails" path)
                return ev("cap", "R7.3", cap_source="proxy_fallback")
        else:
            if adverse_move >= tr.cap_value:
                return ev("cap", "R7.3", cap_source="proxy")
        # R7.4 veto exit / state flip (veto_exit before state_flip on ties)
        if sell and row.vetoes.flow_veto and self.tier.r43_enabled:
            return ev("veto_exit", "R7.4")
        if m == self.reads[1] and row.context_1300 is not None:
            if sell and row.context_1300 == "DOWN":
                return ev("state_flip", "R7.4")
            if not sell and row.context_1300 == "UP":
                return ev("state_flip", "R7.4")
        # R7.5 clock
        if (m - tr.entry_min) >= self.k["clock_minutes"] and m < self.k["resolution_min"]:
            return ev("clock", "R7.5")
        # R7.6 resolution at the 15:30 bar
        if m >= self.k["resolution_min"]:
            return ev("resolution", "R7.6")
        return None

    # -- main --------------------------------------------------------------------
    def evaluate(self, row: FeatureRow, state: EngineState) -> list[Event]:
        out: list[Event] = []
        # veto transitions
        if self._last_vetoes != row.vetoes:
            if self._last_vetoes is not None or (row.vetoes.vt_broken or
                                                 row.vetoes.levels_invalid or row.vetoes.flow_veto):
                out.append(Event(event_type="veto_change", rule_id="R4",
                                 notes=f"vetoes: vt_broken={row.vetoes.vt_broken} "
                                       f"levels_invalid={row.vetoes.levels_invalid} "
                                       f"flow_veto={row.vetoes.flow_veto}"))
            self._last_vetoes = row.vetoes
        # warmup notice once
        if row.warmup and not self._warmup_logged:
            out.append(Event(event_type="state_line", rule_id="R3.3", notes="warmup: range60_pct history below min obs — Branch A inactive"))
            self._warmup_logged = True
        # context reads
        if row.min == self.reads[0] and row.context_1030 is not None:
            out.append(Event(event_type="state_line", rule_id="R3.4", context=row.context_1030,
                             notes=f"10:30 context read: {row.context_1030}"))
        if row.min == self.reads[1] and row.context_1300 is not None:
            out.append(Event(event_type="state_line", rule_id="R3.4", context=row.context_1300,
                             notes=f"13:00 context read: {row.context_1300}"))
        # R10.1: flow-exit inputs missing while a B short is carried -> one line per trade
        tr0 = state.open_trade
        if (tr0 is not None and tr0.branch == "B" and self.tier.r72_enabled
                and not row.hiro_fresh and self._scratch_unavail_trade != tr0.id
                and (row.min - tr0.entry_min) <= self.e7["scratch_window_min"]):
            out.append(Event(event_type="state_line", rule_id="R10.1", trade_id=tr0.id,
                             notes="scratch_unavailable (HIRO down)"))
            self._scratch_unavail_trade = tr0.id
        # exits first (they apply to the open trade before new entries can matter;
        # entry evaluation below still sees the trade as open this bar — one leg at a time)
        exit_ev = self._exit_decision(row, state)
        if exit_ev is not None:
            out.append(exit_ev)
        # heartbeat while open (before exit executes — executor prices exits next bar)
        tr = state.open_trade
        if (tr is not None and exit_ev is None and row.min > tr.entry_min
                and (row.min - tr.entry_min) % self.e7["heartbeat_min"] == 0):
            adverse = (tr.s0 - row.bar.low) if tr.side == "sell_first" else (row.bar.high - tr.s0)
            out.append(Event(event_type="heartbeat", rule_id="R8.1", branch=tr.branch,
                             side=tr.side, trade_id=tr.id,
                             notes=f"open {row.min - tr.entry_min}m, clock "
                                   f"{self.k['clock_minutes'] - (row.min - tr.entry_min)}m left, "
                                   f"adverse-so-far {max(0.0, adverse):.2f}"))
        # entries (only during trading; R4.4 event days never reach evaluate())
        out.extend(self._entry_events(row, state))
        return out
