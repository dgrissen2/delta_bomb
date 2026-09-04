"""R12.2 HAND-COMPUTED fixture (task 15A) — written and committed BEFORE any v3
pricing code exists (commit history is the proof). Every expected value below
is derived BY HAND in the comments. These numbers may NEVER be edited to match
observed behavior: a mismatch is a defect investigation, not a fixture update.

Conventions under test (requirements v3.0):
  R1.4b leg 1 books at the ENTRY bar's closing NBBO, conservative side
        (sell-first -> bid; long-first -> ask)
  R1.4c limit L = fill1 -/+ 0.10, tick-rounded AGAINST us on the 0.10 grid
        (down for BUY limits, up for SELL limits)
  R1.4d fill iff the minute's closing NBBO is marketable: BUY limit ask<=L,
        SELL limit bid>=L; FIRST ELIGIBLE MINUTE = signal+2 (= entry+1)
  R7.0  non-fill exits: decision at close of bar j, booked at close-of-bar j+1
        NBBO conservative side; resolution books at THE 15:30 BAR's closing
        NBBO; session end -> bar j's closing NBBO; any exit cancels the limit
        (fill wins a same-minute race)
  R10.4 entry aborted unless BOTH strikes valid at entry bar; 5th consecutive
        quote_gap minute while open -> limit canceled, outcome data_invalid,
        guards keep running
  R11.3 $ = points x 100; sell-first pnl = fill1 - buyback; long-first pnl =
        sale - fill1; completed bomb = +$10 exactly

Scenario schema:
  side: 'sell_first'|'long_first'; signal_min t; quotes: {strike: {minute:
  (bid, ask) | None}} (None = missing quote that minute; minutes absent from
  the dict and >= entry are also missing); spx_extra: optional bar overrides.
  expect: dict of hand-derived outcomes.
"""

K, K2S, K2L = 7500.0, 7505.0, 7495.0   # base strike; sell-first partner K+5; long-first K-5

SCENARIOS = [
    # ------------------------------------------------------------------ S1
    dict(
        name="S1_sell_first_plain_fill",
        side="sell_first", signal_min=700,
        quotes={
            K:   {701: (40.00, 40.30)},
            # DERIVATION: leg1 = SELL K at 701 closing BID = 40.00
            #             L = 40.00 - 0.10 = 39.90 (BUY K+5 limit; on-grid, no rounding)
            K2S: {701: (39.30, 39.60),   # 39.60 <= 39.90 BUT minute 701 = entry bar -> NOT eligible (t+2 rule)
                  702: (39.70, 40.00),   # ask 40.00 > 39.90 -> no fill
                  703: (39.40, 39.80)},  # ask 39.80 <= 39.90 -> FILL at 703, booked at L=39.90
        },
        expect=dict(leg1_fill=40.00, limit_price=39.90, outcome="fill",
                    fill_min=703, minutes=2,          # 703 - 701
                    credit=0.10, pnl_usd=+10.0),
    ),
    # ------------------------------------------------------------------ S2
    dict(
        name="S2_boundary_equality_and_t2_first_eligible",
        side="sell_first", signal_min=700,
        quotes={
            K:   {701: (40.00, 40.30)},                    # leg1 40.00, L 39.90
            K2S: {701: (39.00, 39.50),                     # marketable but BANNED (entry minute)
                  702: (39.50, 39.90)},                    # ask 39.90 <= 39.90 -> equality FILLS
        },
        expect=dict(leg1_fill=40.00, limit_price=39.90, outcome="fill",
                    fill_min=702, minutes=1, credit=0.10, pnl_usd=+10.0),
    ),
    # ------------------------------------------------------------------ S3
    dict(
        name="S3_long_first_fill_with_tick_rounding_against_us",
        side="long_first", signal_min=700,
        quotes={
            # DERIVATION: leg1 = BUY K at 701 closing ASK = 40.25
            #   raw L = 40.25 + 0.10 = 40.35 -> SELL limit rounds UP (against us)
            #   on the 0.10 premium grid -> L = 40.40; fill iff bid(K-5) >= 40.40
            K:   {701: (39.95, 40.25)},
            K2L: {701: (40.30, 40.70),    # entry-minute quote (valid, not marketable)
                  702: (40.35, 40.75),    # bid 40.35 < 40.40 -> no fill (rounding matters!)
                  703: (40.40, 40.80)},   # bid 40.40 >= 40.40 -> FILL at 703 at L=40.40
        },
        expect=dict(leg1_fill=40.25, limit_price=40.40, outcome="fill",
                    fill_min=703, minutes=2, credit=0.15,   # 40.40 - 40.25
                    pnl_usd=+15.0),
        # NOTE: rounding AGAINST us can only ever RAISE the credit (never below 0.10)
    ),
    # ------------------------------------------------------------------ S4
    dict(
        name="S4_same_minute_fill_beats_scratch",
        side="sell_first", signal_min=700, branch="B",
        scratch_trigger_min=703,           # flow drop signalled at 703 close (within 3-min window)
        quotes={
            K:   {701: (40.00, 40.30)},                    # leg1 40.00, L 39.90
            K2S: {701: (40.00, 40.40),    # entry-minute quote (valid, not marketable)
                  702: (40.00, 40.40),
                  703: (39.50, 39.90)},   # marketable at the SAME close as the scratch -> FILL WINS
        },
        expect=dict(outcome="fill", fill_min=703, minutes=2, credit=0.10,
                    pnl_usd=+10.0, no_scratch=True),
    ),
    # ------------------------------------------------------------------ S5
    dict(
        name="S5_scratch_cancels_limit_and_books_next_close_ask",
        side="sell_first", signal_min=700, branch="B",
        scratch_trigger_min=702,
        quotes={
            K:   {701: (40.00, 40.30),
                  703: (40.30, 40.60)},   # buyback books at 703 CLOSING ASK = 40.60
            K2S: {701: (40.20, 40.50),    # entry-minute quote
                  702: (40.20, 40.50)},   # never marketable
        },
        # DERIVATION: decision at 702 close -> limit_canceled at 702; book at
        # close-of-703 ask 40.60; pnl = 40.00 - 40.60 = -0.60 -> -$60
        expect=dict(outcome="scratch", limit_canceled_min=702,
                    exit_book_min=703, exit_price=40.60, pnl_usd=-60.0,
                    scratch_loss_usd=60.0),
    ),
    # ------------------------------------------------------------------ S6
    dict(
        name="S6_clock_timeout_books_next_close_ask",
        side="sell_first", signal_min=700,
        quotes={
            K:   {701: (40.00, 40.30), 762: (41.00, 41.40)},
            K2S: {m: (40.20, 40.50) for m in range(701, 763)},   # never <= 39.90
        },
        # DERIVATION: clock fires at m - entry >= 60 -> m = 761 (decision);
        # cancel at 761; book at 762 closing ask 41.40; pnl = 40.00 - 41.40 = -1.40 -> -$140
        expect=dict(outcome="timeout", limit_canceled_min=761,
                    exit_book_min=762, exit_price=41.40, pnl_usd=-140.0),
    ),
    # ------------------------------------------------------------------ S7
    dict(
        name="S7_resolution_books_AT_the_1530_bar_close",
        side="sell_first", signal_min=868,
        quotes={
            K:   {871: (40.00, 40.30), 930: (40.60, 41.00)},   # input fix: entry minute is 871 (expected values untouched)
            K2S: {m: (40.20, 40.50) for m in range(870, 931)},
        },
        # DERIVATION: entry 869; clock would fire at 929 (869+60) BUT R5.4: a
        # 14:29-signal entry... entry+60 = 929 < 930 -> clock DOES fire at 929?
        # NO: signal 868 (14:28), entry 869 (14:29), clock at 929 (15:29) fires
        # BEFORE resolution -> to isolate resolution, the clock must not fire:
        # so this scenario pins entry at 871 instead: signal_min 870 is the
        # LAST allowed (14:30); entry 871; clock at 931 > 930 -> resolution at
        # 930 wins (R5.4). Book at BAR 930's CLOSING ask = 41.00;
        # pnl = 40.00 - 41.00 = -1.00 -> -$100
        override_signal_min=870, override_entry_min=871,
        expect=dict(outcome="resolution_close", limit_canceled_min=930,
                    exit_book_min=930, exit_price=41.00, pnl_usd=-100.0),
    ),
    # ------------------------------------------------------------------ S8
    dict(
        name="S8_cap_on_option_mid_move",
        side="sell_first", signal_min=700,
        quotes={
            K:   {701: (40.00, 40.30),                     # leg1 40.00
                  710: (43.40, 43.70),                     # mid 43.55; 43.55-40.00=3.55>=3.5 -> cap at 710
                  711: (43.60, 44.00)},                    # book at 711 closing ask 44.00
            K2S: {m: (40.20, 40.50) for m in range(701, 712)},
        },
        # DERIVATION: pnl = 40.00 - 44.00 = -4.00 -> -$400
        expect=dict(outcome="cap", cap_min=710, limit_canceled_min=710,
                    exit_book_min=711, exit_price=44.00, pnl_usd=-400.0,
                    cap_source="chain"),
    ),
    # ------------------------------------------------------------------ S9
    dict(
        name="S9_five_gap_data_invalid_then_timeout",
        side="sell_first", signal_min=700,
        quotes={
            K:   {**{701: (40.00, 40.30), 762: (40.80, 41.20)},
                  **{m: (40.10, 40.40) for m in range(702, 705)}},
            # K2 quotes exist 702-704, MISSING 705-709 (5 consecutive gap minutes)
            K2S: {**{m: (40.20, 40.50) for m in range(701, 705)},
                  **{m: (40.20, 40.50) for m in range(710, 763)}},
        },
        # DERIVATION: gap minutes 705,706,707,708,709 -> 5th at 709: limit
        # canceled (reason quote_gap); trade stays open under guards; clock at
        # 761 -> timeout decision; book at 762 closing ask 41.20;
        # pnl = 40.00 - 41.20 = -1.20 -> -$120; outcome labeled data_invalid
        expect=dict(outcome="timeout", data_invalid=True,
                    limit_canceled_min=709, cancel_reason="quote_gap",
                    exit_book_min=762, exit_price=41.20, pnl_usd=-120.0),
    ),
    # ------------------------------------------------------------------ S10
    dict(
        # SCENARIO INPUT REDESIGN (authoring defect found by the harness): the
        # original placed the entry at 15:41, INSIDE the R7.6 resolution window,
        # so resolution correctly fired — censoring is only reachable on a
        # PARTIAL day whose bars stop early. Same derivation, same numbers.
        name="S10_session_end_censored_books_bar_j_close",
        side="sell_first", signal_min=600,
        session_last_min=610,
        quotes={
            K:   {601: (40.00, 40.30), 610: (40.30, 40.60)},
            K2S: {m: (40.20, 40.50) for m in range(601, 611)},
        },
        # DERIVATION: entry 601; bars stop at 610 with no decision (clock needs
        # 60m) -> censored; NO bar j+1 -> book at bar 610's closing ask 40.60;
        # pnl = 40.00 - 40.60 = -0.60 -> -$60
        expect=dict(outcome="censored", exit_book_min=610, exit_price=40.60,
                    pnl_usd=-60.0),
    ),
    # ------------------------------------------------------------------ S11
    dict(
        name="S11_entry_abort_when_partner_quote_invalid",
        side="sell_first", signal_min=700,
        quotes={
            K:   {701: (40.00, 40.30)},
            K2S: {701: (0.0, 40.50)},     # bid 0 -> INVALID (R10.4) at the entry bar
        },
        expect=dict(outcome="entry_aborted_no_quote", trade_opened=False,
                    still_qualifying=True),
    ),
    # ------------------------------------------------------------------ S12
    dict(
        name="S12_veto_exit_cancel_and_book",
        side="sell_first", signal_min=700, branch="B",
        veto_trigger_min=720,
        quotes={
            K:   {701: (40.00, 40.30), 721: (41.10, 41.50)},
            K2S: {m: (40.20, 40.50) for m in range(701, 722)},
        },
        # DERIVATION: veto at 720 close -> cancel at 720, book at 721 closing
        # ask 41.50; pnl = 40.00 - 41.50 = -1.50 -> -$150
        expect=dict(outcome="veto_exit", limit_canceled_min=720,
                    exit_book_min=721, exit_price=41.50, pnl_usd=-150.0),
    ),
    # ------------------------------------------------------------------ S13
    dict(
        name="S13_long_first_state_flip_books_next_close_bid",
        side="long_first", signal_min=770,
        state_flip_min=780,                # 13:00 read UP while long carried
        quotes={
            K:   {771: (39.95, 40.25),     # leg1 = BUY at ask 40.25
                  781: (39.00, 39.40)},    # book SELL at 781 closing BID 39.00
            K2L: {m: (39.50, 39.90) for m in range(771, 782)},   # bid < L=40.40 always
        },
        # DERIVATION: pnl (long_first) = sale - fill1 = 39.00 - 40.25 = -1.25 -> -$125
        expect=dict(outcome="state_flip", limit_canceled_min=780,
                    exit_book_min=781, exit_price=39.00, pnl_usd=-125.0),
    ),
]
