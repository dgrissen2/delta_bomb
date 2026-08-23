"""Executor — a pure STATE APPLIER, no trading judgment (design.md).

Order per bar: (1) execute_pending at THIS bar's open (pending exits priced,
then pending entry -> S0 = this open, R1.4); (2) rules evaluated elsewhere;
(3) apply() hands the bar's ExitDecision its execution price per R7.0 and
updates EngineState. One owner per rule: conditions in rules.py, state/prices here.
"""
from __future__ import annotations

from typing import Optional

from .config import Config
from .instruments import InstrumentSelector
from .models import Bar, EngineState, Event, FeatureRow, PendingEntry, SimTrade


class Executor:
    def __init__(self, cfg: Config, selector: InstrumentSelector, chain_available: bool = False):
        self.cfg = cfg
        self.sel = selector
        self.chain_available = chain_available
        self.fill_pts = cfg.num("r1_instruments", "fill_touch_pts")
        self.cap_spot = cfg.num("r7_exits", "cap_spot_pts")
        self.cap_option = cfg.num("r7_exits", "cap_option_pts")
        self.rest_offset = cfg.num("r6_entries", "rest_offset")
        self.debit_max = cfg.num("r7_exits", "resolution_debit_max")

    # -- helpers ---------------------------------------------------------------
    def _entry_event(self, tr: SimTrade) -> Event:
        rest = (f"rest BUY K+5 @ sale-{self.rest_offset:.2f}" if tr.side == "sell_first"
                else f"rest SELL K-5 @ cost+{self.rest_offset:.2f}")
        return Event(event_type="entry", rule_id="R1.4", branch=tr.branch, side=tr.side,
                     s0=tr.s0, expiry=tr.expiry, leg_strikes=tr.leg_strikes,
                     trade_id=tr.id, entry_min=tr.entry_min, signal_min=tr.signal_min,
                     entry_option_mid=tr.entry_option_mid,
                     resting_limit_ref=tr.resting_limit_ref, target=tr.target,
                     bh_level=tr.bh_level, entry_L=tr.entry_L, cap_source=tr.cap_source,
                     cap_value=tr.cap_value, episode=tr.episode,
                     notes=f"ENTRY {tr.branch} | S0={tr.s0} | {rest}")

    def _exit_event(self, tr: SimTrade) -> Event:
        return Event(event_type="exit", rule_id="R7", branch=tr.branch, side=tr.side,
                     s0=tr.s0, expiry=tr.expiry, leg_strikes=tr.leg_strikes,
                     trade_id=tr.id, entry_min=tr.entry_min, signal_min=tr.signal_min,
                     entry_option_mid=tr.entry_option_mid,
                     resting_limit_ref=tr.resting_limit_ref, target=tr.target,
                     bh_level=tr.bh_level, entry_L=tr.entry_L, cap_source=tr.cap_source,
                     cap_value=tr.cap_value, episode=tr.episode,
                     outcome_type=tr.exit_type, outcome_minutes=tr.minutes,
                     exit_ref=tr.exit_ref, resolution_debit=tr.resolution_debit,
                     adverse=tr.adverse,
                     notes=f"EXIT {tr.exit_type} | pnl {self.pnl(tr):+.2f} pts | adverse {tr.adverse:.2f}")

    @staticmethod
    def pnl(tr: SimTrade) -> float:
        """R11.3 leg P&L proxy in SPX points."""
        if tr.exit_ref is None:
            return 0.0
        return (tr.exit_ref - tr.s0) if tr.side == "sell_first" else (tr.s0 - tr.exit_ref)

    def _close(self, state: EngineState, tr: SimTrade, exit_type: str, exit_ref: float,
               minutes: Optional[int] = None, debit: Optional[float] = None) -> Event:
        tr.state = "closed"
        tr.exit_type = exit_type
        tr.exit_ref = exit_ref
        tr.minutes = minutes
        tr.resolution_debit = debit
        # R11.2: the exit reference price is included for non-fill exits
        if exit_type != "fill":
            move = (tr.s0 - exit_ref) if tr.side == "sell_first" else (exit_ref - tr.s0)
            tr.adverse = max(tr.adverse, move)
        state.open_trade = None
        state.pending_exit = None
        return self._exit_event(tr)

    # -- (1) start of bar --------------------------------------------------------
    def execute_pending(self, bar: Bar, state: EngineState) -> list[Event]:
        """Pending exits price at THIS bar's open; then a PendingEntry opens at
        THIS bar's open (S0 = that open, R1.4). The Branch-B entry_L anchor is
        fixed at signal time and travels on the PendingEntry (bh_level is a
        legacy field, always None since v2.3 — A has no scratch)."""
        out: list[Event] = []
        tr = state.open_trade
        if tr is not None and state.pending_exit is not None:
            label = "timeout" if state.pending_exit == "clock" else state.pending_exit
            out.append(self._close(state, tr, label, bar.open,
                                   minutes=None))
        pe = state.pending_entry
        if pe is not None:
            state.pending_entry = None
            s0 = bar.open
            sell = pe.side == "sell_first"
            target = s0 + self.fill_pts if sell else s0 - self.fill_pts
            cap_source = "chain" if self.chain_available else "proxy"
            cap_value = self.cap_option if cap_source == "chain" else self.cap_spot
            bh = pe.bh_level
            entry_l = pe.entry_L
            tr = SimTrade(
                id=state.next_trade_id, branch=pe.branch, side=pe.side,
                signal_min=pe.signal_min, entry_min=bar.min, s0=s0,
                expiry=pe.expiry, leg_strikes=pe.strike_hint,
                entry_option_mid=None, resting_limit_ref=None, target=target,
                bh_level=bh, entry_L=entry_l, cap_source=cap_source,
                cap_value=cap_value, episode=pe.episode,
            )
            state.next_trade_id += 1
            state.open_trade = tr
            state.entries_today += 1
            if pe.branch == "A":
                state.entered_episode_a = pe.episode
            else:
                state.entered_episode_b = pe.episode
            out.append(self._entry_event(tr))
        return out

    # -- (3) end of bar ------------------------------------------------------------
    def apply(self, events: list[Event], row: FeatureRow,
              state: EngineState) -> list[Event]:
        out: list[Event] = []
        exit_ev = next((e for e in events if e.event_type == "exit_decision"), None)
        pend_ev = next((e for e in events if e.event_type == "pending_entry"), None)
        tr = state.open_trade
        if tr is not None:
            is_fill = exit_ev is not None and exit_ev.outcome_type == "fill"
            is_resolution = exit_ev is not None and exit_ev.outcome_type == "resolution"
            # fills: touch bar excluded (R11.2); resolution: executes at this bar's
            # OPEN, so this bar's range past the open never counts (R7.0)
            if not is_fill and not is_resolution:
                # R11.2 adverse: include this bar (execution bar included; touch bar excluded)
                move = (tr.s0 - row.bar.low) if tr.side == "sell_first" else (row.bar.high - tr.s0)
                tr.adverse = max(tr.adverse, move)
            if exit_ev is not None:
                kind = exit_ev.outcome_type
                if kind == "fill":
                    out.append(self._close(state, tr, "fill", tr.target,
                                           minutes=row.min - tr.entry_min))
                elif kind == "resolution":
                    # R7.0: evaluates at the 15:30 bar, executes at its OPEN
                    debit = self._implied_debit(tr) if self.chain_available else None
                    if debit is not None and debit <= self.debit_max:
                        out.append(self._close(state, tr, "resolution_debit",
                                               row.bar.open, debit=debit))
                    else:
                        out.append(self._close(state, tr, "resolution_close",
                                               row.bar.open, debit=debit))
                else:
                    state.pending_exit = kind      # priced at next bar's open
        if pend_ev is not None and state.open_trade is None and state.pending_entry is None:
            state.pending_entry = PendingEntry(
                branch=pend_ev.branch, side=pend_ev.side, signal_min=pend_ev.signal_min,
                episode=pend_ev.episode, expiry=pend_ev.expiry,
                strike_hint=pend_ev.leg_strikes, chain_quote_ts=pend_ev.strike_quote_ts,
                bh_level=pend_ev.bh_level, entry_L=pend_ev.entry_L)
        return out

    def _implied_debit(self, tr: SimTrade) -> Optional[float]:
        return None   # live chain hook (task 7); backtests always resolution_close (R2.5)

    # -- session end -----------------------------------------------------------------
    def end_of_session(self, last_bar: Bar, state: EngineState) -> list[Event]:
        """R7.0: no bar j+1 -> price at the close of bar j. An open horizon
        truncated by session end is censored, never timeout (R7.5)."""
        out: list[Event] = []
        tr = state.open_trade
        if tr is None:
            return out
        if state.pending_exit is not None:
            label = "timeout" if state.pending_exit == "clock" else state.pending_exit
            out.append(self._close(state, tr, label, last_bar.close))
        else:
            out.append(self._close(state, tr, "censored", last_bar.close))
        return out
