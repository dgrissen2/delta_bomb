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
                 "entry_L", "cap_value",
                 "k1", "k2", "leg1_fill", "limit_price", "leg2_fill", "credit",
                 "last_valid_bid", "last_valid_ask", "leg_liq_loss_usd",
                 "spx_adverse_pts", "pnl_usd"}
_INT_FIELDS = {"schema_v", "trade_id", "entry_min", "signal_min", "episode",
               "first_eligible_min", "quote_age", "quote_gap_streak",
               "last_valid_quote_min"}
_BOOL_FIELDS = {"data_invalid"}


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
            kw[f] = None if (f in _FLOAT_FIELDS or f in _INT_FIELDS or f in _BOOL_FIELDS
                             or f in ("expiry", "leg_strikes", "strike_quote_ts", "context",
                                      "outcome_type", "cap_source", "limit_status",
                                      "limit_cancel_reason")) else ""
        elif f in _FLOAT_FIELDS:
            kw[f] = float(v)
        elif f in _INT_FIELDS:
            kw[f] = int(float(v))
        elif f in _BOOL_FIELDS:
            kw[f] = str(v) in ("True", "true", "1")
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
    from .models import RestingLimit
    lim = None
    if ev.limit_price is not None:
        lim = RestingLimit(side=("buy" if ev.side == "sell_first" else "sell"),
                           strike=ev.k2, price=ev.limit_price,
                           placed_min=ev.entry_min,
                           first_eligible_min=ev.first_eligible_min,
                           status=ev.limit_status or "resting",
                           cancel_reason=ev.limit_cancel_reason)
    return SimTrade(
        id=ev.trade_id, branch=ev.branch, side=ev.side, signal_min=ev.signal_min,
        entry_min=ev.entry_min, s0=ev.s0, expiry=ev.expiry, leg_strikes=ev.leg_strikes,
        entry_option_mid=ev.entry_option_mid, resting_limit_ref=ev.resting_limit_ref,
        target=ev.target, bh_level=ev.bh_level, entry_L=ev.entry_L,
        cap_source=ev.cap_source or "proxy", cap_value=ev.cap_value,
        episode=ev.episode, k1=ev.k1, k2=ev.k2, leg1_fill=ev.leg1_fill, limit=lim,
        leg2_fill=ev.leg2_fill, credit=ev.credit,
        quote_gap_streak=ev.quote_gap_streak or 0,
        data_invalid=bool(ev.data_invalid),
        leg_liq_loss_usd=ev.leg_liq_loss_usd or 0.0,
        last_valid_bid=ev.last_valid_bid, last_valid_ask=ev.last_valid_ask,
        last_valid_quote_min=ev.last_valid_quote_min)


def apply_exit_event(tr: SimTrade, ev: Event) -> SimTrade:
    tr.state = "closed"
    tr.exit_type = ev.outcome_type
    tr.exit_ref = ev.exit_ref
    tr.minutes = int(ev.outcome_minutes) if ev.outcome_minutes is not None else None
    tr.adverse = ev.adverse if ev.adverse is not None else tr.adverse
    tr.leg2_fill = ev.leg2_fill if ev.leg2_fill is not None else tr.leg2_fill
    tr.credit = ev.credit if ev.credit is not None else tr.credit
    tr.pnl_usd = ev.pnl_usd
    tr.data_invalid = bool(ev.data_invalid) or tr.data_invalid
    if tr.limit is not None and ev.limit_status:
        tr.limit.status = ev.limit_status
        tr.limit.cancel_reason = ev.limit_cancel_reason
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
                    entry_L=ev.entry_L, k1=ev.k1, k2=ev.k2)
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
            elif ev.event_type == "limit_canceled" and state.open_trade is not None:
                tr = state.open_trade
                if tr.limit is not None:
                    tr.limit.status = "canceled"
                    tr.limit.cancel_reason = ev.limit_cancel_reason or "quote_gap"
                if ev.limit_cancel_reason == "quote_gap":
                    tr.data_invalid = True          # ONLY quote_gap unscores (BP2 F11)
            elif ev.event_type in ("heartbeat", "quote_gap") and state.open_trade is not None:
                tr = state.open_trade
                if ev.quote_gap_streak is not None:
                    tr.quote_gap_streak = ev.quote_gap_streak
                if ev.last_valid_quote_min is not None:
                    tr.last_valid_bid = ev.last_valid_bid
                    tr.last_valid_ask = ev.last_valid_ask
                    tr.last_valid_quote_min = ev.last_valid_quote_min
                if ev.leg_liq_loss_usd is not None:
                    tr.leg_liq_loss_usd = max(tr.leg_liq_loss_usd, ev.leg_liq_loss_usd)
                if ev.spx_adverse_pts is not None:
                    tr.adverse = max(tr.adverse, ev.spx_adverse_pts)
            elif ev.event_type == "entry_aborted_no_quote":
                state.pending_entry = None
    return state


# =============================================================================
# Snapshot sidecar (v3.0, 15f FROZEN CONTRACT — task 19 wires the live writer,
# it may not change this format). One row per evaluated minute while a trade/
# limit is live; doubles as the parity-gate capture and the live-resume quote
# source (logged decisions stay authoritative).
# =============================================================================
# CONTRACT AMENDMENT 2026-08-23 (pre-shakedown, no captures exist): +"side"
# ("buy"|"sell", the RESTING limit's side) — parity needs it (codex BP2 F3).
SIDECAR_COLUMNS = ["minute", "strike", "side", "bid", "ask", "limit_price",
                   "marketable", "decision"]


class QuoteSidecar:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.rows: list[dict] = []

    def record(self, minute: int, strike: float, side: str, bid, ask, limit_price,
               marketable: bool, decision: str) -> None:
        self.rows.append(dict(minute=minute, strike=strike, side=side, bid=bid,
                              ask=ask, limit_price=limit_price,
                              marketable=bool(marketable), decision=decision))

    def flush(self) -> None:
        import pandas as pd
        self.path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.rows, columns=SIDECAR_COLUMNS).to_parquet(self.path, index=False)

    @staticmethod
    def load(path: Path):
        import pandas as pd
        return pd.read_parquet(path)

    @staticmethod
    def quote_source(path: Path):
        """Resume quote source: {(minute, strike): (bid, ask)} from a sidecar."""
        df = QuoteSidecar.load(path)
        return {(int(r.minute), float(r.strike)): (r.bid, r.ask)
                for r in df.itertuples() if r.bid == r.bid}
