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
                 chain_available: bool = False, im: Optional[float] = None,
                 chains=None):
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
        self.selector = InstrumentSelector(cfg)
        self.executor = Executor(cfg, self.selector, tier=tier)
        self.chains = chains
        if tier.fill_mode == "limit" and chains is None:
            raise ValueError("fill_mode=limit requires a ChainStore (R2.5)")
        self.quote_gap_streak = 0
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
        if (self.tier.fill_mode == "limit" and self.chains is not None
                and not self._option_feed_ok(tick.bar.min)):
            return "OPTION_QUOTES_DOWN"
        if tick.spy_bar is None:
            return "DEGRADED_VWAP"
        return "OK"

    def _option_feed_ok(self, minute: int) -> bool:
        """R10.4 live lifecycle: is the option feed serving ANY data this
        minute? Replay caches always are; a live ChainStore reports outages
        via `feed_ok` (task 19 wires the real check). FakeChains in tests may
        override feed_ok to simulate a 10-minute outage."""
        probe = getattr(self.chains, "feed_ok", None)
        if probe is None:
            return True
        return bool(probe(self.day, minute))

    def _quotes_for(self, minute: int):
        """QuoteView for the two working strikes this minute (limit mode)."""
        if self.tier.fill_mode != "limit" or self.chains is None:
            return None
        tr = self.state.open_trade
        pe = self.state.pending_entry
        k1 = k2 = None
        if tr is not None:
            k1, k2 = tr.k1, tr.k2
        elif pe is not None:
            k1, k2 = pe.k1, pe.k2
        return self.chains.quote_view(self.day, minute, k1, k2)

    def _count_gap(self, quote_view) -> None:
        """R10.4: streak of minutes without a valid working-strike quote while
        a limit rests (Session counts; RuleEngine arbitrates the cancel)."""
        tr = self.state.open_trade
        if (self.tier.fill_mode == "limit" and tr is not None and tr.limit is not None
                and tr.limit.status == "resting"):
            q2 = quote_view.leg2 if quote_view is not None else None
            self.quote_gap_streak = 0 if (q2 is not None and q2.valid)                 else self.quote_gap_streak + 1
        else:
            self.quote_gap_streak = 0

    def _resolve_instruments(self, events, row):
        """R1.2 (v3.0): a fresh PendingEntry gets {expiry, K, K2} from the
        SIGNAL-minute chain snapshot; snapshot unusable -> entry aborted
        (signal remains, stays qualifying)."""
        if self.tier.fill_mode != "limit":
            return events
        out = []
        for ev in events:
            if ev.event_type == "pending_entry":
                snap = self.chains.signal_snapshot(self.day, row.min)
                side = ev.side
                k1, k2 = (self.selector.pick_from_snapshot(snap, side)
                          if len(snap) else (None, None))
                if k1 is None:
                    out.append(Event(event_type="entry_aborted_no_quote", rule_id="R10.4",
                                     branch=ev.branch, side=side, signal_min=ev.signal_min,
                                     episode=ev.episode,
                                     notes="entry ABORTED — signal-minute chain snapshot "
                                           "unusable (R10.4); signal remains qualifying"))
                    continue
                ev.k1, ev.k2 = k1, k2
                ev.expiry = self.chains.expiry_of(self.day)
                ev.leg_strikes = f"{k1:.0f}/{k2:.0f}"
                out.append(ev)
            else:
                out.append(ev)
        return out

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
        start_quotes = self._quotes_for(bar.min)                               # (0) this bar's NBBO
        entry_events = self.executor.execute_pending(bar, self.state,
                                                     quotes=start_quotes)      # (1)
        row = self.features.update(bar, tick.hiro, tick.spy_bar)               # (2)
        prev_health = self.health
        new_health = self._health(tick)
        if new_health in ("HIRO_DOWN", "OPTION_QUOTES_DOWN") and 600 <= bar.min <= 870:
            self.outage_min += 1
        self.health = new_health
        quote_view = self._quotes_for(bar.min)
        self._count_gap(quote_view)
        row = dataclasses.replace(row, vetoes=self._vetoes(row), health=self.health,
                                  quote_view=quote_view,
                                  quote_gap_streak=self.quote_gap_streak)      # (3)
        health_events: list[Event] = []
        if new_health != prev_health:
            note = {"HIRO_DOWN": "HIRO DOWN — no new entries",
                    "OPTION_QUOTES_DOWN": "NO OPTION QUOTES — STAND DOWN from new entries "
                                          "(open leg keeps cap/clock/resolution guards)",
                    "DEGRADED_VWAP": "SPY missing — context reads degrade to CHOP (degraded_vwap)",
                    "OK": f"feed RESTORED | outage so far {self.outage_min}m",
                    }.get(new_health, new_health)
            if prev_health == "HIRO_DOWN" and new_health != "HIRO_DOWN":
                note = f"HIRO RESTORED | outage so far {self.outage_min}m"
            health_events.append(Event(event_type="outage", rule_id="R10", notes=note))
        rule_events = self.rules.evaluate(row, self.state)                     # (4)
        rule_events = self._resolve_instruments(rule_events, row)              # (4b) R1.2 at signal minute
        if self.health in ("HIRO_DOWN", "OPTION_QUOTES_DOWN"):
            # R10.1: no new entries while HIRO is down; flow exits already gated by hiro_fresh
            kept = []
            for ev in rule_events:
                if ev.event_type in ("signal", "pending_entry"):
                    why = ("HIRO down" if self.health == "HIRO_DOWN"
                           else "option quotes down (R10.4)")
                    kept.append(Event(event_type="skip", rule_id="R10.1", branch=ev.branch,
                                      episode=ev.episode, notes=f"skip: {why}"))
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
            def _lim(t):
                return (t.limit.price, t.limit.status) if (t and t.limit) else None
            diverged = ((a is None) != (b is None)
                        or (a is not None and b is not None
                            and (a.id != b.id or a.entry_min != b.entry_min
                                 or a.s0 != b.s0
                                 or a.leg1_fill != b.leg1_fill
                                 or _lim(a) != _lim(b)
                                 or a.exit_type != b.exit_type))
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
            end_events = self.executor.end_of_session(
                self.last_bar, self.state, quotes=self._quotes_for(self.last_bar.min))
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
