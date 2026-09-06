"""Executor — a pure, I/O-FREE state applier (spec v3.0).

fill_mode="limit" (full tier): leg 1 books at the bar's closing NBBO
conservative side (R1.4b); the second leg is a RestingLimit at fill1 -/+ 0.10
(R1.4c); fills book at L (R7.1); every non-fill exit books at the NEXT bar's
closing NBBO conservative side (R7.0; resolution books AT the 15:30 bar;
session end books at bar j). Quotes arrive on the QuoteView passed in by
Session — the Executor never performs I/O or trading judgment.

fill_mode="spot_touch" (price tier only): the legacy v2 semantics (S0 +/- 3
touch, open-price bookings) are retained verbatim, quarantined by TierPolicy.
"""
from __future__ import annotations

from typing import Optional

from .config import Config
from .instruments import InstrumentSelector
from .models import (Bar, EngineState, Event, FeatureRow, PendingEntry, QuoteView,
                     RestingLimit, SimTrade, TierPolicy, realized_pnl_usd,
                     round_limit_against)


class Executor:
    def __init__(self, cfg: Config, selector: InstrumentSelector,
                 tier: Optional[TierPolicy] = None):
        self.cfg = cfg
        self.sel = selector
        from .models import TIER_FULL
        self.tier = tier or TIER_FULL
        self.fill_pts = cfg.num("r1_instruments", "fill_touch_pts")
        self.cap_spot = cfg.num("r7_exits", "cap_spot_pts")
        self.cap_option = cfg.num("r7_exits", "cap_option_pts")
        self.rest_offset = cfg.num("r6_entries", "rest_offset")
        self.credit = cfg.num("r1v3_limits", "credit")
        self.credit_b = cfg.num("r1v3_limits", "credit_b")      # W2.1 knob: Branch-B credit (v1 = same as credit)
        self.tick = cfg.num("r1v3_limits", "limit_tick")
        self.first_off = cfg.i("r1v3_limits", "first_eligible_offset")
        self.stale_max = cfg.i("r1v3_limits", "exit_stale_quote_max_min")

    # ------------------------------------------------------------------ events
    def _trade_fields(self, tr: SimTrade) -> dict:
        lim = tr.limit
        return dict(branch=tr.branch, side=tr.side, s0=tr.s0, expiry=tr.expiry,
                    leg_strikes=tr.leg_strikes, trade_id=tr.id, entry_min=tr.entry_min,
                    signal_min=tr.signal_min, entry_option_mid=tr.entry_option_mid,
                    resting_limit_ref=tr.resting_limit_ref, target=tr.target,
                    bh_level=tr.bh_level, entry_L=tr.entry_L, cap_source=tr.cap_source,
                    cap_value=tr.cap_value, episode=tr.episode,
                    k1=tr.k1, k2=tr.k2, leg1_fill=tr.leg1_fill,
                    limit_price=(lim.price if lim else None),
                    limit_status=(lim.status if lim else None),
                    limit_cancel_reason=(lim.cancel_reason if lim else None),
                    first_eligible_min=(lim.first_eligible_min if lim else None),
                    leg2_fill=tr.leg2_fill, credit=tr.credit,
                    quote_gap_streak=tr.quote_gap_streak,
                    last_valid_bid=tr.last_valid_bid, last_valid_ask=tr.last_valid_ask,
                    last_valid_quote_min=tr.last_valid_quote_min,
                    data_invalid=tr.data_invalid, leg_liq_loss_usd=tr.leg_liq_loss_usd,
                    spx_adverse_pts=tr.adverse, pnl_usd=tr.pnl_usd)

    def _entry_event(self, tr: SimTrade) -> Event:
        if self.tier.fill_mode == "limit":
            verb = "sold" if tr.side == "sell_first" else "bought"
            rest = ("resting BUY" if tr.side == "sell_first" else "resting SELL")
            note = (f"ENTRY {tr.branch} | {verb} {tr.k1:.0f}P @ {tr.leg1_fill:.2f} | "
                    f"{rest} {tr.k2:.0f}P @ {tr.limit.price:.2f}")
        else:
            note = f"ENTRY {tr.branch} | S0={tr.s0} (spot_touch tier)"
        return Event(event_type="entry", rule_id="R1.4", notes=note, **self._trade_fields(tr))

    def _exit_event(self, tr: SimTrade) -> Event:
        note = f"EXIT {tr.exit_type}"
        if tr.pnl_usd is not None:
            note += f" | pnl ${tr.pnl_usd:+,.0f}"
        if tr.data_invalid:
            note += " | DATA_INVALID (unscored)"
        return Event(event_type="exit", rule_id="R7", outcome_type=tr.exit_type,
                     outcome_minutes=tr.minutes, exit_ref=tr.exit_ref, adverse=tr.adverse,
                     notes=note, **self._trade_fields(tr))

    # ------------------------------------------------------------------ booking
    def _conservative_close_out(self, tr: SimTrade, q: Optional[QuoteView],
                                minute: int) -> tuple[Optional[float], bool]:
        """Price to close the LONE leg now: sell_first buys back at ASK,
        long_first sells at BID. Returns (price, data_invalid_flag)."""
        snap = q.leg1 if q else None
        if snap is not None and snap.valid:
            return (snap.ask if tr.side == "sell_first" else snap.bid), False
        # stale allowance (exit BOOKING only, <= stale_max minutes)
        if (tr.last_valid_quote_min is not None
                and minute - tr.last_valid_quote_min <= self.stale_max):
            px = tr.last_valid_ask if tr.side == "sell_first" else tr.last_valid_bid
            return px, False
        # administrative close at last valid, unscored (R10.4)
        px = tr.last_valid_ask if tr.side == "sell_first" else tr.last_valid_bid
        return px, True

    def _close(self, state: EngineState, tr: SimTrade, exit_type: str,
               exit_ref: Optional[float], minutes: Optional[int] = None,
               data_invalid: bool = False) -> Event:
        tr.state = "closed"
        tr.exit_type = exit_type
        tr.exit_ref = exit_ref
        tr.minutes = minutes
        if data_invalid:
            tr.data_invalid = True
        if tr.limit is not None and tr.limit.status == "resting":
            tr.limit.status = "canceled" if exit_type != "fill" else "filled"
            if exit_type != "fill" and tr.limit.cancel_reason is None:
                tr.limit.cancel_reason = exit_type
        if self.tier.fill_mode == "limit" and tr.leg1_fill is not None:
            if exit_type == "fill":
                tr.pnl_usd = round(abs(tr.credit or 0.0) * 100.0, 6)
            elif exit_ref is not None:
                tr.pnl_usd = realized_pnl_usd(tr.side, tr.leg1_fill, exit_ref)
        elif exit_ref is not None:                       # spot_touch legacy pnl in pts
            pts = (exit_ref - tr.s0) if tr.side == "sell_first" else (tr.s0 - exit_ref)
            tr.pnl_usd = None
        state.open_trade = None
        state.pending_exit = None
        return self._exit_event(tr)

    # ------------------------------------------------------------------ (1) bar start
    def execute_pending(self, bar: Bar, state: EngineState,
                        quotes: Optional[QuoteView] = None) -> list[Event]:
        out: list[Event] = []
        tr = state.open_trade
        # pending non-fill exit books at THIS bar
        if tr is not None and state.pending_exit is not None:
            label = "timeout" if state.pending_exit == "clock" else state.pending_exit
            if self.tier.fill_mode == "limit":
                px, dinv = self._conservative_close_out(tr, quotes, bar.min)
                out.append(self._close(state, tr, label, px, data_invalid=dinv))
            else:
                out.append(self._close(state, tr, label, bar.open))
        pe = state.pending_entry
        if pe is not None:
            state.pending_entry = None
            if self.tier.fill_mode == "limit":
                out.extend(self._book_limit_entry(bar, pe, quotes, state))
            else:
                out.append(self._book_spot_entry(bar, pe, state))
        return out

    def _book_spot_entry(self, bar: Bar, pe: PendingEntry, state: EngineState) -> Event:
        s0 = bar.open
        sell = pe.side == "sell_first"
        tr = SimTrade(id=state.next_trade_id, branch=pe.branch, side=pe.side,
                      signal_min=pe.signal_min, entry_min=bar.min, s0=s0,
                      expiry=pe.expiry, leg_strikes=pe.strike_hint,
                      entry_option_mid=None, resting_limit_ref=None,
                      target=s0 + self.fill_pts if sell else s0 - self.fill_pts,
                      bh_level=pe.bh_level, entry_L=pe.entry_L,
                      cap_source="proxy", cap_value=self.cap_spot, episode=pe.episode)
        self._register_entry(state, tr, pe)
        return self._entry_event(tr)

    def _book_limit_entry(self, bar: Bar, pe: PendingEntry,
                          quotes: Optional[QuoteView], state: EngineState) -> list[Event]:
        q1 = quotes.leg1 if quotes else None
        q2 = quotes.leg2 if quotes else None
        if (pe.k1 is None or pe.k2 is None or q1 is None or q2 is None
                or not q1.valid or not q2.valid):
            return [Event(event_type="entry_aborted_no_quote", rule_id="R10.4",
                          branch=pe.branch, side=pe.side, signal_min=pe.signal_min,
                          episode=pe.episode, k1=pe.k1, k2=pe.k2,
                          notes="entry ABORTED — working-strike quotes missing/invalid (R10.4)")]
        sell = pe.side == "sell_first"
        leg1_fill = q1.bid if sell else q1.ask                     # conservative (R1.4b)
        credit = self.credit_b if pe.branch == "B" else self.credit
        raw_l = leg1_fill - credit if sell else leg1_fill + credit
        lim_side = "buy" if sell else "sell"
        L = round_limit_against(raw_l, lim_side, self.tick)
        lim = RestingLimit(side=lim_side, strike=pe.k2, price=L, placed_min=bar.min,
                           first_eligible_min=pe.signal_min + self.first_off)
        tr = SimTrade(id=state.next_trade_id, branch=pe.branch, side=pe.side,
                      signal_min=pe.signal_min, entry_min=bar.min, s0=bar.open,
                      expiry=pe.expiry, leg_strikes=f"{pe.k1:.0f}/{pe.k2:.0f}",
                      entry_option_mid=q1.mid, resting_limit_ref=L, target=None,
                      bh_level=pe.bh_level, entry_L=pe.entry_L,
                      cap_source="chain", cap_value=self.cap_option, episode=pe.episode,
                      k1=pe.k1, k2=pe.k2, leg1_fill=leg1_fill, limit=lim,
                      last_valid_bid=q1.bid, last_valid_ask=q1.ask,
                      last_valid_quote_min=bar.min)
        self._register_entry(state, tr, pe)
        ev = self._entry_event(tr)
        ev.quote_age = 0                                     # R10.4: decisions use minute-of quotes only
        return [ev]

    def _register_entry(self, state: EngineState, tr: SimTrade, pe: PendingEntry) -> None:
        state.next_trade_id += 1
        state.open_trade = tr
        state.entries_today += 1
        if pe.branch == "A":
            state.entered_episode_a = pe.episode
        else:
            state.entered_episode_b = pe.episode

    # ------------------------------------------------------------------ (3) bar end
    def apply(self, events: list[Event], row: FeatureRow,
              state: EngineState) -> list[Event]:
        out: list[Event] = []
        exit_ev = next((e for e in events if e.event_type == "exit_decision"), None)
        cancel_ev = next((e for e in events if e.event_type == "limit_canceled"), None)
        pend_ev = next((e for e in events if e.event_type == "pending_entry"), None)
        tr = state.open_trade
        if tr is not None:
            self._update_marks(tr, row)
            if cancel_ev is not None and tr.limit is not None and tr.limit.status == "resting":
                tr.limit.status = "canceled"
                tr.limit.cancel_reason = cancel_ev.limit_cancel_reason or "quote_gap"
                if cancel_ev.limit_cancel_reason == "quote_gap":
                    tr.data_invalid = True                 # R10.4 horizon property —
                    # ONLY the quote-gap cancel unscores a trade; ordinary exit
                    # cancels (scratch/veto/clock/...) are fully scored
                    # (rehearsal defect 2026-08-23, R9a defect policy)
            if exit_ev is not None:
                kind = exit_ev.outcome_type
                if kind == "fill":
                    out.append(self._apply_fill(tr, row, state))
                elif kind == "resolution":
                    if self.tier.fill_mode == "limit":
                        px, dinv = self._conservative_close_out(tr, row.quote_view, row.min)
                        out.append(self._close(state, tr, "resolution_close", px,
                                               data_invalid=dinv))
                    else:
                        out.append(self._close(state, tr, "resolution_close", row.bar.open))
                else:
                    if tr.limit is not None and tr.limit.status == "resting":
                        tr.limit.status = "canceled"
                        tr.limit.cancel_reason = kind
                    state.pending_exit = kind              # books next bar
        if pend_ev is not None and state.open_trade is None and state.pending_entry is None:
            state.pending_entry = PendingEntry(
                branch=pend_ev.branch, side=pend_ev.side, signal_min=pend_ev.signal_min,
                episode=pend_ev.episode, expiry=pend_ev.expiry,
                strike_hint=pend_ev.leg_strikes, chain_quote_ts=pend_ev.strike_quote_ts,
                bh_level=pend_ev.bh_level, entry_L=pend_ev.entry_L,
                k1=pend_ev.k1, k2=pend_ev.k2)
        return out

    def _apply_fill(self, tr: SimTrade, row: FeatureRow, state: EngineState) -> Event:
        if self.tier.fill_mode == "limit":
            L = tr.limit.price
            tr.leg2_fill = L
            tr.credit = round(abs(tr.leg1_fill - L), 10)
            credit = self.credit_b if tr.branch == "B" else self.credit
            if tr.credit < credit - 1e-9:                    # R1.4e invariant, hard
                raise AssertionError(
                    f"credit invariant violated: {tr.credit} < {credit}")
            tr.limit.status = "filled"
            return self._close(state, tr, "fill", L, minutes=row.min - tr.entry_min)
        # spot_touch legacy: fill at the SPX target touch
        return self._close(state, tr, "fill", tr.target, minutes=row.min - tr.entry_min)

    def _update_marks(self, tr: SimTrade, row: FeatureRow) -> None:
        # contextual SPX excursion (drives nothing)
        move = (tr.s0 - row.bar.low) if tr.side == "sell_first" else (row.bar.high - tr.s0)
        tr.adverse = max(tr.adverse, move)
        # option marks (limit mode)
        q = row.quote_view.leg1 if (row.quote_view is not None) else None
        if q is not None and q.valid:
            tr.last_valid_bid, tr.last_valid_ask = q.bid, q.ask
            tr.last_valid_quote_min = row.min
            if tr.leg1_fill is not None:
                liq = realized_pnl_usd(tr.side, tr.leg1_fill,
                                       q.ask if tr.side == "sell_first" else q.bid)
                tr.leg_liq_loss_usd = max(tr.leg_liq_loss_usd, -min(liq, 0.0))
        tr.quote_gap_streak = row.quote_gap_streak

    # ------------------------------------------------------------------ session end
    def end_of_session(self, last_bar: Bar, state: EngineState,
                       quotes: Optional[QuoteView] = None) -> list[Event]:
        out: list[Event] = []
        tr = state.open_trade
        if tr is None:
            return out
        if self.tier.fill_mode == "limit":
            px, dinv = self._conservative_close_out(tr, quotes, last_bar.min)
        else:
            px, dinv = last_bar.close, False
        if state.pending_exit is not None:
            label = "timeout" if state.pending_exit == "clock" else state.pending_exit
            out.append(self._close(state, tr, label, px, data_invalid=dinv))
        else:
            out.append(self._close(state, tr, "censored", px, data_invalid=dinv))
        return out

    @staticmethod
    def pnl(tr: SimTrade) -> float:
        """Legacy pts helper (price tier / v2 tests)."""
        if tr.exit_ref is None or tr.s0 is None:
            return 0.0
        return (tr.exit_ref - tr.s0) if tr.side == "sell_first" else (tr.s0 - tr.exit_ref)
