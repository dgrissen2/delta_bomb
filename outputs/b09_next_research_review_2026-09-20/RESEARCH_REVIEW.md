# B09: new information for accuracy, existing information for more opportunities

September 20, 2026. Author analysis using the canonical Quant and Charlie analytical
lenses. These are not separate reviewers, and Charlie is a simulated persona,
not the actual person. Independent Claude review has **not run**: reviewer agents
are disabled in this side conversation. The requested skill was read and its
logic-review checklist applied locally. No new strategy outcomes were calculated.

**Recommendation:** keep the current B09 sector-F4-or-SPX rule fixed. First inspect
incremental B05 opportunities and isolate SPY relative volume. The most useful new
options hypothesis is short-dated call richness in sector ETFs and their rising
constituents, including whether that richness is accelerating. A short, causal IV-confirmation
window is a plausible way to expand N using current measurements, but needs its
own explicit test. None of these proposals has demonstrated an improvement yet.

## 1. The evidence that constrains the next tests

The objective stays **+5 SPX points before −10 within 60 native minute bars**,
including entry. Nothing after +5 changes a winner. Keep strict causal above-VT
eligibility, native SPX entry prices, unknown outcomes and the existing entry clock.
The primary policy is no spacing; existing first/day and 60-minute spacing are
dependence/execution sensitivities, not replacements for the user's objective.

| Finding | What the next proposal must respect |
|---|---|
| B09 F4 OR SPX: 198/318, 62.3%, on121 active dates in2025–September18,2026 | Current fixed reference; an accuracy filter reduces this N, while a union may expand it |
| F4 alone:115/188,61.2%; OR adds130 entries and83 winners | Alternative sources can expand opportunity; the observed addition does not establish a repeatable future rate |
| Both sector and SPX confirm:32/57,56.1% | More agreement is not automatically better; do not stack confirmations by intuition |
| OR raw uplift+8.0pp; same-date+4.7pp; within-date/block+2.9pp, interval−3.6 to+9.4 | Favorable times explain part of the headline; new information must be compared within similar market conditions |
| OR61.3–63.1% after any individual-day deletion; top five winning days17.2% of wins | No single session drives the pooled result; this is not a narrow confidence interval or fresh validation |
| Partial2026H2:18 signals onseven days | Too thin to decide stability in either direction |
| OR107/175=61.1% spaced;70/121=57.9% first/day | Repetition policy changes the result; new raw signals need separate active-day and spaced counts |
| B05F4:70/112=62.5%;65/100=65.0% spaced | Existing alternative trigger worth checking for incremental opportunities |
| B05F4 outside a corresponding B09F4 date/block:37/70=52.9% | Independent opportunity is unproven; favorable overlap can account for the headline |
| B07F4:14/21 | Too sparse to prioritize as a standalone accuracy winner |
| Older B07 six-sector acceleration:96/157=61.1% versus393/769=51.1% | A different frozen rule on2024–2026; useful secondary expansion candidate, not interchangeable with MAD F4 |
| Expanded B06:50.7% plain,50.1% falling IV,49.8% acceleration | The early50-day story failed broader replication; preserve the negative evidence |
| B09 broad sign controls approximately54.1%, near plain54.3% | Simply loosening magnitude to any negative acceleration did not retain the observed improvement |

The older IV inventory included105 rule labels; the later MAD grid included48
cells. Their findings are exploratory, with reused observations and related
features. New historical tests must acknowledge that search history.

## 2. Quant lens: what would count as useful new information?

An additional data source need not be statistically independent to be useful.
The requirement is **incremental information at the decision time**. A second
transformation of the same price/IV movement can be highly correlated and still
look persuasive when shown as a separate confirmation. Conversely, a correlated
feature can help on the disagreements; it should not be rejected merely for
having nonzero correlation.

The largest unresolved confound is selection of favorable dates, times and
volatility conditions. +5 and −10 are fixed point barriers: the same five-point
move represents a different hurdle in calm and volatile markets. High activity
can increase target hits by reducing timeouts, without identifying better upward
direction. That still matters to the user's objective, but it needs to be named
correctly. Use observed prior30-minute SPX volatility and return as diagnostic
controls; do not replace +5/−10 with an ATR target or require a sustained rally.

For each new feature, use the same feature-observed population for the reference
and challenger, preserve unknowns, and show existing-rule yes/no crossed with
feature yes/no. The first pair of cells addresses accuracy inside the318-entry
rule; the second addresses potential additions outside it. No performance is
claimed for missing-data cells. Same-date/block comparisons and available support
matter more than selecting whichever pooled cell looks best.

For expansion, inspect the added entries on their own. If base accuracy is p,
N base entries and n genuinely added entries with accuracy q produce
`(N*p + n*q)/(N+n)`. To maintain the observed base rate exactly, q must be at least
p. For example, adding100 entries to198/318 would require at least63 additional
winners to avoid lowering its historical percentage. That is arithmetic, not a
prediction or a statistically established noninferiority margin.

## 3. Charlie lens: which mechanisms are plausibly different?

The current rule primarily describes **unusually rapid cooling in option-implied
volatility** while the price trigger describes a small upward staircase. Two
different questions remain: is there active buying behind the price move, and
can an upward move be driven by demand for calls even when ATM IV does not cool?

Those motivate volume/transaction-pressure data and short-dated upside richness.
The hypothesis is not that every call-skew increase causes dealers to buy, or that
every high-volume green bar is accumulation. Quote-based IV is not signed order
flow; total call volume does not identify who bought, who sold, or dealers' net
exposure. Even an authentic upside chase can reach the user's first+5 and later
reverse; that later reversal must not be relabeled a failure.

For N, treat the IV condition as a possible description of a favorable interval,
then ask whether an existing price trigger arrives slightly after the strongest
acceleration reading. This is a timing hypothesis, not authority to forward-fill
missing quotes, carry the signal indefinitely, or admit entries based on a later
confirmation. B05 and B07 can offer different entry geometry in the same interval;
their marginal entries must justify themselves.

## 4. Ranked new-information candidates

### A. SPY relative volume — cheapest useful first experiment

**Question:** does a B09 staircase accompanied by unusual actual trading activity
reach+5 more often than one occurring on ordinary activity?

Proposed single feature: trailingfive completed RTH minutes of SPY share volume,
divided by the median same-clock five-minute volume over60 strictly prior sessions.
Use the same feed throughout; require complete windows and adequate prior history.
`RVOL>1` is one simple proposed split, chosen for an interpretable historical
reference, not because it has been validated. No cutoff sweep or multiple lookbacks.
The five-minute window matches the slower chart context; sixty sessions reuses
the existing normalization horizon. These are design choices, not natural constants.

**Availability checked without outcomes:** the existing central XNAS.ITCH cache
has1,509,057 rows over2,040 dates,2018-05-01 through2026-06-11; no duplicate date/minute
keys. It overlaps214/239 research dates and supplies the five preceding minute rows
for2,906/3,141 B09 parents. This establishes row availability only: volume quality,
historical baseline completeness and retained OR-cohort coverage still need checks.
It is Nasdaq-venue SPY volume, not consolidated US trading volume. SPX itself has
no traded volume. Do not mix feeds within a baseline or call a green-bar signed
volume proxy buyer-initiated flow.

Volume was proposed earlier, and a bullish range/volume event looked weak. A clean
relative-volume ablation on the current B09/IV cohort was not found in the reviewed
results. This is an untested application, not a previously successful indicator.
Compare against the same return/range conditions; if improvement disappears after
accounting for realized movement, call it an activity/volatility effect.

### B. Short-dated sector and rising-constituent skew — the user's distinct hypothesis

**Scope correction:** the latest SPX experiment measured30-day ATM IV acceleration.
It did not test short-dated sector ETF skew or the skew of rising constituents.
Older sector experiments included30-day call richness, put richness and risk
reversal; their B06 results do not answer this more specific proposal. One archived
B05 rising-call-richness diagnostic was64/106=60.4%; it was a selected observation,
not a validation of short tenor, constituent conditioning or skew acceleration.
The initial author proposal over-narrowed the new idea toSPX; this section corrects it.

**Question:** when the underlying sector or company is already rising, is its
upside call wing getting richer, and is that strengthening speeding up? Does it
help distinguish which B09 setups reach+5 first, particularly when broad ATM IV
does not fall enough to pass the current rule?

Start with a proposed fixedseven-calendar-day tenor and25-delta call wing. For
each instrumenti, measure its own
`C_i(t) = IV_i(25-delta call,7D,t) − IV_i(ATM,7D,t)`.
Over the same30 completed minutesT−30 throughT−1, fit actual-time OLS slopesb1
andb2 on the first and second15-minute halves. Skew strengthening meansb2>0;
positive curvature/acceleration is`a_C=(b2−b1)/15>0`. IV in percentage points gives
b unitsvol-points/minute anda_C unitsvol-points/minute². This is our discrete
two-slope acceleration proxy, not an exact instantaneous second derivative.

For example, call richness moving from−2 to−1 means the call wing has become
relatively richer even though it remains below ATM. If it rose slowly in the first
half and faster in the second, acceleration is positive. Rising call richness does
not require ATM IV to fall. A separate put-richness coordinate
`P_i=IV_i(25-delta put)−IV_i(ATM)` explains whether a risk-reversal change comes
from upside repricing or cheaper downside insurance. Do not countC,P andC−P as
three independent confirmations.

**B1 — sector ETF level.** Keep the existing eleven ETFs. Pair each ETF's return
overT−30 throughT−1 with its ownC,b2 anda_C over that exact window. Record the
count/share of sectors that are rising and have strengthening call skew. Then
separately ask whether acceleration adds information among those already showing
strengthening skew. Keep flat/nonrising price cases as controls, and all quote/
expiry unknowns visible. A greater count of rising sectors alone already contains
price information; compare like price participation and return strength before
crediting skew. Do not automatically reuse the ATM-F4 four-sector threshold for
this new coordinate or choose the best breadth cutoff after viewing outcomes.

**B2 — constituent level.** Use dated sector-ETF holdings, with weights and any
option-liquidity eligibility known before the session. At each entry, identify
the constituents whose own observed30-minute returns are positive; pair their
own short-dated skew and acceleration with their own price rise. Today's holdings
cannot be substituted into past dates. Avoid selecting the eventual day's winners
or choosing a handful of names based on their later performance.

Use within-sector weight shares as descriptive features, with the full predeclared
weight denominator retained and missing mass explicit. Report known positive,
known negative and unknown weight; do not renormalize missing names into a
stronger confirmation. Also report the price-rising weight so skew can be assessed
conditional on price participation. Keep this distinct from weighting an ETF's
own option surface: ETF options need not summarize the option demand in their
constituents. Any aggregated index measure needs a separately valid mapping;
do not present sector-ETF holding weights as exact SPX contribution weights.

The most relevant control is a similar price rise without skew strengthening;
the incremental second-derivative test compares strengthening-skew entries with
and without measured acceleration. Do not assume acceleration deserves its extra
measurement noise merely because the ATM-MAD version was promising. Normalize or
compare instrument magnitudes only with a predeclared prior-history method; raw
skew acceleration is not directly comparable across ETFs and volatile constituents.
Breadth of reliable signs is a simpler initial feature than anotherMAD cutoff grid.

Seven days is a proposed fixed tenor, not a proven optimum. Before any outcome
study, audit whether the sector ETFs and proposed constituents actually have
listed expiries/usable strikes that bracket it. No extrapolation, no substituting
30DTE where7DTE is missing, and no search of tenors to find the best hit rate.
Constituent earnings schedules known at entry and maturity roll are measurement/
context diagnostics; do not use later-reported surprises. Fixed-delta interpolation
and changing spot can move calculated IV without fresh option-price information.
Check actual quote changes and same-contract behavior, especially for acceleration.

The reviewed caches do not establish a ready short-tenor ETF/constituent dataset.
First perform an outcome-blind availability/measurement pilot, choosing its universe
and dates without knowing which entries win. Freeze the aggregation and any one
admission threshold before testing outcomes. If native acquisition is required
later, use the ThetaData SDK, minute data and central storage. No provider request
was made in this review. Short-tenorSPX skew is an optional benchmark, not a
substitute for the sector/constituent hypothesis the user asked to preserve.

### C. SPY or ES transaction pressure / order-book imbalance — more distinct, higher cost

**Question:** is upward progress supported by actual pressure at the bid/ask, rather
than just more trading on both sides?

Use a single properly measured series from one declared instrument/feed. True
top-of-book order-flow imbalance includes changes to displayed bid/ask price and
size; trade imbalance instead classifies executed buys versus sells. They are
different measurements. Neither can be reconstructed faithfully from OHLCV or a
minute-end quote snapshot alone. Trade-and-quote sequencing and unknown trade-side
classification require explicit treatment. Market-depth changes can also cancel
quickly; measurement is not a guarantee of a subsequent move.

This has a stronger microstructure rationale than total volume alone: Cont,
Kukanov and Stoikov found order-flow imbalance explained contemporaneous short
interval price changes more robustly than raw volume in their sample. That is
not evidence for forecasting B09's next hour or for this SPX dataset.
[Primary research](https://arxiv.org/abs/1011.6402).

Historical readiness and access are unverified. Defer collection until the simpler
volume experiment and data feasibility justify the work; do not build an engine
or a synthetic HIRO replacement just to test this idea.

### Additional ideas to preserve, not stack into the first experiment

| Idea | Incremental question | Status / limitation |
|---|---|---|
| Seven-day versus30-day ATM term structure | Is immediate stress easing differently from month-ahead stress? | Natural diagnostic alongside the7D collection; correlated with ATM IV, not another independent vote |
| Timestamped scheduled-event proximity | Are signals being scored across a known announcement that changes the next hour? | Context/control first; use only the schedule known before entry, not realized surprise or retrospectively selected event days |
| Constituent leadership and concentration as the price control forB2 | Does constituent skew add anything beyond the price leadership itself? | Previously brainstormed; dated holdings and causal selection required; distinct from testing theETF's own skew |
| Executable nearby liquidity / positioning levels | Is the five-point objective obstructed or supported by an observable liquidity concentration? | Requires timestamped data and validated semantics; gross option volume/OI alone does not establish dealer gamma sign |

Cboe's term-structure descriptions support maturity as a separate measurement
dimension, not a bullish trading rule: [Cboe term structure](https://www.cboe.com/tradable_products/vix/term_structure).
Cboe also explains why large gross option volume need not imply large net dealer
exposure: [Cboe's0DTE analysis](https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options).

## 5. Three bounded ways to expand N with existing measurements

### N1. Union with existing B05 F4, inspect only the additions first

Keep B09 OR unchanged and add existing B05F4 timestamps absent from that set.
Deduplicate exact date/entry-minute executions; different minutes remain different
signals in the primary no-spacing result. Publish new timestamps, new dates,
overlapping60-minute windows, marginal wins/N, and the chronological spaced union.
Never add standalone112 and318 as if all entries were independent additions.

B05 has the most immediately comparable measured support: same sector-MAD sources,
same calendar,70/112 overall,65/100 spaced. But the53%-ish outcomes outside B09
blocks are an explicit warning that additions might dilute accuracy. The existing
block diagnostic can refer to a **later** B09 signal; it must never become an
available-at-entry gate. This test assesses the actual union, not an invented
rule requiring a future B09 confirmation.

### N2. Allow a five-minute-old IV burst while requiring current falling IV

Keep B09 and M>1 fixed. For decisionT, consider exact measured endpoints
`u ∈ {T−5,…,T−1}`. The sector route passes if, at one commonu, at leastfour sectors
each had `M_s(u)>1`, `b2_s(u)<−1e−12`, **and those same sectors** have observed
`b2_s(T−1)<−1e−12`. The SPX route similarly needs one qualifying prioru and observed
negative currentSPX slope. Their OR gives a single proposed expanded rule.

This includes every current qualifier becauseu=T−1 is included. It may also admit
a later staircase after an acceleration burst has subsided. Current source windows
and scales must remain valid; no missing current slope can be treated as still
falling. Prior votes must be simultaneous, not assembled from different minutes.
Every source window for an entry stays beforeT, and existing baseline timestamp
constraints remain unchanged.

Five minutes is one proposed design choice tied to the five-minute context, not
an optimized duration. Do not sweep1–60minutes. Start by auditing existing endpoint
availability without outcomes. The concern is that this merely admits late entries
or more repeats of the same move. Report the new entries separately, and reject
the useful-N story if they dilute accuracy or supply negligible new dates/episodes.
This is deliberate signal persistence, not stale-quote imputation.

### N3. Union with the already-tested B07 original six-sector IV rule

Use the existing original six-sector falling-and-accelerating rule on B07, not
the sparse MADF4 version. Its2024–2026 findings were96/157=61.1%, with an observed
improvement versus plainB07 in each reported half. Its frozen reference endsT−6;
that differs from currentMAD'sT−1 and must remain visible.

Restrict to the same2025–2026 calendar for a first union with B09OR. Reuse the
original measurement/quote rules and score; do not import the full2024–2026
61.1% as the incremental subgroup's rate. Exact timestamps, common days and
shared observation windows may overlap. The only relevant N gain is the actual
increment after deduplication; the accuracy of that increment remains unknown.

This is secondary toN1 because it combines a different measurement clock/policy
and an already-searched family. Do not transferMAD thresholds onto it again or
search among allB0x families for the best union.

## 6. Ideas that should not become shortcuts

- Treating the162 unresolved-sector/SPX-no entries as automatic passes because
  their already-seen100/162 rate looks good. Missingness is not positive evidence.
- Re-fetching every gap as though no permitted expiry bracket were a failed request,
  loosening quote guards, or forward-filling IV just to increase N.
- Requiring both SPX and sector confirmation; that particular intersection looked
  worse, not better, in the existing data.
- Another MAD threshold/sector-count sweep, another EMA/RSI/ADX vote stack, or a
  naive call-volume-as-bullish/dealer-buying rule.
- Using an entire day's eventual B09 activity, full-day above-VT status or later
  IV confirmation to admit an earlier trade.
- Confusing more years of observations with more trade opportunities per day.
- Reopening post+5 givebacks as a success criterion or substituting linear+5/−10
  expectancy for the user's first-move objective.

## 7. Recommended sequence and reporting contract

1. **N1, existing B05 union:** lowest implementation cost; report marginal entries
   even if the result is negative. No need to acquire data or retune rules.
2. **A, SPY relative volume:** one standalone feature on its honest common coverage;
   keep comparisons restricted to that same population. No call-skew intersection.
3. **N2, five-minute IV persistence:** one fixed duration, current measured falling
   condition, same-sector identities, no threshold relaxation.
4. **B, short-dated sector/constituent call richness:** measurement feasibility
   first. Pair each instrument's price rise with its own skew strengthening; assess
   acceleration separately within strengthening skew. Freeze universe, aggregation
   and admission definition before outcomes; inspect current-rule disagreements.
5. **N3, original B07 union:** preserve as the second price-family expansion.
6. Order-flow data and remaining ideas stay queued pending evidence/feasibility.

This is a prioritized research proposal, not permission to run every combination.
No rule is adopted from these recommendations. Existing results are reused and
not renamed holdout evidence. Freeze each precise comparison before attaching
its outcomes; log every attempted comparison and preserve negative results.

For each test: report wins/N and all outcomes; observed/unknown coverage; targets
retained or added; active/new dates; raw and spaced counts; all half-years; whole-
date uncertainty; and influence of individual days. Keep partial2026H2 visible
but do not give its18-entry result decisive weight. For expansion, report both
union-minus-base and added-subgroup accuracy; for filtering, report how many
existing winners are lost. No universal invented N floor or post hoc acceptable
accuracy-loss margin. A wider interval after honest clustering is not failure.

## 8. Evidence and provenance

- [Current transfer/SPX findings](/Users/dgrissen/Dev/delta_bomb/outputs/mad_transfer_spx_2026-09-20/FINDINGS.md).
- [Day-influence findings](/Users/dgrissen/Dev/delta_bomb/outputs/b09_or_day_influence_2026-09-20/FINDINGS.md).
- [Full prior-IV findings](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/FINDINGS.md)
  and [idea inventory](/Users/dgrissen/Dev/delta_bomb/outputs/branch_b_iv_full_2024_2026_2026-09-19/IDEA_INVENTORY.md).
- [Accumulated branch notes](/Users/dgrissen/Dev/delta_bomb/outputs/ohlcv_branch_design_2026-09-12/OHLCV_BRANCH_COMBINATIONS.md).
- [Earlier independent-review response and accepted constraints](/Users/dgrissen/Dev/delta_bomb/outputs/b09_mad_followup_plan_2026-09-20/REVIEW_RESPONSE.md).
- [Adjacent one-/five-minute evidence](/Users/dgrissen/Dev/spy_chaser/outputs/trend_catching_research_review_2026-09-12.md).
- Canonical lenses: [Quant](/Users/dgrissen/.config/persona-review-kit/personas/strategy/quant.md)
  and [Charlie](/Users/dgrissen/.config/persona-review-kit/personas/market/charlie-mcelligott.md).
- [Requested review skill](/Users/dgrissen/Dev/persona-review-kit/skills/claude-strategy-review/SKILL.md).
- SPY data inspected read-only:
  `/Users/dgrissen/Dev/central_trade_data/databento/spy_ohlcv_1m/spy_ohlcv_1m.parquet`.

No new strategy outcomes, market-data downloads, parameter searches, external
reviewer runs, dashboard changes or edits to existing study sources occurred in
this review. Only the new review package was written.
