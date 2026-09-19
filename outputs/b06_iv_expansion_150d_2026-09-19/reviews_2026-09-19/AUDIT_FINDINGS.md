# Why the B06 / IV conclusion changed

19 September 2026. This audit supersedes the interpretation in the original
expansion report; it preserves every frozen input and historical result.
The only success criterion here is **SPX +5 before −15 within 60 native minute
intervals**. What happens after a successful first touch is irrelevant to this audit.

## What the audit establishes

There is a real eligibility mismatch: the study selected days that **opened**
above Vol Trigger, then accepted B06 signals even after SPX fell below it.
It did not enforce “above VT at entry” or “always above VT.” That is my research
definition error relative to the user's clarified requirement. The opening-only
rule was explicitly recorded in the protocol, but recording it did not make it
equivalent to the intended trading regime.

The numerical collapse is not explained by that mismatch. Excluding below-VT
entries leaves the original IV rule at 72.5% on the old dates and 49.7% on the
added dates. Plain B06 moves from 62.9% to 55.2% under the same entry gate.

Three further facts explain where the apparent edge went: the new population has
more signals that never travel far enough within an hour; IV disproportionately
selects weaker B06 days in the added sample; and its original advantage among
signals on comparable dates largely disappears. These are measured descriptions,
not proof of a single economic cause. Repeated exploration of the original dates
and the uncertain IV acceleration measurement make sample-specific optimism
plausible. Neither explanation has been identified as the sole cause.

## Independent reviews and reconstruction

| Review | Verdict | Main result |
|---|---|---|
| [Claude code review](claude_code.md) | CONDITIONAL PASS | No verified calculation error in this run explaining the reversal; nine findings, primarily replay/validation weaknesses |
| [Claude strategy review](claude_strategy.md) | CONDITIONAL PASS | Narrow the conclusions; separate date selection, regime, uncertainty and same-day comparisons; nine findings |
| [Local red-team audit](RED_TEAM.md) | FAIL for the intended above-VT claim | Opening eligibility fails the intended intraday regime; independently reconstructed numerical results pass |

Both Claude reviews used the requested independent Opus 5/xhigh wrappers with
read-only tools. Neither received the other review. Their initial prompts preceded
the user's explicit “always above VT” clarification. The local red-team audit
subsequently checked that requirement across every day and entry.

The independent audit imports none of the study's signal, scoring or slope
functions. It rebuilt all **1,040** immediate B06 signals from native SPX bars,
including their frozen six-bar ceilings and repeated-level suppression; all
entry prices and +5/−15 first-touch outcomes matched. It recomputed **44,812**
available-panel sector/event/policy records using a separate least-squares fit
and checked all **4,160** baskets across the full **45,760** sector-row grid.
The original 50-day table remains exactly reproducible. The 15 existing unit
tests pass. This does not independently validate ThetaData's IV inversion model.

The day-opening CSV loses one float64 ULP on 2026-06-22: 7500.44 versus native
7500.4400000000005. The audit allows exactly one ULP for that comparison. VT
eligibility, signals and outcomes are unchanged. This is not an explanation of
the performance change.

## Vol Trigger: precisely what was included

VT is the positive same-date, preopen-corroborated daily level already frozen in
the study. Every day was checked against the source VT CSV and all 390 native
SPX minute bars. We do not invent an intraday-changing VT series.

| Check | Original 50 | Added 100 | Combined |
|---|---:|---:|---:|
| Days opening strictly above VT | 50 | 100 | 150 |
| Days touching or falling below VT during RTH | 20 | 34 | 54 |
| Days with a minute close at/below VT | 20 | 33 | 53 |
| B06 entries below VT | 34 | 46 | 80 |
| Entries above VT when taken | 340 | 620 | 960 |
| Entries continuously above VT from open through entry | 265 | 497 | 762 |

All 80 disallowed entry prices were strictly below VT, and their preceding
breakout closes were below VT too. None is a rounding-edge equality. Another
198 entries were above VT when taken but followed an earlier session breach.

Example: on **2025-10-10 at 13:30 ET**, the entry was **6620.05** against VT
**6725**. The session opened at 6740.49. Calling that an above-VT entry would
plainly be wrong. Exact date/time/price/VT rows for all 80 exceptions are saved
in `below_vt_entries.csv`; the full 150-day chronology is in `day_vt_audit.csv`.

The tables below restrict the already frozen B06 parents. They do not change
IV thresholds, generate replacement dates, re-score outcomes, or redesign the
original repeated-ceiling suppression. They are corrective scope checks, not
a new independent discovery sample.

### Restrict to SPX above VT at entry

| Rule | Old dates: wins / entries | Hit rate | Added dates: wins / entries | Hit rate |
|---|---:|---:|---:|---:|
| Plain B06 | 214 / 340 | 62.9% | 342 / 620 | 55.2% |
| Original IV validity | 58 / 80 | 72.5% | 95 / 191 | 49.7% |
| Allow bid-IV recovery | 67 / 97 | 69.1% | 108 / 209 | 51.7% |
| Recovery + 100% spread guard | 45 / 63 | 71.4% | 78 / 148 | 52.7% |
| Recovery + 50% spread guard | 21 / 27 | 77.8% | 44 / 90 | 48.9% |

This restriction removes a genuine mistake but does not restore the apparent edge.
In the combined entry-above population the 100% guard is slightly higher than
baseline, **58.3% versus 57.9%**. Thus “every row trails baseline” must not be
carried from the original opening-only table into this different population.

### Require no VT breach from the open through entry

Each prior observed minute low must be strictly above VT, and the entry open
must be above it. The entry minute's subsequent low and all future bars are
excluded from this eligibility test.

| Rule | Old dates: wins / entries | Hit rate | Added dates: wins / entries | Hit rate |
|---|---:|---:|---:|---:|
| Plain B06 | 167 / 265 | 63.0% | 263 / 497 | 52.9% |
| Original IV validity | 39 / 58 | 67.2% | 76 / 151 | 50.3% |
| Allow bid-IV recovery | 47 / 74 | 63.5% | 88 / 168 | 52.4% |
| Recovery + 100% spread guard | 34 / 50 | 68.0% | 64 / 118 | 54.2% |
| Recovery + 50% spread guard | 14 / 20 | 70.0% | 33 / 70 | 47.1% |

One small positive hint survives: the 100% spread guard has **+1.3 percentage
points** over baseline on the added dates. Its paired date-bootstrap 95% interval
is **−6.8 to +9.5 points**; the month-block interval also spans zero. This is not
strong evidence for a mandatory filter. It is also incorrect to say every
version performed worse under this stricter interpretation.

Exactly **96 of 150 days** never touched VT anywhere in the complete session.
For completeness, `vt_comparison.csv` also reports that subset, explicitly named
`whole_day_above_descriptive`. On its added dates B06 is 53.3%, the original IV
rule 51.7%, bid-IV recovery 53.5%, the 100% guard 56.4%, and the 50% guard 48.5%.
These are hindsight-conditioned descriptions: excluding an otherwise eligible
13:00 entry because VT breaks at 15:00 would select using the future. They
cannot establish a rule usable at 13:00.

## Diagnosis 1: the baseline drop was mostly more unfinished moves in 2025

These figures use the frozen opening-above cohort to explain the originally
reported reversal, rather than silently changing its denominator mid-explanation.

| Plain B06 population | Signals | +5 first | −15 first | Neither within one hour |
|---|---:|---:|---:|---:|
| Original 50 dates, all 2026 | 374 | 63.9% | 13.6% | 22.5% |
| Added 66 dates in 2025 | 442 | 52.0% | 10.9% | 37.1% |
| Added 34 dates in 2026 | 224 | 62.9% | 10.7% | 26.3% |

The added 2025 signals were not mainly turning into more −15-first failures.
Many more simply did not reach +5 or −15 before the fixed hour expired. They
are two thirds of the new signal population, so their lower hit rate pulls down
the new aggregate. Arithmetic attributes about **7.9 of the 8.2-point baseline
drop** to the difference between added-2025 and original hit rates; about 0.3
points comes from added-2026. This is a decomposition, not causal identification.

A measurement available before every entry supports a different movement
environment: the median SPX range from 09:30 through 10:04 was **21.7 points**
on the 66 added 2025 days, versus **27.1** across the original 50 days and **24.9**
on the 34 added 2026 days. All 50 dates, including the zero-signal date, are
included in that 27.1 comparison. The machine-readable cohort-year outcome
table separately records active-day medians (27.3 for the original 49 active
days); these are different denominators, not conflicting prices.

This is evidence consistent with smaller movement making a fixed +5 harder
to achieve. It does not prove that lower volatility caused every missed target,
and it does not explain away the IV filter's loss of incremental advantage.

## Diagnosis 2: the IV condition selected a different mix of days

For the original IV rule in the added sample, the raw figures are **55.7%** for
all B06 versus **50.0%** for IV-qualified entries. Give each day's plain-B06
success rate the same weight as the number of IV-qualified entries on that day.
The weighted B06 benchmark falls to **51.6%**.

That yields an exact descriptive decomposition of the **−5.7-point** difference:
**−4.1 points** from weighting dates differently, and **−1.6 points** remaining
within those weighted dates. About 72% of this observed aggregate deficit is
date composition. The filter was firing disproportionately on days where B06
itself had fewer successes. It was not clearly identifying bad individual entries
within otherwise identical conditions.

In the original sample, the same calculation gives a **+1.1-point** date-mix
component and a **+7.1-point** within-date residual, totaling the old **+8.1-point**
apparent gain. So the earlier result was not *only* favorable date weighting;
the within-date relationship also changed. The decomposition is descriptive
because each day's benchmark uses that day's realized outcomes. It is not a
predictor we could calculate at entry.

## Diagnosis 3: the original “avoid stalling” association did not persist

Compare the original IV rule's definite yes and definite no states, keeping
unknowns out of that contrast:

| Population | Neither: IV yes | Neither: IV no | −15 first: IV yes | −15 first: IV no |
|---|---:|---:|---:|---:|
| Original 50 | 14.0% | 26.4% | 14.0% | 12.5% |
| Added 100 | 35.6% | 33.5% | 14.4% | 8.7% |

Originally IV yes was associated with substantially fewer stalls. In the added
sample that distinction disappears. It never demonstrated protection against
−15-first outcomes in the original sample, either. These are unadjusted group
percentages and do not establish that IV causes either outcome.

To compare within dates, weight each date with both yes and definite-no entries
by `n_yes * n_no / (n_yes + n_no)`. The yes-minus-no hit-rate difference falls
from **+14.1 points across 34 comparable dates** to **−1.2 points across 81 dates**.
The strategy reviewer’s date-bootstrap interval for the latter is **−9.5 to +7.4**.
Using all other entries, including unknowns, gives different contrasts; those
are separately labelled `same_day_yes_vs_other_pp` in the audit data. Unknown
must never be silently equated with definite no.

Neither the near-zero within-day result nor the raw negative aggregate supports
turning this into an “avoid IV confirmation” rule. The evidence establishes a
failure to demonstrate a stable advantage, not a dependable reverse signal.

## Diagnosis 4: what the evidence cannot identify

**The original sample was heavily explored.** Numerous B06, IV, price-breadth,
timing and recovery ideas were examined on these same dates. Choosing promising
conditions after seeing those results makes the old percentages optimistic as
forecasts, even when every calculation is correct. The original paired-date
intervals already included zero. That is evidence of fragility and a reason to
expect regression; it is not proof that a particular percentage of the reversal
was overfitting. The fixed expansion prevents new threshold tuning; it cannot
retroactively turn the original sample into an untouched test.

**The added sample is not a balanced cross-section of every regime.** Preopen
note provenance and opening-above-VT eligibility restrict the sample; no
March–July 2025 dates were selected. The added dates are new to this comparison,
not certified unseen across all research. The negative new-2026 point estimates
show the aggregate pattern also appears there, but 34 dates cannot prove that
year/regime differences are irrelevant. The four IV variants overlap heavily;
they are not four independent replications.

**Acceleration may be too noisy to carry the proposed interpretation.** The
earlier acceleration study reported zero of 1,604 qualifying sector/event
acceleration signs resolved beyond conservative propagated quote envelopes.
That does not show midpoint patterns cannot predict; it does mean that the
claim “we measured new options information accelerating downward” is not
established. This audit reproduces the provider-IV calculation, not an
independent fair-IV estimate or the real information content of quotes.

**Coverage affects who is eligible.** The first 10:05 signals require the 09:30
IV observation; all 18 are unknown under all four policies in the actual stored
data. There are 35 missing sector-day brackets in the combined sample. These
were retained as missing, not replaced by favorable dates. Earlier time-of-day
adjustments in the strategy review do not reverse the main opening-cohort result.

**Intervals depend on clustering assumptions.** Date bootstrap accounts for
signals sharing a day but not arbitrary dependence between days. The original
rule's added-sample uplift interval of −11.0 to −0.4 under date resampling widens
to roughly **−11.9 to +0.3** under month-block resampling. With few month blocks
and prior exploration, neither should be read as a precise causal claim.

## What I am correcting

The old results were encouraging observations, not a reliable established edge.
I should have made the eligibility definition and uncertainty central sooner.
The new results do not justify declaring IV intrinsically harmful or all IV ideas
useless. Under the user's continuous-above-VT interpretation, the guarded-100
version retains a small, uncertain hint. None of the four has demonstrated the
stable hit-rate improvement needed to make it a mandatory B06 filter.

No market data was fetched for this audit. No frozen thresholds or original
tables were overwritten. The full audit data is at
`/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_audit_2026-09-19-v1/`.
The reproducible checks are `audit_frozen.py` and `diagnose_shift.py` beside this
report; both refuse to overwrite completed audit outputs. See the root central
changelog and dictionaries for inventory and provenance.
