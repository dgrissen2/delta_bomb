# B01–B10 on the fixed 150-date sample

Finalized after independent Charlie and Brent reviews, before generating the new
family outcomes. Review dispositions are recorded in PERSONA_DECISIONS.md.

## Objective and fixed sample

Reapply the existing entry recipes to the identical150 dates in
`/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/research/combined_days.csv`.
Retain original50 versus additional100 cohorts and all zero-entry dates. No date
redraw, tuning, new data collection, reconstructed minutes, HIRO or option P&L.

Primary eligibility: each observed RTH minute low before entry must be strictly
above the positive same-date VT, and entry open must be above VT. A prior breach
locks the rest of that date out. Never inspect the entry minute's later low or
future session prices for eligibility. Also retain opening-only and entry-above
diagnostic populations, labelled separately; no full-day-hindsight selection.

Generate the original setup state machines first and attach the eligibility
gate to emitted events. Under the monotonic primary gate, later events cannot
requalify after a breach. Preserve source episode/rearm/refire rules.

## Thirteen rows from ten families

| ID | Frozen recipe |
|---|---|
| B01 | Fixed-time control at10:00,11:00,12:00,13:00,14:00 |
| B02 | Existing5m thrust package |
| B03 | Existing5m thrust-or-staircase-enabled package; not stairs-only |
| B04 | T: bullish5m, half-ATR pullback, later1m three-high break |
| B05 | Eight-point pullback, five-bar stall, running typical-price mean reclaim; original15m refires |
| B06 immediate / retest | Existing six-bar5m ceiling; immediate or later1m holding retest |
| B07 | Existing frozen-range undercut/reclaim/then break |
| B08 price / RSI | Existing flat-state BB20,2 rebound; separately first1m RSI14 recovery through30 |
| B09 | Existing1m staircase with its own two-bar5m EMA20 slope context |
| B10 immediate / retest | Existing09:30–09:34 opening high; first eligible close above or later1m retest |

Snapshot the eight rule modules from
`/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/`
without edits. Their existing clocks, ATR/EMA/RSI initialization, warmup,
episode expiry, delayed observation and repeated-level suppression stay fixed.
SPX has no observed volume here: B02/B03 remain the explicitly price-only
transfer; no inferred VWAP/volume or new ADX admission gate.

Five-minute bars come only from complete native one-minute bins. Use all available
chronological native prehistory, including non-evaluation dates, to warm the
inherited continuous indicators. Record exact history sources, gaps/exclusions,
and any differences versus the original dashboard's source inventory. Five-minute
history may include valid complete bins from partial sessions, matching the
existing builder; minute RSI uses complete390-minute RTH sessions only. No forward
fill, synthetic overnight observations or warming only on sampled evaluation days.

## Score and reporting

Each emitted signal uses the actual next available minute's open at its known_min.
Within the next60 native minutes, +5 before−15 is a win. First touches in the same
minute are ambiguous; neither/ambiguous remain in the denominator. No post-target
giveback criterion. Preserve individual events/episode IDs and duplicate same-time
episodes; report distinct date/minute counts so overlaps are visible.

The primary opportunity unit is one variant/date/entry minute: multiple overlapping
B07 ranges triggering together remain in the raw setup ledger, but count once in
the price-hit denominator. B05 refires at different minutes remain separate entries.

Produce all13 rows for original50, added2025, added2026, added100 and combined150: N, active dates,
distinct times/setups, targets, adverse, neither, ambiguous, hit rate, date-bootstrap
uncertainty and opportunities retained. Compare each family with the B01 entry at
the beginning of the SAME hour on the SAME date, subject to the same VT gate.
Reweight those observed control outcomes by that family's entry-date/hour mix;
report matched N and a paired date-bootstrap interval on the difference. These
controls occur earlier than most family entries, so this is a timing diagnostic,
not a randomized causal treatment effect. No selecting a winner solely from pooled
150 results. Treat new-family results as exploratory on reused data.

Predeclared diagnostics: year/cohort and hour of entry; observed opening35m range,
ATR and distance above VT available at entry; first-per-day and nonoverlapping60m
event subsets; paired immediate/retest and B08 price/RSI setup outcomes including
setups with no delayed trigger. Keep these diagnostics separate from primary
rules. Never optimize range, target, time, cooldown or IV cutoffs.

Freeze diagnostic terciles using one outcome-free row per date across150 dates:
completed09:30–10:04 range, ATR14 from the five-minute bar known at10:05, opening
cushion above VT in points and divided by that ATR. Apply the frozen ATR and
VT-cushion cut points to their available-at-entry measurements; do not interpret
the resulting bins as deployable thresholds. Full35-minute range diagnostics
exclude entries before10:05; the event ledger separately records the partial
opening range actually known at those earlier times. Keep hour bins as10,11,12,13,14.
Record calendar-day gaps in warmup sources and the prior100-five-minute-bar history.
These are observed calendar gaps, not claims about exchange trading-day closures.

Report target/(target+adverse) only as a diagnostic alongside neither/ambiguous;
it never replaces the primary denominator. No automatic strategy promotion from
this exploratory comparison. A follow-up candidate should at least have positive
same-date/hour control differences in all three era groups, with uncertainty and
first-per-day/60-minute-spacing sensitivities shown. No IV overlay is attached to
these13 entry rows. The old50/additional100 split is not called train/test for
B02–B10: the ten original dashboard development dates do not overlap the150.
The primary continuous-above gate is an explicit user-requested population change;
the original opening-only population remains visible for fidelity.

## Validation and storage

First reproduce existing10-day dashboard event identities/counts using its frozen
source inventory, then disclose effects of newly available warmup history if any.
Reproduce B06's1,040 parents/outcomes and its strict-VT762-event audit subset on150.
Test prior-only VT eligibility, ambiguous ordering, no change after target,
zero-event dates, source integrity, and prefix invariance for selected dates.

All derived data/logs/manifests go under
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v1/`.
Source snapshots, methods and findings live in this separate project slug.
Freeze protocol/input/module hashes before expanded-family outcomes. Completed
artifacts are verified on rerun; they must not be overwritten. Update central
CHANGELOG and DATA_DICTIONARY and commit the scoped evidence.
