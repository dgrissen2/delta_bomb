# Charlie and Brent: why the result weakened, and B01–B10 replay

Completed 19 September 2026. The objective is **SPX +5 before −15 within 60 native
one-minute bars after entry**. A target hit remains a win even if price later reverses.
No option P&L or sustained-rally requirement is added.

## CIO interpretation

There are two different disappointments. First, the added sample was harder for
plain B06: more entries ran out of time without reaching +5. Second, the IV rule
stopped selecting a better subset of those B06 entries. A quieter sample explains
much of the first observation; it does not by itself explain the second.

Charlie and Brent independently ranked **optimism from repeatedly exploring the
original small sample** as the most plausible explanation for the lost IV advantage.
They also identified slower available price movement and noisy, partly price-driven
IV acceleration as possible contributors. Those are hypotheses about causes, not
measured percentages of blame. Neither actual dealer gamma nor CTA/dealer flows
were observed. Above VT cannot establish those mechanisms.

The replay leaves four useful candidates to investigate, with distinct evidence:

- **B10 opening-range retest:** highest observed accuracy, 17/20 across all150 dates
  and11/13 on the added100. It held up in both added years, but twenty entries are
  very little evidence. On the same20 setups, immediate entry already won16 times;
  retest won17. Much of the attractive result may be which setups retest, rather
  than a large gain from delaying entry. It omitted45 successful immediate entries.
- **B02 five-minute thrust:** 26/33 overall and13/18 added. High observed accuracy
  with few opportunities. This is the unchanged SPX price-only transfer recipe;
  no volume or VWAP is inferred.
- **B08 lower-band price re-entry:** 62/97 overall and44/70 added. The most promising
  middle ground between accuracy and sample size. The added2025/2026 rates were
  61.2%/66.7%, and spacing entries60minutes leaves62.3% on the added sample.
- **B07 failed-breakdown reclaim:** 159/261 overall and111/186 added. Lower accuracy
  than B08 but substantially more opportunities; added2025/2026 rates56.0%/67.2%.
  These are observed comparisons across different entry times and dates, not proof
  either rule improves a specific B06 entry.

B06 retest, B04 T, B05 stall/reclaim and B09 one-minute staircase did not show a
convincing general accuracy improvement in the added data. B03 adds opportunities
to B02 while lowering the observed percentage. B08's RSI addition leaves only9
entries overall and does not justify its lost opportunities. No row is promoted
to an established strategy from this reused, exploratory sample.

## What was held fixed

- The same150 dates: original50, added66 from2025 and34 from2026. No redrawing dates.
- The eight copied entry modules, their parameters, clocks and episode rules.
  B01 is the declared fixed-time control at10:00,11:00,12:00,13:00,14:00 ET.
- Native observed one-minute SPX prices; complete five-minute aggregation; inherited
  continuous EMA/ATR/RSI warmup. No data download, interpolation or HIRO dependency.
- +5/−15/60-minute first-touch scoring. Neither and ambiguous remain in N.
- Primary eligibility: every minute low from09:30 through the minute before entry
  is strictly above same-date VT, and entry open is above VT. A prior touch/breach
  blocks the rest of that date. The later low of the entry minute is not inspected.
- The old opening-only cohort and an entry-above-only cohort remain diagnostic
  tables. The strict continuous gate is an explicit change from the old dashboard.

All150 dates opened above corroborated same-date VT. Fifty-four eventually touched
or crossed it, but **future crossings do not remove earlier eligible entries**.
Twenty-seven dates have no eligible entry in these13 rows; they remain in the
date-resampling universe. There are5,403 distinct strict-VT family/date/minute
opportunities. Overlapping families are not independent trades.

The ten original dashboard development dates do not overlap these150. However,
the original50 were repeatedly used for B06/IV research, and the150 are now reused
for this comparison. These tables are not a clean held-out validation of a winner
selected after reading them. The2025 coverage is uneven:8 February dates and58
August–December dates, not a balanced calendar-year sample.

## All13 frozen comparison rows

Each cell is targets/opportunities and hit rate. One opportunity means one
variant/date/entry minute. Zero-event dates are retained in uncertainty calculations.
No IV filter is attached to these entry families.

| Entry family | Original50 | Added2025 | Added2026 | Added100 | All150 |
| --- | --- | --- | --- | --- | --- |
| B01 · Fixed-time control | 110/166 · 66.3% | 123/235 · 52.3% | 81/134 · 60.4% | 204/369 · 55.3% | 314/535 · 58.7% |
| B02 · Five-minute thrust | 13/15 · 86.7% | 8/12 · 66.7% | 5/6 · 83.3% | 13/18 · 72.2% | 26/33 · 78.8% |
| B03 · Thrust + staircase | 30/46 · 65.2% | 26/48 · 54.2% | 11/16 · 68.8% | 37/64 · 57.8% | 67/110 · 60.9% |
| B04 · T pullback/break | 100/152 · 65.8% | 102/200 · 51.0% | 63/110 · 57.3% | 165/310 · 53.2% | 265/462 · 57.4% |
| B05 · Stall/reclaim | 162/269 · 60.2% | 227/424 · 53.5% | 158/274 · 57.7% | 385/698 · 55.2% | 547/967 · 56.6% |
| B06 · Immediate breakout | 167/265 · 63.0% | 158/321 · 49.2% | 105/176 · 59.7% | 263/497 · 52.9% | 430/762 · 56.4% |
| B06 · Breakout/retest | 39/63 · 61.9% | 28/69 · 40.6% | 35/52 · 67.3% | 63/121 · 52.1% | 102/184 · 55.4% |
| B07 · Failed breakdown/reclaim | 48/75 · 64.0% | 70/125 · 56.0% | 41/61 · 67.2% | 111/186 · 59.7% | 159/261 · 60.9% |
| B08 · Band rebound, price | 18/27 · 66.7% | 30/49 · 61.2% | 14/21 · 66.7% | 44/70 · 62.9% | 62/97 · 63.9% |
| B08 · Band rebound + RSI | 1/3 · 33.3% | 3/4 · 75.0% | 1/2 · 50.0% | 4/6 · 66.7% | 5/9 · 55.6% |
| B09 · One-minute staircase | 390/599 · 65.1% | 425/855 · 49.7% | 250/417 · 60.0% | 675/1272 · 53.1% | 1065/1871 · 56.9% |
| B10 · Opening-range immediate | 23/29 · 79.3% | 21/40 · 52.5% | 17/23 · 73.9% | 38/63 · 60.3% | 61/92 · 66.3% |
| B10 · Opening-range retest | 6/7 · 85.7% | 5/6 · 83.3% | 6/7 · 85.7% | 11/13 · 84.6% | 17/20 · 85.0% |

## Uncertainty and opportunity count

These are95% percentile intervals from10,000 resamples of complete dates, seed20260919.
They account for within-date dependence; they do not remove exploratory selection,
cross-date market dependence or calendar coverage bias. Very sparse/all-success
groups can produce misleadingly narrow or degenerate bootstrap intervals.

| Entry family | All150 targets/N | Active dates | 95% date interval | Added100 targets/N | Added95% interval |
| --- | --- | --- | --- | --- | --- |
| B01 · Fixed-time control | 314/535 · 58.7% | 123 | 54.4–62.9% | 204/369 · 55.3% | 50.1–60.2% |
| B02 · Five-minute thrust | 26/33 · 78.8% | 29 | 64.5–91.7% | 13/18 · 72.2% | 53.3–91.7% |
| B03 · Thrust + staircase | 67/110 · 60.9% | 67 | 51.8–69.3% | 37/64 · 57.8% | 45.5–68.9% |
| B04 · T pullback/break | 265/462 · 57.4% | 107 | 51.7–63.0% | 165/310 · 53.2% | 46.3–59.8% |
| B05 · Stall/reclaim | 547/967 · 56.6% | 112 | 52.6–60.7% | 385/698 · 55.2% | 50.1–60.3% |
| B06 · Immediate breakout | 430/762 · 56.4% | 105 | 50.8–61.7% | 263/497 · 52.9% | 46.2–59.2% |
| B06 · Breakout/retest | 102/184 · 55.4% | 83 | 45.6–64.5% | 63/121 · 52.1% | 40.0–62.7% |
| B07 · Failed breakdown/reclaim | 159/261 · 60.9% | 99 | 53.8–68.3% | 111/186 · 59.7% | 50.8–68.6% |
| B08 · Band rebound, price | 62/97 · 63.9% | 68 | 54.4–73.1% | 44/70 · 62.9% | 50.8–74.1% |
| B08 · Band rebound + RSI | 5/9 · 55.6% | 9 | 20.0–88.9% | 4/6 · 66.7% | 20.0–100.0% |
| B09 · One-minute staircase | 1065/1871 · 56.9% | 108 | 52.1–61.4% | 675/1272 · 53.1% | 47.2–58.6% |
| B10 · Opening-range immediate | 61/92 · 66.3% | 92 | 56.5–75.7% | 38/63 · 60.3% | 48.3–72.3% |
| B10 · Opening-range retest | 17/20 · 85.0% | 20 | 68.0–100.0% | 11/13 · 84.6% | 61.5–100.0% |

## Why adding dates lowered plain B06

The strict-VT numbers make the change tangible:

| Cohort | B06 +5 first | −15 first | Neither | B01 +5 first |
| --- | --- | --- | --- | --- |
| original_50 | 167/265 · 63.0% | 13.2% | 23.8% | 110/166 · 66.3% |
| added_2025 | 158/321 · 49.2% | 8.1% | 42.7% | 123/235 · 52.3% |
| added_2026 | 105/176 · 59.7% | 9.7% | 30.7% | 81/134 · 60.4% |
| additional_100 | 263/497 · 52.9% | 8.7% | 38.4% | 204/369 · 55.3% |
| combined_150 | 430/762 · 56.4% | 10.2% | 33.3% | 314/535 · 58.7% |

Plain B06's original-to-added decline is10.1 percentage points. Neither rises
from23.8% to38.4%, while −15-first actually falls from13.2% to8.7%. We did not
mostly add more violent downward failures; we mostly added entries that could
not finish the required move in time. B01 also weakens, from66.3% to55.3%, which
supports a broader sample/environment effect rather than a B06-only coding failure.
This arithmetic identifies where the rate changed, not a unique economic cause.

The new2025 B06 rate is49.2%; the new2026 rate is59.7%. The fixed diagnostic bins
give additional support to a movement explanation. Among added B06 entries,
the lowest/middle/highest opening35-minute-range groups hit42.5%/58.2%/68.1%
(N226/177/94), while neither rates were48.2%/35.0%/21.3%. The cuts were19.9933
and27.72 SPX points, computed without outcomes before scoring. These are descriptive
bins, **not a newly tested entry filter or permission to optimize a cutoff**.

## Why that does not rescue the original IV conclusion

The preceding audit, preserved separately, reproduced all1,040 B06 parents and
available IV features. On the continuously-above-VT population, original IV
falling-and-accelerating qualifiers hit39/58 (67.2%) on the old sample versus
76/151 (50.3%) on the added sample. Plain B06 was63.0% and52.9%, respectively.
The filter changed from an apparent +4.2pp advantage to a −2.6pp point difference.
Those unconditional differences are descriptive, not evidence of causation.

On the old opening-only population, the more familiar figures were72.0% against
63.9%; on the added opening-only population,50.0% against55.7%. The gate correction
changes denominators but does not reverse the diagnosis. The added2026 IV group
also weakened, so simply blaming2025 is insufficient. Uncertainty remains large;
the evidence does not establish that IV is harmful either.

The prior audit's day-mix decomposition attributed about−4.1pp of the added
opening-only IV difference to the dates it selected and−1.6pp to entries within
those dates. That is an accounting decomposition, not identification of why IV
selected those dates. Original-rule unknown states were17.4%/12.7%/19.6% across
old50/added2025/added2026; coverage differs, but missingness alone is not proven
responsible. The complete coverage-by-cohort diagnostic is retained.

The earlier IV advantage was small-sample exploratory evidence. Adding data did
not make that advantage established and then break it; it exposed how uncertain
and sample-dependent it had been. The original50's repeated reuse makes optimism
a plausible leading explanation. No new IV thresholds were searched here.

## Dependence checks: first entry and60-minute spacing

Added100 only, unchanged score and strict VT. These are predeclared sensitivities,
not replacements for the primary rows.

| Entry family | Every entry | First per day | At least60m apart |
| --- | --- | --- | --- |
| B01 · Fixed-time control | 204/369 · 55.3% | 56/85 · 65.9% | 204/369 · 55.3% |
| B02 · Five-minute thrust | 13/18 · 72.2% | 13/16 · 81.2% | 13/17 · 76.5% |
| B03 · Thrust + staircase | 37/64 · 57.8% | 24/42 · 57.1% | 30/55 · 54.5% |
| B04 · T pullback/break | 165/310 · 53.2% | 45/75 · 60.0% | 92/171 · 53.8% |
| B05 · Stall/reclaim | 385/698 · 55.2% | 41/76 · 53.9% | 126/240 · 52.5% |
| B06 · Immediate breakout | 263/497 · 52.9% | 46/73 · 63.0% | 99/186 · 53.2% |
| B06 · Breakout/retest | 63/121 · 52.1% | 31/58 · 53.4% | 40/82 · 48.8% |
| B07 · Failed breakdown/reclaim | 111/186 · 59.7% | 40/69 · 58.0% | 63/110 · 57.3% |
| B08 · Band rebound, price | 44/70 · 62.9% | 30/47 · 63.8% | 38/61 · 62.3% |
| B08 · Band rebound + RSI | 4/6 · 66.7% | 4/6 · 66.7% | 4/6 · 66.7% |
| B09 · One-minute staircase | 675/1272 · 53.1% | 47/76 · 61.8% | 125/227 · 55.1% |
| B10 · Opening-range immediate | 38/63 · 60.3% | 38/63 · 60.3% | 38/63 · 60.3% |
| B10 · Opening-range retest | 11/13 · 84.6% | 11/13 · 84.6% | 11/13 · 84.6% |

B06 first-per-day reaches63.0% (46/73), but simple60-minute blocking is53.2%
(99/186), essentially its52.9% unthinned result. First-per-day also concentrates
the time of day: B01's first eligible daily entry reaches65.9% (56/85). Thus the
first-signal observation remains worth distinguishing from a generic morning
effect. A one-hour cooldown does not itself reproduce the first-entry improvement.
B09's large1,272-entry added sample contains many overlapping price paths; its
53.1% raw rate is not1,272 independent pieces of evidence.

## Paired immediate versus delayed setup accounting

All150 strict-VT, at the setup level. B06 has187 delayed setup records but184
distinct retest entry minutes: three pairs trigger at shared minutes. Primary
hit rates deduplicate those price opportunities. B07 likewise has98 extra
overlapping setup records among strict-VT entries. Neither is silently counted
as independent evidence in the primary table.

| Pair | Parent setups | With delayed entry | Parent hit on paired setups | Delayed hit on paired setups | Successful parents without delayed entry |
| --- | --- | --- | --- | --- | --- |
| b06_breakout → b06_retest | 762 | 187 | 55.1% | 55.1% | 327 |
| b08_price → b08_rsi | 97 | 9 | 55.6% | 55.6% | 57 |
| b10_breakout → b10_retest | 92 | 20 | 80.0% | 85.0% | 45 |

B06 retest does not show an improvement even after pairing to the same setups:
both parent and child hit55.1% at the setup level, while327 successful parent
setups have no eligible delayed entry. B08 RSI omits57 successful price-only
parents and has only9 retained entries. B10 retest is the interesting exception,
but the paired gain is one additional target out of20, not the large gap suggested
by comparing85.0% retest with66.3% across all immediate entries. Each delayed entry
starts its own60-minute clock. These are not equal-start-time causal comparisons.

## Important limitation of the requested B01 comparison

Both personas proposed a same-date/hour B01 contrast. It is preserved below and
in comparison.csv, **but it cannot establish signal value**. B01 enters at the
start of the hour; the family usually triggers later. Choosing a10:00 control
because a10:35 breakout subsequently appeared conditions that control on future
price movement. Some of the rise needed to create the breakout can already have
paid the earlier control's +5 target. Conversely, a later failed-breakdown or
band-rebound trigger selects earlier controls exposed to the preceding decline.

This explains why the same-hour control can look extraordinarily good against
breakouts and extraordinarily bad against rebounds. All strict entries have a
matched control, and the reported differences are arithmetically correct, but
their confidence intervals do not repair this selection problem. They describe
timing on selected paths. They do not prove B06 destroys value or B07/B08 create
the large measured advantage. The predeclared positive-control-sign screen is
therefore **insufficient for promotion**; no family is promoted here. A future
incremental test must define comparable decision opportunities at a common
observable clock before knowing which later setup appears. This limitation is
recorded after scoring; the original protocol and control results remain intact.

Added100 diagnostic contrasts:

| Family | Matched N | Family hit | Earlier control hit | Difference | 95% date interval |
| --- | --- | --- | --- | --- | --- |
| B01 · Fixed-time control | 369 | 55.3% | 55.3% | +0.0pp | +0.0 to +0.0pp |
| B02 · Five-minute thrust | 18 | 72.2% | 100.0% | -27.8pp | -46.7 to -8.3pp |
| B03 · Thrust + staircase | 64 | 57.8% | 90.6% | -32.8pp | -45.3 to -21.1pp |
| B04 · T pullback/break | 310 | 53.2% | 68.1% | -14.8pp | -21.4 to -8.5pp |
| B05 · Stall/reclaim | 698 | 55.2% | 54.4% | +0.7pp | -5.0 to +6.7pp |
| B06 · Immediate breakout | 497 | 52.9% | 82.1% | -29.2pp | -34.8 to -23.9pp |
| B06 · Breakout/retest | 121 | 52.1% | 74.4% | -22.3pp | -34.9 to -11.5pp |
| B07 · Failed breakdown/reclaim | 186 | 59.7% | 34.9% | +24.7pp | +16.2 to +33.5pp |
| B08 · Band rebound, price | 70 | 62.9% | 25.7% | +37.1pp | +24.2 to +50.0pp |
| B08 · Band rebound + RSI | 6 | 66.7% | 33.3% | +33.3pp | +0.0 to +76.6pp |
| B09 · One-minute staircase | 1272 | 53.1% | 70.0% | -16.9pp | -22.5 to -11.6pp |
| B10 · Opening-range immediate | 63 | 60.3% | 76.2% | -15.9pp | -25.4 to -7.4pp |
| B10 · Opening-range retest | 13 | 84.6% | 92.3% | -7.7pp | -26.7 to +0.0pp |

## Reproduction, warmup correction and audit trail

Before expanded-family scoring, all441 original dashboard event identities were
reproduced. All1,040 existing B06 parents/outcomes and the762 strict-VT subset
reconcile. Four date-prefix checks leave earlier signals unchanged when later
data is withheld. The twelve new causal/scoring/accounting tests plus inherited
rule tests passed:122 tests total.

The first preparation omitted35 already-cached non-evaluation SPX sessions in
the earlier50-date source folder. A warmup-gap audit found the omission before
any new-family outcomes were scored. That unscored v1 namespace remains intact
with7,413 raw events. Corrected v2 uses995 source records,992 included five-minute
history sessions and983 complete minute-RSI sessions; nine partial sessions
contribute only complete five-minute bins. Three post-dashboard dates are listed
but excluded, preserving the original inventory policy. Included history runs
from2022-01-03 through2026-09-08. No evaluation-entry prior100-bar window retains
an observed calendar gap exceeding four days after the correction.

The source correction changes entry identities in B02/B03/B04/B08/B09, as expected
for smoothing-dependent features. It changes no B06 identity and therefore cannot
explain the prior B06/IV result reversal. Both original-inventory and corrected-
inventory replays still reproduce all441 dashboard identities. The complete
before/after identity ledger is stored, without scoring or selecting between
the warmup vintages. Corrected v2 produces7,465 raw setup entries and7,313 distinct
variant/date/minute opportunities before the VT gate.

An independent verifier reread all150 native price sources and checked every
one of those7,313 scores, entry prices and causal VT flags without calling the
replay's scorer. It reconciled all585 summary rows and their matched-control
arithmetic, and verified frozen hashes. No fetched inputs or existing dashboard
files were changed. Diagnostic bins and analysis methods were frozen before
outcomes. There were zero ThetaData or ORATS calls.

## Files and reproduction

- Authoritative data: [/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2)
- [Full585-row comparison](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2/comparison.csv):3 VT scopes ×3 entry sensitivities ×5 cohorts ×13 variants.
- [Native-event ledger](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2/distinct_event_outcomes.csv) and [independent verification](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2/independent_verification.json).
- [Warmup identity changes](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2/warmup_event_identity_changes.csv) and [35 added source records](/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_150d_rerun_2026-09-19-v2/warmup_added_sources.csv).
- [Frozen protocol](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_150d_rerun_2026-09-19/PROTOCOL.md), [warmup correction](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_150d_rerun_2026-09-19/WARMUP_CORRECTION.md), [review dispositions](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_150d_rerun_2026-09-19/PERSONA_DECISIONS.md).
- Independent persona reports: [Charlie](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_150d_rerun_2026-09-19/charlie_independent.md), [Brent](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_150d_rerun_2026-09-19/brent_independent.md). These are synthetic analytical lenses, not participation by the named people.
- Prior IV/VT evidence: [/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_audit_2026-09-19-v1](/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_audit_2026-09-19-v1).

Runner stages are `complete_history.py prepare`, `freeze`, `generate`, `outcomes`,
then `analyze`; `verify_results.py` independently reconciles final artifacts.
The adapter selects authoritative v2. Direct `run.py`/`analyze.py` default to the
preserved unscored v1 and must not be used as the final replay entrypoint.
Stages intentionally refuse to overwrite completed namespaces; a deliberate
reproduction needs a new namespace rather than deleting the frozen evidence.
