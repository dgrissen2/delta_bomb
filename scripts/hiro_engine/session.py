"""Session (task 5b) — the orchestrator. The per-bar contract lives HERE, nowhere else:

    (1) executor.execute_pending at THIS bar's open
    (2) features.update
    (3) Session attaches vetoes/health to the row (FeatureRow is otherwise immutable)
    (4) rules.evaluate at bar close
    (5) executor.apply
    (6) log.emit

Health state machine shell (OK / HIRO_DOWN / SPX_STALLED / DEGRADED_VWAP) is fed
by feed exceptions; the live feed (task 7) supplies the exceptions.
"""
from __future__ import annotations

import csv
import dataclasses
from pathlib import Path
from typing import Optional

from .calendar import CalendarLoader
from .config import Config
from .eventlog import EventLog, rebuild_state
from .executor import Executor
from .features import FeatureEngine
from .feeds import ReplayFeed, load_spx_day
from .instruments import InstrumentSelector
from .levels import LevelsLoader
from .models import Event, EngineState, SessionRow, TierPolicy, Vetoes
from .rules import RuleEngine


class _NullLog:
    """Muted log used during warm crash-resume replay (rows already on disk)."""
    csv_path = None

    def emit(self, events):
        return None


def build_range60_history(cfg: Config, tier: TierPolicy, days_before: list[str]) -> list[float]:
    """Causal pooled range60 history (R3.3): replay prior stored SPX sessions
    through the same window math — one code path, no lookahead."""
    hist: list[float] = []
    w = cfg.i("r3_derived", "range60_window")
    for d in days_before:
        try:
            spx = load_spx_day(cfg.path_of("spx_dir"), d)
        except Exception:
            continue
        g = spx[(spx["min"] >= 570) & (spx["min"] <= 960)]
        highs = [float(x) for x in g.high]
        lows = [float(x) for x in g.low]
        for i in range(w - 1, len(highs)):
            hist.append(max(highs[i - w + 1:i + 1]) - min(lows[i - w + 1:i + 1]))
    return hist


class Session:
    def __init__(self, cfg: Config, tier: TierPolicy, day: str, mode: str,
                 log: EventLog, range60_history: Optional[list[float]] = None,
                 shakedown: bool = False, resume: bool = False,
                 chain_available: bool = False, im: Optional[float] = None):
        self.cfg = cfg
        self.tier = tier
        self.day = day
        self.mode = "shakedown" if shakedown else mode
        self.log = log
        self.levels = LevelsLoader(cfg.path_of("levels_csv")).load(day, im=im)
        self.calendar = CalendarLoader(cfg.path_of("calendar_csv")).check(day)
        self.features = FeatureEngine(cfg, tier, range60_history=range60_history,
                                      im=self.levels.im)
        self.rules = RuleEngine(cfg, tier, selector=InstrumentSelector(cfg))
        self.executor = Executor(cfg, InstrumentSelector(cfg), chain_available=chain_available)
        self.state = rebuild_state(log.csv_path, day) if resume else EngineState()
        self.vt_broken = False
        self.health = "OK"
        self.outage_min = 0
        self.last_bar = None
        self.last_bar_min: Optional[int] = None
        self._stamp_fields = dict(mode=self.mode, tier=tier.tier_stamp, session_date=day,
                                  config_hash=cfg.config_hash)

    # -- stamping ---------------------------------------------------------------
    def _stamp(self, events: list[Event], bar_min: Optional[int]) -> list[Event]:
        hh = f"{bar_min // 60:02d}:{bar_min % 60:02d}" if bar_min is not None else "--:--"
        for ev in events:
            ev.ts = f"{self.day} {hh}"
            ev.mode = self._stamp_fields["mode"]
            ev.tier = self._stamp_fields["tier"]
            ev.session_date = self.day
            ev.config_hash = self._stamp_fields["config_hash"]
            ev.health = self.health
        return events

    # -- startup ------------------------------------------------------------------
    def startup_events(self) -> list[Event]:
        out = [Event(event_type="banner", rule_id="R8.2",
                     notes=f"session start | CONFIG_HASH={self.cfg.config_hash[:12]}… "
                           f"| mode={self.mode} tier={self.tier.tier_stamp}")]
        if self.calendar.is_event_day:
            out.append(Event(event_type="banner", rule_id="R4.4",
                             notes=f"EVENT DAY — STAND DOWN ({self.calendar.reason})"))
            return out
        if not self.levels.valid:
            out.append(Event(event_type="banner", rule_id="R4.2",
                             notes="LEVELS MISSING → LONG-FIRST ONLY"))
        else:
            out.append(Event(event_type="banner", rule_id="R2.3",
                             notes=f"levels valid | VT={self.levels.vt} CW={self.levels.cw} "
                                   f"IM={self.levels.im if self.levels.im is not None else '—'}"))
        return out

    # -- vetoes ---------------------------------------------------------------------
    def _vetoes(self, row) -> Vetoes:
        if self.levels.valid and self.levels.vt is not None and row.bar.close < self.levels.vt:
            self.vt_broken = True            # persists all day (R4.1)
        flow = (self.tier.r43_enabled and row.hiro_fresh
                and row.r15 is not None and row.r15n is not None
                and row.r15 < self.cfg.num("r4_vetoes", "flow_veto_bps")
                and row.r15n < self.cfg.num("r4_vetoes", "flow_veto_bps"))
        return Vetoes(vt_broken=self.vt_broken,
                      levels_invalid=not self.levels.valid,
                      flow_veto=bool(flow))

    # -- health -----------------------------------------------------------------------
    def _health(self, tick) -> str:
        if self.tier.requires_hiro and (
                tick.hiro is None or not len(tick.hiro)
                or int(tick.hiro["min"].max()) < tick.bar.min - 2):   # stale payload
            return "HIRO_DOWN"
        if tick.spy_bar is None:
            return "DEGRADED_VWAP"
        return "OK"

    def observe_gap(self, gap_min: int) -> None:
        """SPX stall span (task 7 feeds this); counts toward outage inside 10:00-14:30."""
        self.outage_min += gap_min

    # -- the per-bar contract -------------------------------------------------------------
    def process_tick(self, tick) -> None:
        bar = tick.bar
        stall_events: list[Event] = []
        if self.last_bar_min is not None and bar.min - self.last_bar_min > 1:
            gap = bar.min - self.last_bar_min - 1
            lo = max(self.last_bar_min + 1, self.cfg.i("r5_clock", "observe_end_min"))
            hi = min(bar.min - 1, self.cfg.i("r5_clock", "entry_end_min"))
            if hi >= lo:
                self.outage_min += hi - lo + 1
            if gap > 2:
                stall_events.append(Event(
                    event_type="outage", rule_id="R10.2",
                    notes=f"SPX_STALLED: {gap}m gap before this bar | "
                          f"outage so far {self.outage_min}m"))
        entry_events = self.executor.execute_pending(bar, self.state)          # (1)
        row = self.features.update(bar, tick.hiro, tick.spy_bar)               # (2)
        prev_health = self.health
        new_health = self._health(tick)
        if new_health == "HIRO_DOWN" and 600 <= bar.min <= 870:
            self.outage_min += 1
        self.health = new_health
        row = dataclasses.replace(row, vetoes=self._vetoes(row), health=self.health)  # (3)
        health_events: list[Event] = []
        if new_health != prev_health:
            note = {"HIRO_DOWN": "HIRO DOWN — no new entries",
                    "DEGRADED_VWAP": "SPY missing — context reads degrade to CHOP (degraded_vwap)",
                    "OK": f"HIRO RESTORED | outage so far {self.outage_min}m",
                    }.get(new_health, new_health)
            if prev_health == "HIRO_DOWN" and new_health != "HIRO_DOWN":
                note = f"HIRO RESTORED | outage so far {self.outage_min}m"
            health_events.append(Event(event_type="outage", rule_id="R10", notes=note))
        rule_events = self.rules.evaluate(row, self.state)                     # (4)
        if self.health == "HIRO_DOWN":
            # R10.1: no new entries while HIRO is down; flow exits already gated by hiro_fresh
            kept = []
            for ev in rule_events:
                if ev.event_type in ("signal", "pending_entry"):
                    kept.append(Event(event_type="skip", rule_id="R10.1", branch=ev.branch,
                                      episode=ev.episode, notes="skip: HIRO down"))
                elif (ev.event_type == "exit_decision"
                      and ev.outcome_type in ("scratch", "veto_exit")
                      and self.state.open_trade is not None
                      and self.state.open_trade.branch == "B"):
                    kept.append(Event(event_type="state_line", rule_id="R10.1",
                                      notes="scratch_unavailable (HIRO down)"))
                else:
                    kept.append(ev)
            rule_events = kept
        trade_events = self.executor.apply(rule_events, row, self.state)       # (5)
        self.log.emit(self._stamp(stall_events + entry_events + health_events + rule_events
                                  + trade_events, bar.min))                    # (6)
        self.last_bar = bar
        self.last_bar_min = bar.min

    # -- crash-resume ------------------------------------------------------------------
    def warm_replay(self, ticks) -> None:
        """Crash-resume (spec NFR): rebuild ALL warm state — FeatureEngine
        windows/EMAs/VWAP/open_0930, run machine, episode trackers, RuleEngine
        per-episode dedup, Session.vt_broken, Executor state — by re-processing
        today's bars with the log MUTED (their rows are already on disk).
        The engine is deterministic, so the replayed state equals the pre-crash
        state; the log-derived EngineState is cross-checked and any divergence
        prints a loud RESUME WARNING."""
        real_log, self.log = self.log, _NullLog()
        try:
            for t in ticks:
                self.process_tick(t)
        finally:
            self.log = real_log
        if real_log.csv_path is not None:
            ref = rebuild_state(real_log.csv_path, self.day)
            a, b = self.state.open_trade, ref.open_trade
            diverged = ((a is None) != (b is None)
                        or (a is not None and b is not None
                            and (a.id != b.id or a.entry_min != b.entry_min
                                 or a.s0 != b.s0))
                        or self.state.entries_today != ref.entries_today)
            if diverged:
                self.log.emit(self._stamp([Event(
                    event_type="banner", rule_id="NFR",
                    notes="RESUME WARNING: replayed state diverges from the logged "
                          "state — inspect paper_log before trusting signals")],
                    self.last_bar_min))

    # -- lifecycle ------------------------------------------------------------------------
    def run_replay(self, feed: ReplayFeed) -> SessionRow:
        self.log.emit(self._stamp(self.startup_events(), None))
        if self.calendar.is_event_day:
            return self.finish(event_standdown=True)
        for tick in feed.iter_day(self.day):
            self.process_tick(tick)
        return self.finish()

    def finish(self, event_standdown: bool = False) -> SessionRow:
        if self.last_bar is not None:
            end_events = self.executor.end_of_session(self.last_bar, self.state)
            self.log.emit(self._stamp(end_events, self.last_bar.min))
        if event_standdown:
            dispo = "event_standdown"
        elif self.mode == "shakedown":
            dispo = "shakedown"
        elif (self.outage_min > 15
              or self.last_bar_min is None or self.last_bar_min < 955):
            dispo = "partial"
        else:
            dispo = "countable"
        row = SessionRow(date=self.day, disposition=dispo, outage_min=self.outage_min,
                         mode=self.mode, config_hash=self.cfg.config_hash)
        self.log.emit(self._stamp([Event(event_type="disposition", rule_id="R10.3",
                                         notes=f"session {dispo} | outage {self.outage_min}m")],
                                  self.last_bar_min))
        self._write_session_row(row)
        return row

    def _write_session_row(self, row: SessionRow) -> None:
        p = Path(self.cfg.get("logging", "sessions_log"))
        if not p.is_absolute():
            from .config import REPO_ROOT
            p = REPO_ROOT / p
        if self.mode == "backtest":
            p = p.with_name("sessions_backtest.csv")   # never contaminate the live record
        p.parent.mkdir(parents=True, exist_ok=True)
        new = not p.exists() or p.stat().st_size == 0
        with open(p, "a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["date", "disposition", "outage_min",
                                               "mode", "config_hash"])
            if new:
                w.writeheader()
            w.writerow(dataclasses.asdict(row))
