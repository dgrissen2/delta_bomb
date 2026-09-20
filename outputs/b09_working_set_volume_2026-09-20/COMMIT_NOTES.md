Test fixed cached SPY volume across all five Branch B cohorts; preserve the working set

User request: first consolidate/push the full findings and current working-set
memory, then test volume with existing data against each individual signal and
their combined union. Consolidation was committed and pushed as e5259b4 before
this experiment; central committed research was also pushed as 329085a.

Extend the previously defined five-minute SPY relative-volume feature, without
changing any threshold, signal, IV rule, scoring objective or research calendar.
At entry T, use completed T-5 through T-1 share volume divided by the same-clock
median of exactly 60 strictly preceding source sessions. RVOL > 1 is high;
finite <= 1 is ordinary; missing current/history observations remain unknown.
Require all five actual bars in every reference window. No fill, inferred
minute data, downloads, threshold sweep or inverted low-volume strategy.

The source is existing Nasdaq-venue XNAS.ITCH SPY volume, not consolidated volume
or signed buying pressure. Cache ends June 11, 2026. Of 685 combined entries,
592 have usable volume; 52 lack current data and 41 fail complete historical
coverage. All 39 partial-2026-H2 entries lack volume; no H2 volume result exists.
Record exact unknown timestamps/cohort flags/status in the central ledger.

Keep the current cohorts: B09 F4 OR SPX, B05 F4, B09 five-minute persistence,
original B07 six-sector acceleration, and their exact-minute-deduplicated union.
Same 239 selected 2025-2026 research dates, no spacing, causal above VT. Accuracy
continues to mean a native high touch of entry+5 before a native low touch of
entry-10 within 60 bars including entry. No candle-close stop or trailing peak.
Neither/ambiguous stay in N. Reversal after the target does not undo a winner.

Pooled high versus ordinary volume, each on measured coverage:
- B09 F4 OR SPX: 84/136 = 61.8% versus 92/148 = 62.2%.
- B05 F4: 29/44 = 65.9% versus 30/44 = 68.2%.
- B09 persistence: 126/200 = 63.0% versus 145/236 = 61.4%.
- Original B07: 20/33 = 60.6% versus 29/44 = 65.9%.
- Combined: 173/274 = 63.1% versus 198/318 = 62.3%.

The combined difference is only +0.87 percentage points, with a paired whole-date
95% interval of -8.08 to +9.52. The appropriate unfiltered reference is observed
371/592 = 62.7%, not the full 427/685 sample. High volume improves that observed
rate by only +0.47 pp while discarding 198 observed winners and retaining 46.3%
of observed signals. Unknowns are not counted as volume-based rejections.

B05 illustrates the coverage trap: high volume 65.9% looks higher than its full
62.5%, but its same observed population already scores 67.0% unfiltered. Always
compare common measurement coverage. Preserve unknown outcomes separately.

Combined high-volume accuracy is modestly higher in each measured half, but
high-volume counts are 82, 168 and only 24; 2026 H2 is unavailable. Individual
cohort direction varies, and B05 4/4 or B07 0/1 in 2026 H1 proves nothing stable.
Five overlapping cohorts are not five independent confirmations.

Combined high volume has 75/274 stops first (27.4%) versus 69/318 (21.7%) for
ordinary volume; fewer neither outcomes accompany more stops and slightly more
targets. We keep the requested +5-first objective and add no post-target metric.

Reuse the prior same-date/hour diagnostic. Combined difference is +0.44 pp with
CI -12.72 to +14.47 on 136 entries/38 dates; persistence is -4.32 pp on 96 entries/
27 dates. Tiny B05/B07 support does not justify inference. Stronger pre-entry
returns and movement in high-volume entries remain possible confounding.

Pooled leave-one-date-out high-minus-ordinary ranges cross zero for combined;
persistence retains a small positive difference, but its broader uncertainty and
matched-block result remain weak. These deletion ranges are not confidence
intervals. Bootstrap uses 5,000 paired date draws, seed 20260920, includes original
zero-entry dates, and reports finite draws. No prior-search or regime adjustment.

Freeze and audit: 685 outcome-free features; exact agreement at all 501 earlier
B09 feature timestamps; independent raw five-bar checks for every entry; exact
earlier baseline volume counts. Independently replay all 685 native SPX paths
(41,100 bar observations across 163 dates), above-VT admission and barrier order;
recount all 125 summary rows and 1,195 leave-date rows. Existing causal RVOL
boundary test and Ruff pass. No independent reviewer was run in this side chat.

Store every derived table under central_trade_data, with a namespace dictionary,
hash freeze/analysis/verification receipts and root changelog/dictionary entries.
Document full pooled/half-year results, opportunity cost, coverage and limitations
in FINDINGS, canonical learning notebook section 11.36 and project MEMORY.

Disposition: this fixed activity measure has not earned a hard gate. Preserve
the five-rule working set unchanged, retain the weak finding, and do not promote
the opposite threshold or initiate new data collection based on this result.
This is not a test of all volume hypotheses, consolidated flow or signed pressure.
Preserve all unrelated concurrent dashboard, notebook and central-registry work.
