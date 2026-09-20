# Extensive learning record: B09 expansions, volume, and preserved new information

September 20, 2026. Read FINDINGS.md for all numerical comparisons and PROTOCOL.md
for the frozen calculation. This note records what changed in our understanding,
what remains only a proposal, and mistakes future work must avoid.

## 1. Opportunity expansion can work without another threshold search

The fixed B09 sector F4 OR SPX reference was198/318=62.3%. Three separately tested
changes increased observed raw opportunities while leaving the combined rate near
that level: B05 union262/423=61.9%; persistence308/492=62.6%; B07 union254/408=62.3%.
These are successful descriptive expansions of the sampled signal set. They are
not proof that future accuracy is preserved. Shared-date uncertainty for the
change includes both improvement and deterioration in every experiment.

No fourth strategy combining all three changes was tested. No new magnitude,
sector count, quote guard, trading hour, timeframe or duration sweep was run.
The original first-move objective stayed intact: +5 before−10 within60 bars;
post+5 reversal is irrelevant. The existing price trigger and causal VT gate
were reused and replayed on native prices.

## 2. Larger N has several meanings, and they give different rankings

Persistence is the largest raw-signal expansion:174 new entries and110 targets.
B07 adds90 entries and56 targets but27 new active dates, compared with18 for
persistence and19 forB05. The raw B05 increment is105 entries and64 targets.
Those are different opportunity profiles; none should be labeled a universal winner.

Within60 minutes of a base entry lie119/174 persistence additions,48/105 B05
additions and24/90 B07 additions. This does not invalidate multiple trades, but
those observations share market paths and are not independent new evidence.
No-spacing remains primary because the user requested it. Spacing is reported
to expose concentration and policy effects, not secretly substituted for it.

## 3. Earlier admissible entries can displace later winners

The60-minute baseline was107/175=61.1%. Full chronological union replay gives
B05 139/230=60.4%, persistence138/235=58.7%, B07 142/235=60.4%. Simply adding the
standalone candidate's spaced events would give incorrect accounting.

Persistence adds78 executions to the thinned baseline's set but displaces18;
their respective target counts are48 and17. The net result is60 more executions
and31 more targets. The fact that17 of18 displaced baseline entries won explains
why raw63.2% additions do not mean a better spaced policy. This is an observed
timing/selection effect, not authority to tune spacing or use eventual success
to choose which signal to keep. First-per-day also changes membership and must
be re-run on the union.

## 4. New-date evidence is weaker than the pooled expansion headline

Additional B05 signals on existing base-active dates are54/77=70.1%; on entirely
new dates10/28=35.7%. Persistence is98/149=65.8% versus12/25=48.0%. B07 is38/54=70.4%
versus18/36=50.0%. New-date samples are too small for firm rate comparisons, but
the distinction is material to claims about adding independent opportunities.

The “base-active date” label uses the eventual full day and can include a later
baseline signal. It is a retrospective explanation only. An implementation that
admits an earlier signal because B09OR eventually fires that day would leak the
future. Likewise, same-block B09 overlap from the earlier B05 study is not an
entry-time permission rule. Keep these fields diagnostic.

Individual-day deletion still shows that no single session creates the pooled
union results. Those narrow deletion ranges retain almost all original data;
they must not be sold as narrow confidence intervals or as a fix for overfitting.

## 5. Persistence must preserve instrument identity and information time

At one endpointu betweenT−5 andT−1, the samefour ETFs must have qualified together.
Each must still have a valid negative IV slope atT−1. Do not combine one sector's
burst atT−5 with another's atT−2 to invent simultaneous breadth. SPX is a separate
one-instrument route. Every endpoint uses its own strictly prior historical scale;
crossing an hour-block boundary does not authorize mixing scales or recomputing
the past with the current baseline.

A current missing observation is not still-falling IV. The expanded rule requires
current measurement eligibility and never forward-fills a quote. Retaining a
recent valid signal is an explicit hypothesis, distinct from repairing bad data.
IncludingT−1 makes every old OR qualifier a member of the raw expanded set;
that monotonicity does not survive chronological thinning in general.

The source proof ledger records five endpoints for eleven ETFs plusSPX at each
of3,141 B09 entries, with source-minute support and first qualifying witnesses.
An independent scalar implementation reproduced every classification.

## 6. The B07 addition uses the older rule, not the sparse MAD transfer

The candidate is original_accelerating_6: six of eleven sectors with falling IV
and downward acceleration under the original completeT−35…T−6 reference and quote
policy. It is not B07MADF4, which had only21 entries, and not a retimedT−1 variant.
The prior96/157 headline uses the full2024–2026 calendar. Here the exact common
2025–2026 calendar yields91 candidates and90 additions after one duplicate.
Keeping the source clock explicit prevents attributing a change to the price
trigger when the measurement definition also changed.

## 7. A simple volume gate did not earn its cost

RVOL>1 within currentB09OR gives84/136=61.8%, versus92/148=62.2% for ordinary volume.
Its difference interval is broad and includes zero. A hard gate would throw away
92 observed-volume winners without an observed accuracy gain;34 volume-unknown
base signals contain22 more winners. They are not automatically allowed or rejected
by pretending unknown volume is a sign.

The broader parent had a modest pooled high-volume advantage, but its sign reversed
inside matched date/hour blocks under equal-date weighting. The compared samples
and weighting change, and price balance is not perfect. This is evidence against
declaring a robust simple volume improvement, not proof that low volume is a
bullish signal. No inverse filter was selected after seeing the comparison.

Data quality changes the usable denominator. Current five-bar availability covered
2,906 entries; requiring complete60-session baselines leaves2,766. An extra140
entries fail historical support, and235 have no current data afterJune11. Nasdaq-
venue SPY share volume is a consistent-feed activity proxy, not consolidated
volume, index volume or signed customer flow. Do not stitch a new feed into the
old baseline without treating it as a measurement change.

## 8. Preserve the user's new skew hypothesis exactly

The latestSPX study measured30-day ATM IV acceleration. The proposed new feature
is **short-dated call skew for rising sector ETFs and their rising constituents**,
including whether skew strengthening accelerates. Earlier30-day sector skew
diagnostics do not answer it. An initial author response incorrectly narrowed
the new idea toSPX; the research review and pilot now explicitly correct that.

For each ETF or company pair its own price rise with its own call-wing richness
relative to its own ATM IV. First assess strengthening; then assess acceleration
among strengthening cases. This separates the second derivative's contribution
from the first derivative and from price movement itself. Improving risk reversal
can also reflect puts cheapening; do not call it call buying without the separate
wing decomposition. Total option volume and computed IV do not reveal signed
dealer exposure or prove a hedging mechanism.

Seven-calendar-day,25-delta call richness is a proposed fixed measurement, not
a validated optimal tenor/delta. ETF and constituent options are different data
sources. Historical ETF membership/weights and their publication timing are
required; current holdings or eventual winners cannot select old constituents.
Missing weights stay explicit. A top-three measurement pilot cannot stand in for
full-sector breadth or exactSPX contribution.

## 9. New-information registry and present status

| Idea | Status after this execution | Next honest question |
|---|---|---|
| B05F4 union | Tested, observed rawN expansion near same accuracy | Does marginal quality repeat on distinct dates? |
| Five-minute IV persistence | Tested, largest rawN expansion, weaker spaced policy | Is the desired execution policy able to use the added signals? |
| B07 original six-sector union | Tested, most new dates, variable marginal half-year rates | Does new-date accuracy improve with more observations under the fixed rule? |
| SPY relative volume | Tested, no useful current-rule improvement | Do not tune a rescue threshold; actual transaction pressure is a separate question |
| Short-dated sectorETF call skew | Ten-date measurement pilot prepared, no collection/test | Are native short-tenor quotes and curvature measurable? |
| Rising-constituent short-dated skew | Pilot scope prepared; dated holdings/readiness unresolved | Does constituent skew add information beyond its price leadership? |
| Skew acceleration | Preserved as nested comparison after strengthening | Does curvature add anything beyond first derivative and quote noise? |
| Transaction pressure/order-book imbalance | Preserved, untested, source readiness unverified | Is measured buying pressure useful beyond volume and price? |
| Short-versus30-day term structure | Preserved as a diagnostic, untested here | Does near-term stress add information beyond ATM level/direction? |
| Scheduled-event proximity | Preserved as timestamped context | Are apparent effects selection of different event risk? |
| Constituent leadership/concentration | Preserved as the price control for skew | Is the index advance broad or driven by a few observed leaders? |
| Nearby liquidity/positioning | Preserved, untested | Are levels measured causally with defensible exposure semantics? |

No new strategy was adopted, no thresholds were searched, and no short-dated
data or order-book data were acquired. All datasets remain central. All original
measurements and studies remain unchanged. These notes preserve unsuccessful and
untested ideas as well as the encouraging raw-N comparisons.

## 10. Review and validation status

The canonical Quant and Charlie personas were used as analytical lenses by this
assistant in the preceding proposal, not as independent reviewers. This side
conversation disallows reviewer agents, so none were launched for this execution.
During commit preparation, the main thread's independent proposal review was
discovered complete: generic FAIL (13), Quant FAIL (16), Charlie CONDITIONAL PASS
(9). Its raw reviews and author corrections are separate, untouched artifacts.
They predate these execution results and do not constitute approval of them.
The historical research-review draft's NOT RUN wording describes its creation
time; it is not the current status of the main-thread proposal review.

The review correctly emphasized exact marginal accounting, spacing displacement,
volume support and same-sector persistence. These are now measured here. Its
price-volatility alternative remains a separately defined future comparison;
reporting prior price balance does not execute that matched test. Do not adopt
reviewer shortcuts that inferred marginal outcomes from hourly overlap, declared
supersets unable to improve accuracy, or replaced the user's first+5 objective
with conditional-on-resolution success. The main-thread response explicitly
corrects those claims. Neither reviewers nor this execution add independent
market observations or overcome the history of searches.

Eight boundary tests andRuff pass. Frozen hashes,3,141 scalar persistence votes,
415 originalB07 classifications,3,141 raw-volume features,5,093 nativeVT/outcome
replays,105 event summaries,120 volume summaries,1,912 day deletions,45 chronological
change rows andtwo within-block controls are verified. Tests check causality,
same-sector identity, unknowns, complete historical support, deduplication and
spacing displacement. Verification is evidence about implementation correctness;
it does not turn reused historical performance into forward validation.
