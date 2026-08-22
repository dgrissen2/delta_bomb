"""EventLog (R8.1) — ONE formatter: the console line and the CSV row are the
same Event, rendered twice. Append-only. On startup with an existing file for
today: replay it to rebuild EngineState (crash-resume, spec NFR)."""
from __future__ import annotations

import csv
import sys
from dataclasses import asdict, fields
from pathlib import Path
from typing import Optional, TextIO

from .models import EVENT_FIELDS, EngineState, Event, PendingEntry, SimTrade

_FLOAT_FIELDS = {"s0", "run", "rate", "dC", "dP", "share", "r15", "pull30", "bounce30",
                 "outcome_minutes", "exit_ref", "resolution_debit", "adverse",
                 "entry_option_mid", "resting_limit_ref", "target", "bh_level",
                 "entry_L", "cap_value"}
_INT_FIELDS = {"schema_v", "trade_id", "entry_min", "signal_min", "episode"}


def _hhmm(m: Optional[int]) -> str:
    return f"{m // 60:02d}:{m % 60:02d}" if m is not None else "--:--"


def format_console(ev: Event) -> str:
    """Human rendering of the SAME fields that go to CSV."""
    bits = [ev.ts, ev.mode, f"tier={ev.tier}", ev.event_type.upper()]
    if ev.rule_id:
        bits.append(ev.rule_id)
    if ev.branch:
        bits.append(f"{ev.branch}/{ev.side}" if ev.side else ev.branch)
    if ev.s0 is not None:
        bits.append(f"S0={ev.s0:.2f}")
    if ev.run is not None:
        def _f(v, fmt):
            return (fmt % v) if v is not None else "—"
        bits.append(f"run={_f(ev.run, '%.2f')}$B rate={_f(ev.rate, '%.1f')} "
                    f"dC={_f(ev.dC, '%.2f')} dP={_f(ev.dP, '%.2f')} "
                    f"share={_f(ev.share, '%.2f')} r15={_f(ev.r15, '%.2f')}")
    if ev.outcome_type:
        bits.append(f"-> {ev.outcome_type}"
                    + (f" in {ev.outcome_minutes:.0f}m" if ev.outcome_minutes is not None else ""))
    if ev.exit_ref is not None:
        bits.append(f"exit_ref={ev.exit_ref:.2f}")
    if ev.cap_source:
        bits.append(f"cap={ev.cap_source}")
    if ev.adverse is not None:
        bits.append(f"adverse={ev.adverse:.2f}")
    if ev.health and ev.health != "OK":
        bits.append(f"[{ev.health}]")
    if ev.notes:
        bits.append(ev.notes)
    return " | ".join(str(b) for b in bits if str(b) != "")


def event_to_row(ev: Event) -> dict:
    d = asdict(ev)
    return {k: ("" if d[k] is None else d[k]) for k in EVENT_FIELDS}


def event_from_row(row: dict) -> Event:
    kw = {}
    for f in EVENT_FIELDS:
        v = row.get(f, "")
        if v == "" or v is None:
            kw[f] = None if (f in _FLOAT_FIELDS or f in _INT_FIELDS
                             or f in ("expiry", "leg_strikes", "strike_quote_ts", "context",
                                      "outcome_type", "cap_source")) else ""
        elif f in _FLOAT_FIELDS:
            kw[f] = float(v)
        elif f in _INT_FIELDS:
            kw[f] = int(float(v))
        else:
            kw[f] = str(v)
    if kw["schema_v"] is None:
        kw["schema_v"] = 1
    return Event(**kw)


class EventLog:
    def __init__(self, csv_path: Path, console: TextIO = sys.stdout, echo: bool = True):
        self.csv_path = Path(csv_path)
        self.console = console
        self.echo = echo
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        new = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        self._fh = open(self.csv_path, "a", newline="")
        self._w = csv.DictWriter(self._fh, fieldnames=EVENT_FIELDS)
        if new:
            self._w.writeheader()

    def emit(self, events: list[Event]) -> None:
        for ev in events:
            self._w.writerow(event_to_row(ev))
            if self.echo:
                print(format_console(ev), file=self.console)
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()


def trade_from_entry_event(ev: Event) -> SimTrade:
    return SimTrade(
        id=ev.trade_id, branch=ev.branch, side=ev.side, signal_min=ev.signal_min,
        entry_min=ev.entry_min, s0=ev.s0, expiry=ev.expiry, leg_strikes=ev.leg_strikes,
        entry_option_mid=ev.entry_option_mid, resting_limit_ref=ev.resting_limit_ref,
        target=ev.target, bh_level=ev.bh_level, entry_L=ev.entry_L,
        cap_source=ev.cap_source or "proxy", cap_value=ev.cap_value,
        episode=ev.episode)


def apply_exit_event(tr: SimTrade, ev: Event) -> SimTrade:
    tr.state = "closed"
    tr.exit_type = ev.outcome_type
    tr.exit_ref = ev.exit_ref
    tr.minutes = int(ev.outcome_minutes) if ev.outcome_minutes is not None else None
    tr.resolution_debit = ev.resolution_debit
    tr.adverse = ev.adverse if ev.adverse is not None else tr.adverse
    return tr


def rebuild_state(csv_path: Path, session_date: str) -> EngineState:
    """Crash-resume: replay today's rows and reconstruct EngineState."""
    state = EngineState()
    if not Path(csv_path).exists():
        return state
    with open(csv_path, newline="") as fh:
        for raw in csv.DictReader(fh):
            if raw.get("session_date") != session_date:
                continue
            ev = event_from_row(raw)
            if ev.event_type == "pending_entry":
                state.pending_entry = PendingEntry(
                    branch=ev.branch, side=ev.side, signal_min=ev.signal_min,
                    episode=ev.episode, expiry=ev.expiry, strike_hint=ev.leg_strikes,
                    chain_quote_ts=ev.strike_quote_ts, bh_level=ev.bh_level,
                    entry_L=ev.entry_L)
            elif ev.event_type == "entry":
                state.pending_entry = None
                state.open_trade = trade_from_entry_event(ev)
                state.entries_today += 1
                state.next_trade_id = max(state.next_trade_id, (ev.trade_id or 0) + 1)
                if ev.branch == "A":
                    state.entered_episode_a = ev.episode
                else:
                    state.entered_episode_b = ev.episode
            elif ev.event_type == "exit" and state.open_trade is not None:
                apply_exit_event(state.open_trade, ev)
                state.open_trade = None
                state.pending_exit = None
            elif ev.event_type == "exit_decision" and state.open_trade is not None:
                if ev.outcome_type not in ("fill", "resolution"):
                    state.pending_exit = ev.outcome_type
    return state
