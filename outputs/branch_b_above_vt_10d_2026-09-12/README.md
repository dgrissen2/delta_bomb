# Branch B — ten recent sessions opening above VT

Separate prototype slug: **branch_b_above_vt_10d_2026-09-12**. Existing research outputs and the source carousel were not changed. This pass implements B02 and B03 only; the fixed-time baseline is skipped.

Open the [integrated Branch B dashboard](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/branch_b_carousel.html). Select **Thrust only** or **Thrust + staircase** in the same page. The carousel, date selector and counters automatically exclude dates without matching entry types: thrust-only shows **2 dates / 3 entries**; staircase-enabled shows **3 dates / 6 entries**. Entry-type checkboxes filter both markers and dates. The old two URLs redirect into the integrated dashboard.

Keep the HTML file beside `plotly.min.js`; no network is required. The dashboard uses the exact saved reference's layout, candle colors, average colors, ADX panel, fonts and carousel controls. It labels the current experiment's undisplaced EMA5/9/20 correctly. The layout resizes to the window, and VT replaces the unavailable VWAP overlay.

Click the **ⓘ information buttons** beside the mode or entry types for a general explanation of the setup, its rules and when it fires. These explain the entry family rather than an individual signal. Close with ×, Escape or a click outside the explanation.

## Fixed selection and observed counts

Take the **latest ten complete cached SPX sessions as of September 11, 2026** whose first 09:30 **open** is strictly above the same-date recorded Vol Trigger. Select before computing signals. No SG-index-sign, closing-price, all-day-above-VT or intraday-VT entry requirement. Each date has 390 unique valid regular-session minutes, aggregated into 78 complete five-minute bars. The separate 16:00 observation is excluded. August 21 is incomplete and ineligible.

| Date | SPX open | VT | Thrust-only entries | Staircase-enabled entries |
|---|---:|---:|---:|---:|
| 2026-08-12 | 7765.46 | 7720 | 0 | 0 |
| 2026-08-13 | 7763.18 | 7720 | 0 | 0 |
| 2026-08-14 | 7806.60 | 7745 | 0 | 0 |
| 2026-08-17 | 7790.68 | 7765 | 0 | 0 |
| 2026-08-25 | 7676.66 | 7660 | 0 | 0 |
| 2026-08-27 | 7710.34 | 7675 | 0 | 1 |
| 2026-08-28 | 7735.17 | 7700 | 1 | 2 |
| 2026-09-03 | 7686.71 | 7675 | 2 | 3 |
| 2026-09-04 | 7750.19 | 7720 | 0 | 0 |
| 2026-09-08 | 7717.81 | 7715 | 0 | 0 |
| **Total** | | | **3 across 2 dates** | **6 across 3 dates** |

The enabled package's six entries comprise **two thrust admissions and four staircase admissions**. Its set is not simply the three thrust entries plus four staircase entries: one later September 3 thrust is suppressed because a staircase already started the uninterrupted qualifying run. The two columns are competing variants, not nine independent opportunities. Zero-entry dates remain in the research sample and table above, but are filtered out of the dashboard. Counts are descriptive; this pass calculates no accuracy, returns, exits or option completion.

## Rules held constant

The entry source is `eda/bvt_5m_expand_probe.py:entries()` in the `below_vol_trigger` worktree. The older carousel's `long_entries()` uses a different ADX-based entry rule; only the saved HTML's appearance is reused.

Both variants require:

- EMA5 > EMA9 > EMA20 and both adjacent gaps strictly widening.
- **Total** EMA5−EMA20 fan ≥ 0.10 × ATR14.
- A green signal candle and `(close − EMA5) / ATR ≤ 1.50`.
- A valid positive ATR and at least two preceding bars within the session.

**Thrust:** the signal close exceeds the highest body-top of the preceding three bars by at least **10 bp**, with current close as denominator. Prior highs/wicks are not this reference.

**Staircase enabled:** thrust passes **or** the close clears that body-top by at least zero, three closes strictly rise, each of the two prior candles is green with body strictly larger than combined wicks, and EMA5's total two-bar change is at least **0.60 × current ATR**. Three closes means two increases. The current bar need only be green. Thrust gets the displayed attribution when both shapes pass.

Each version independently emits the first qualifying bar in a run and rearms after any failed condition. There is no exit-dependent rearm. These are candidate times to sell B's first put, not evidence that an option sale would fill.

## Necessary adaptations and clock

This is an **SPX OHLC-only transfer** from the older SPY study. Both located SPY volume caches end June 11 and have no overlap with these ten dates. The original VWAP condition and its large-green reclaim exception are omitted equally from both variants; no price average is substituted for VWAP. No HIRO, volume gate, ADX gate, geometry, strength bypass, clean-leg or discretionary override is used.

The checklist's **10:00–14:30 ET inclusive** decision window is retained. The source extractor originally allowed a wider session window; this clock change is explicit. All regular-session candles are displayed, but entries are limited to that window.

For this prototype, cached minute labels are treated as interval starts: the 09:55–10:00 candle becomes available at 10:00. Its entry reference is the stored 10:00 one-minute open, plotted precisely at that time and price. The cache discarded the original timestamp metadata, so start-versus-end labeling is not independently certified. These references are not asserted executable prices, and no option-fill calculation uses them. Marker hover and the table distinguish the signal interval, availability and reference.

Features are computed continuously over **all available valid, complete five-minute regular-session intervals through September 8**, including prior and intervening below-VT days. EMA and first-observation-seeded Wilder RMA match the source; ATR includes overnight gaps. Partial five-minute intervals are dropped, never filled. Evaluation still uses only the ten selected dates.

## Controls and supporting files

Previous/next buttons, left/right keys and the date dropdown navigate only matching dates. Switching modes keeps the current date when it still matches, otherwise selects the first matching date. Each newly selected mode starts with its applicable entry types visible. Within staircase-enabled mode, thrust entries alone show **2 dates / 2 entries** and staircase entries alone show **3 dates / 4 entries**. Unchecking all entry types shows an empty state with navigation disabled.

Other display toggles show times, averages, VT and all qualifying signal bars. The latter includes repeat qualifications of the selected types, shown as small circles at signal closes; they are not extra entry events and do not add dates to the carousel. Hiding VT tightens the price scale. ADX is diagnostic only.

The [selection ledger](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/selection_ledger.csv), [entries](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/entries.csv), [bar diagnostics](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/bar_diagnostics.csv) and [manifest](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/manifest.json) retain the inputs, fixed settings and hashes. All ten VT values match corresponding notes headed **07:00 AM ET**; [VT provenance](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/vt_provenance.json) contains paths, hashes and line extracts. This supports pre-open publication, not contemporaneous local ingestion: some September levels were appended to the local CSV afterward.

Rebuild with `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python /Users/dgrissen/Dev/delta_bomb/outputs/branch_b_above_vt_10d_2026-09-12/build.py`. From this output directory, run `python -m unittest test_build.py test_signals.py` with that same interpreter. The 13 checks cover data completeness, date selection, threshold boundaries, run rearming, staircase bridging, timing and absence of future influence. Browser verification is recorded separately in `browser_checks.json`.
