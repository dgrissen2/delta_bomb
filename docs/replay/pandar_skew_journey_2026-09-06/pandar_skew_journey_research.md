# Delta, distance and the high-call-skew journey

**September 8 update — larger tests without HIRO:** [The new report](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_no_hiro_2026-09-08/pandar_no_hiro_research.md) analyzes 17,458 eligible high-wing stock-dates across 643 signal dates, plus 1,163 exact-chain input cases across 203 dates. It uses the authorized actual-earnings exclusion and no HIRO features or coverage gate. The tested slowdown rule does not improve the specified outcome; the economic strike selector does not establish profitable new-name trades. These separately frozen follow-ups preserve the earlier results below with their original scope.

**New hypothesis study:** the [June trade results](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/pandar_trade_results.md) apply the authorized retrospective 30-day earnings exclusion, preserve fifty frozen episodes, and compare both legs using actual quote-event history. See the [three-round decision memo](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/memo-pndr_pandar_call_research.md) and [complete eligibility/richness tables](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/eligibility_and_richness_tables.md). The earlier August examples below retain their original, separate evidence status.

**September 7 review update:** exact quotes now support the ten-example four/five-session
comparison below. Two mature cases have profitable quoted closes of both legs; three
others have positive conservative marks with a zero-bid long. All five made less than
simply covering the original short at the same deadline. The new 30-day earnings rule
is recorded below; the available dated schedules do not clear any of the 73 recent
selections, so these option replays are counterfactual, not admitted trades.

**Charlie and Brent both favor treating strike distance, richness and exhaustion as
separate questions.** A persistent high call wing can keep expanding. The research
question is whether its age and rollover add information beyond its starting level.
These were canonical persona simulations; [their decisions](persona_decisions.md)
and the [protocol frozen before outcomes](research_protocol.md) are recorded separately.

**The most useful research leads are skew age and rollover, mainly for volatility
normalization.** Age 6+ raised the joint decline rate from 23.8% to 28.6%, but spot fell
only 52% of the time and its average change was effectively zero. Two-day wing rollover
gave 27.7%, with similar point estimates in 2024–2025 and 2026; its descriptive advantage
after starting-state matching was about 2.8 percentage points. These are modest associations.

**Positive 30/60-day variance gaps alone did not improve this timing test.** The larger
combined filter also weakened in 2026: 21.4% joint declines from only 28 nonoverlapping
observations, versus 24.5% for that period's high-rank baseline. Both personas advise
against promoting that combination into an entry gate. Their post-result agreement
is to prioritize exact-quote tests of rollover versus continued expansion, retaining
delta, % OTM and normalized distance as separate coordinates.

The retrospective daily-surface study covers **317 stocks with
observed data**, **173,413 eligible stock-days**, and
**29,025 high-front-wing stock-days** from January 2024
through September 3, 2026. The universe is the **September 3 HIRO membership set applied
backwards**. It is not historical HIRO membership or a claim that intraday HIRO existed
throughout. Requested stocks without usable history remain in the coverage ledger.
Collection used **66 requests** under this experiment's separate 80-attempt cap.

The primary reference result is **23.8%** spot-down **and** ATM-IV10-down,
from **11,324 nonoverlapping high-rank observations**, over two holding
sessions beginning at the next-session EOD reference. This is a daily stock/surface
outcome study, **not an exact-option profit backtest**.

![Delta, distance and chronological journey comparisons](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_skew_journey_2026-09-06/delta_distance_and_journey.png)

## Combining delta and distance

Use **delta + % OTM + expiry + distance in ATM expected-move units**. For the recent
contracts, the extra coordinate is log(K/S) / (ATM IV × sqrt(DTE/365)). IV is decimal;
S is a spot approximation because a matched forward is unavailable. Rich tail IV
must not inflate its own distance denominator. These quantities do not establish
strike-touch probability or bounded loss. SMCI's 9.26Δ / 24.78% OTM and JNJ's
9.43Δ / 3.56% OTM remain economically different cases.

The longer-history surface panel uses a **constant 5Δ/10D proxy**. It cannot prove
which exact 2–10Δ and % OTM combination performs best without historical chains,
quotes and fixed contract execution rules. The [73-contract bridge](recent_73_calls_with_journey.csv)
keeps those exact-contract coordinates alongside the proxy's journey; it does not
substitute the proxy percentile for a strike-history z-score.

**We can obtain the contract histories needed to test this.** Use the existing
ThetaData account for historical option NBBO quotes and underlying prices; use
ORATS historical strikes for chain-wide Greeks, bid/ask IV and fitted surfaces where
needed. The follow-up below already fetched 18 missing contract histories and reused
two cached histories for the ten examples. That is enough for their specified price
replay, not for an optimal delta/% OTM test across the whole historical universe.

The full experiment needs these additional steps:

1. Freeze the eligible ticker-date population, the 30-day earnings gate, expiry rules,
   delta bands and % OTM/ATM-distance bins before fetching outcome quotes. Save every
   failed selection. Use historical listings, option deliverables and split adjustments
   so a renamed or adjusted contract is not silently replaced by another one.
2. Obtain each signal-date chain and the chain/underlying snapshot at the actual entry.
   Recheck delta, distance, spread and displayed size then: yesterday's 4Δ call need not
   still be 4Δ tomorrow. Keep the preselected far call and the rule-selected nearer call;
   no picking a better strike after seeing its price path.
3. For strike richness, build a strictly prior-only history of **comparable delta/DTE**
   and a separately reported **comparable forward-moneyness/DTE** coordinate. Interpolate
   only inside supported smiles, requiring at least 60 valid prior observations for the
   initial specification. Compare executable call-bid IV minus matched ATM IV with its
   own prior mean/dispersion, alongside a robust percentile. A newly listed weekly
   contract has no 60-day life of its own; the comparable surface history supplies the
   reference distribution. Sparse deep-wing quotes remain unavailable, not extrapolated.
4. Pull minute quotes for both legs through the fourth/fifth holding session or expiry,
   with quote timestamps, sizes, condition codes, underlying prices and corporate-action
   metadata. Use tick/quote-event history to assess staleness when necessary. Align the
   existing HIRO observations by ET session and use only information before each order.
5. Replay same-day, next-day and second-day purchases under fixed causal rules, with
   identical initial entries and closing deadlines. Compare the nearer-call conversion
   against covering the original short and against buying the spread immediately.
   Include fees, slippage, failed entries, uncompleted trades and short-phase adverse
   exposure. Preserve chronological evaluation periods and resample by date/episode.

ThetaData's [historical quote endpoint](https://docs.thetadata.us/operations/option_history_quote.html)
provides the contract quote history. ORATS offers [historical strikes and individual
contract histories](https://orats.com/docs/historical-data-api), with a separate
[minute-history product](https://orats.com/intraday-data-api). Confirm account entitlements
and a request budget before scaling: ORATS daily full-chain work costs roughly
ceil(tickers/10) × dates in requests; its minute-chain work is ticker × timestamp.
The small replay made no new ORATS requests and did not purchase a data subscription.


## Where the high-call-skew episode stands

| Dimension | Recorded measure | Interpretation |
| --- | --- | --- |
| How extreme now? | Prior-only 252-session percentile and absolute call-wing IV minus ATM | High percentile can still mean a negative wing |
| How long? | Consecutive sessions at rank ≥85; age 1–2, 3–5, 6+ | Age bands are research choices, not Pandar rules |
| How much sustained demand? | Cumulative normalized rank excess above85 | Persistence/intensity, without assuming a reversal |
| How far from its own peak? | Highest wing known so far minus current wing, in vol points | Never uses a later realized peak |
| Still expanding or rolling over? | Two successive rises versus two successive falls in the fixed-tenor wing | Separates continued demand from observed deterioration |
| Is change accelerating? | Daily change in wing/IV slope; change in log-return momentum | Temporal acceleration, distinct from cross-strike curvature and option gamma |

Missing observations interrupt episodes. Unknown starting ages remain in the baseline
and a separate censored-age category, not the known-age comparisons. The 30D/25Δ
ex-earnings call skew and ORATS cross-strike curvature are also retained for context.
Strict episode age resets after even one below-85 observation; it is not the age of an
entire market narrative. The recent-contract bridge additionally shows the number of
high-rank days in the last 20 sessions and distance from that window's peak. Those are
descriptive additions after the primary results, not newly tested admission filters.

**To test persistence cleanly, backfill a session-by-session coverage ledger first.**
It must distinguish a failed download, a listed contract with no valid quote, a stock
that was not yet listed, a delisted/renamed stock and an observation that lies after the
cutoff. Those are different situations; filling them all with yesterday's number would
invent a continuous skew episode.

- For each historical HIRO-universe stock, obtain adjusted closes and the same
  fixed-tenor option surface on every actual exchange session, at least 252 sessions
  before the evaluation period, then through the final required exit. To know an
  episode's start, extend backward until an observed below-threshold session precedes
  it; if that cannot be found, retain unknown age. For recent-persistence tests, require
  complete 20-session windows as well as the complete RV windows.
- Retry only documented provider gaps, then check alternate ORATS/ThetaData coverage
  with reconciled timestamps, adjustments and IV conventions. Investigate the six
  missing-price names **FSR, GPS, MPW, NYCB, PARA and SQ** with dated security identifiers.
  Do not splice an assumed replacement ticker. Pre-IPO and post-delisting history
  cannot be manufactured by buying another feed.
- For a HIRO timing test, obtain the actual archived intraday series for the eligible
  dates and following sessions. Membership in today's HIRO ticker list does not provide
  historical flow. If the older feed cannot be recovered, the daily-surface test can
  continue, but that portion cannot establish HIRO's contribution.
- Freeze the new persistence hypotheses (high days/20, distance below the known
  20-session peak, and any permitted brief threshold interruption), then rebuild
  episodes and compare them with the existing consecutive-age rule on a later period.
  Apply the same earnings and coverage requirements to both groups, and retain the
  excluded/censored ledger. These additions have not yet been tested as entry gates.

The ten-contract follow-up has every expected nearer-call minute row for its admitted
entries through the available cutoff, but some rows contain invalid/non-executable
quotes and are skipped. A complete timestamp grid therefore does not prove continuous
liquidity, tick-level completeness or that an order would fill.


## Realized versus implied volatility

Compute trailing **30 and 60 calendar-day** realized variance from split/dividend-adjusted
stock log returns: 252 × mean squared daily returns, requiring all observations in the
window. Compare it with matched IV30² and IV60². Positive spreads mean implied variance
exceeds recently realized variance; they are not guaranteed carry or forward forecasts.
The study retains modeled earnings premium separately and does not mix raw RV with
ex-earnings IV under a claim of pure diffusion premium. Weekly IV and event exposure
remain relevant even if 30/60-day comparisons look attractive.
For example, MRNA's trailing RV is heavily affected by ORATS's reported adjusted-close
move from $62.96 to $174.38 on August 19. That observation remains in raw RV; its catalyst
is not established here. The August 24 IV30/RV30 comparison of 92.5%/370.3% therefore
does not mean its particular far-OTM call was cheaply offered. A past jump can dominate
trailing RV after the options market has already repriced future volatility.
The weak result for the simple positive-gap rule does not test or reject every
realized-volatility forecasting model or earnings-adjusted comparison.

**New admission rule requested in review: automatically exclude a stock with earnings
on the evaluation date or within the next 30 calendar days, inclusive.** Recheck at
both signal and actual entry. A missing, placeholder, stale or subsequently revised
date is not an earnings-free clearance; keep it out of the tradable sample until the
schedule known at that time is verified. This is the user's added filter, not a
Pandar-attributed rule.

The central sources are present, but the reviewed copies do not cover these August/
September signals with dated schedules:

- [Central earnings history](/Users/dgrissen/Dev/central_trade_data/orats/earnings/earnings_long.parquet):
  latest actual row June 25, 2026 (the adjacent manifest is older and says June 11).
- [Extended event history](/Users/dgrissen/Dev/central_trade_data/orats/earnings/pit_constituents_earnings_long.parquet):
  latest event July 29, 2026. Its name does not itself establish what future dates were
  known on each historical signal date.
- [Daily next-earnings snapshots](/Users/dgrissen/Dev/central_trade_data/orats/stable_rrs_earnings_2026-07-29-v1/normalized/earnings.parquet):
  latest snapshot July 29, 2026. The recent retained screen rows have `nextErn=0000-00-00`
  for all 73 selected calls. Their weeks-to-earnings estimates are retained as estimates,
  not substituted for dated schedules.

The [73-row earnings audit](review_earnings_73.csv) therefore marks every recent selection
**unknown / not admitted under this new policy**. Refresh the central calendar through
at least the last intended entry plus 30 calendar days, retain retrieval/version and
announcement-time metadata, and use archived as-known snapshots for retrospective
admission. A calendar refreshed today alone cannot prove what was known then.

The original surface percentages below are **unfiltered by this newly requested rule**
and remain frozen. The exact-quote examples are explicitly counterfactual while
earnings admission is unresolved. Do not present either as earnings-cleared performance.
Excluding upcoming earnings also does not remove MRNA's earlier reported jump from
trailing RV; that price move still needs a separate corporate-action/cross-source check.


ORATS distinguishes 30/60-calendar-day implied vol, daily adjusted stock prices, and
cross-strike curvature in its [field definitions](https://orats.com/docs/definitions).
The summary endpoint's confidence fraction is converted to percent before applying
the confidence gate. Eight timing, missing-data, unit and column-selection tests pass;
no future price or volatility value enters the signal features.

## Frozen two-session comparisons

EOD features on t authorize a next-session EOD reference on t+1. Outcomes below run
from that reference to t+3. Nonoverlap is chosen separately per rule using the maximum
three-session holding horizon, so rules can enter on different dates. The intervals
resample calendar months of the full cross section and do not make observations
independent trades. The complete CSV also reports all daily signals, 1/3-session
horizons, missing outcomes, component hit rates and signal-to-entry drift.

| Frozen comparison | Valid nonoverlapping observations | Spot down + IV down: rate [month-block 95% interval] | Mean spot return % | Mean ATM IV10 change (pts) |
| --- | --- | --- | --- | --- |
| All eligible daily surfaces | 35415 | 21.7% [19.2, 24.5] | 0.34 | 0.31 |
| High front-wing rank ≥85 | 11324 | 23.8% [22.4, 25.1] | 0.24 | -0.19 |
| High rank + wing above ATM | 11322 | 23.8% [22.4, 25.1] | 0.24 | -0.19 |
| High rank, age 1–2 | 9658 | 22.8% [21.6, 24.0] | 0.24 | 0.02 |
| High rank, age 3–5 | 2800 | 27.2% [25.6, 29.2] | 0.21 | -0.68 |
| High rank, age 6+ | 1575 | 28.6% [25.3, 32.3] | -0.01 | -1.31 |
| High rank, age left-censored | 2 | 0.0% [nan, nan] | 13.07 | 19.41 |
| High rank, expanding wing | 6846 | 23.3% [21.6, 25.0] | 0.22 | -0.12 |
| High rank, rolling-over wing | 1486 | 27.7% [25.1, 30.4] | 0.01 | -1.53 |
| Age ≥3 + rollover | 1485 | 27.7% [25.1, 30.4] | 0.01 | -1.55 |
| High rank, both RV/IV windows available | 11323 | 23.8% [22.4, 25.1] | 0.24 | -0.19 |
| High rank + positive 30/60 variance premia | 5728 | 23.0% [21.4, 24.8] | 0.26 | -0.29 |
| High rank + price/IV exhaustion | 4115 | 27.9% [25.7, 30.0] | 0.02 | -1.05 |
| Age ≥3 + rollover + premia + exhaustion | 126 | 31.0% [22.7, 39.1] | -0.65 | -2.52 |
| Exhaustion + accelerating IV decline | 3438 | 28.8% [26.8, 30.8] | 0.02 | -1.45 |
| High rank + modeled front event premium ≤2 pts | 9809 | 23.3% [22.0, 24.6] | 0.18 | 0.46 |
| First observation below high-rank threshold | 9252 | 23.7% [22.2, 25.4] | 0.16 | -0.21 |


Price/IV exhaustion means preceding three-session strength, slowing daily stock returns,
and falling IV10. Accelerating-IV sensitivity additionally requires IV's daily slope to
become more negative. The combined hypothesis requires known age ≥3, wing rollover,
both positive variance premia and that exhaustion condition. **No weights or thresholds
were optimized on observed winners.**

## Chronological and starting-state checks

| Comparison | 2024–2025 joint rate | 2026 joint rate | Starting-state comparison: all daily signals |
| --- | --- | --- | --- |
| High front-wing rank ≥85 | 23.5% (n=8,143) | 24.5% (n=3,181) | Reference |
| High rank, age 1–2 | 22.3% (n=6,810) | 23.8% (n=2,848) | -2.9 points (supported n=16,561) |
| High rank, age 3–5 | 27.4% (n=2,051) | 26.7% (n=749) | +3.0 points (supported n=5,793) |
| High rank, age 6+ | 28.0% (n=1,278) | 31.0% (n=297) | +1.6 points (supported n=5,320) |
| High rank, expanding wing | 23.2% (n=4,969) | 23.5% (n=1,877) | -1.6 points (supported n=9,702) |
| High rank, rolling-over wing | 27.4% (n=1,150) | 28.6% (n=336) | +2.8 points (supported n=2,155) |
| High rank + price/IV exhaustion | 29.2% (n=2,902) | 24.7% (n=1,213) | +3.2 points (supported n=5,391) |
| Age ≥3 + rollover + premia + exhaustion | 33.7% (n=98) | 21.4% (n=28) | +6.2 points (supported n=133) |


The final column compares each group with other high-rank daily observations in the
same fixed calendar-quarter, starting-rank, absolute-wing, ATM-IV and modeled-event
premium cell, requiring at least five controls. It uses common-support observations
and is a descriptive percentage-point difference, not a causal or tradable edge.
These are all-signal comparisons; their sample sizes differ from the nonoverlap columns.
Current-universe selection, residual confounding and multiple comparisons remain.
The later 2026 slice is not a pristine untouched holdout.

## What the recent calls looked like along that journey

These are selected examples fixed before reading their outcome rows, including both
HIRO-covered and uncovered cases. The original stock/IV column uses a next-session EOD
reference. The two added columns use **exact option quotes with a next-session 10:01
clock entry**, not that EOD reference or a HIRO trigger. The journey belongs to the fixed
5Δ/10D surface proxy; delta and distance are signal-date coordinates, not entry Greeks.

**Why four rows say “skipped sale”:** this comparison checked one possible sale time,
10:01 ET on the next trading day, and required at least $0.20 per share ($20 for one
standard contract). At that minute, NVDA and SMCI offered $15 per contract, BE offered
$5, and JNJ offered $4. The replay therefore left those trades unopened. The clock time
and minimum premium are project assumptions used to make this one comparison consistent;
they are not Pandar's requirements. Those rows do not tell us whether selling on the
signal day, waiting until later, or following HIRO could have produced a good trade.

For the added test, sell the preselected far call at the next-session 10:01 bid >=$0.20;
buy the fixed nearer call at the first subsequent valid minute ask that leaves $0.10
gross credit. Close at 15:50 on session 4 or 5, counting entry as session 1, or expiry
if sooner. Dollar results include $2.60 round-trip fees per one-contract spread. Buying
the nearer call completes the spread; it does not close it. This project conversion
and the fixed bid/credit/time rules are not universal Pandar requirements.

| Signal EOD | Call delta / % OTM / log-distance | Front 5Δ/10D wing journey | IV/RV %: 30d; 60d | Observed post-reference 2-session spot / IV10 | Sell first / buy cheaper, closed within 4–5 sessions? | Why / why not (ET; per contract) |
| --- | --- | --- | --- | --- | --- | --- |
| COIN 08-20 | 5.02Δ / 28.24% / 2.18 ATM moves | age 2; high 2/20 days; expanding; 0.00 pts below episode peak | 70.3/72.4; 70.2/68.7 | +0.36% / -2.71 pts | Yes, quoted closes: $+11.40 / $+6.40 net (D4/D5) | Sold 220C $2.02; bought 215C $1.89 on 08-21 10:41. |
| COIN 08-21 | 4.40Δ / 26.97% / 2.23 ATM moves | age 3; high 3/20 days; mixed; 0.36 pts below episode peak | 69.7/74.8; 70.8/71.3 | +1.28% / -6.01 pts | Completed; short covered, long marked at zero: $+9.40 / $+10.40 net (D4/D5) | Sold 235C $0.21; bought 230C $0.07 on 08-25 09:31. No long-call closing bid; positive conservative mark is not a full close. |
| STX 08-24 | 4.71Δ / 16.19% / 1.68 ATM moves | age 1; high 2/20 days; expanding; 0.00 pts below episode peak | 69.0/83.4; 69.3/93.4 | +3.11% / -3.68 pts | Completed; short covered, long marked at zero: $+2.40 / $+2.40 net (D4/D5) | Sold 925C $2.10; bought 920C $2.00 on 08-25 12:06. No long-call closing bid; positive conservative mark is not a full close. Expiry caps exit at 08-28. |
| NVDA 08-26 | 3.72Δ / 15.70% / 1.73 ATM moves | age 3; high 4/20 days; expanding; 0.00 pts below episode peak | 41.3/34.0; 39.0/36.4 | -3.16% / -6.55 pts | Skipped sale: $0.15 bid at 08-27 10:01 | This replay required at least $0.20 per share ($20 per contract); the bid offered $15 per contract. Only that entry time was checked. Other entry times remain untested here. |
| BE 08-28 | 3.64Δ / 29.56% / 2.12 ATM moves | age 2; high 2/20 days; mixed; 0.71 pts below episode peak | 80.3/105.2; 83.7/116.1 | +5.32% / +5.38 pts | Skipped sale: $0.05 bid at 08-31 10:01 | This replay required at least $0.20 per share ($20 per contract); the bid offered $5 per contract. Only that entry time was checked. Other entry times remain untested here. |
| MSTR 08-20 | 4.31Δ / 33.86% / 2.22 ATM moves | age 2; high 2/20 days; expanding; 0.00 pts below episode peak | 78.3/73.8; 78.8/80.8 | +6.36% / -3.77 pts | Yes, quoted closes: $+10.40 / $+36.40 net (D4/D5) | Sold 150C $0.75; bought 145C $0.64 on 08-21 14:50. |
| SMCI 08-13 | 9.26Δ / 24.78% / 1.70 ATM moves | age 1; high 7/20 days; mixed; 0.00 pts below episode peak | 81.0/115.0; 80.4/103.2 | -6.10% / +3.32 pts | Skipped sale: $0.15 bid at 08-14 10:01 | This replay required at least $0.20 per share ($20 per contract); the bid offered $15 per contract. Only that entry time was checked. Other entry times remain untested here. |
| JNJ 08-24 | 9.43Δ / 3.56% / 1.27 ATM moves | age 3; high 9/20 days; expanding; 0.00 pts below episode peak | 21.8/21.7; 24.9/26.4 | -2.70% / -0.69 pts | Skipped sale: $0.04 bid at 08-25 10:01 | This replay required at least $0.20 per share ($20 per contract); the bid offered $4 per contract. Only that entry time was checked. Other entry times remain untested here. |
| MRNA 08-24 | 3.15Δ / 40.24% / 2.23 ATM moves | age 4; high 4/20 days; rolling over; 9.44 pts below episode peak | 92.5/370.3; 88.7/271.9 | -10.11% / -32.65 pts | Completed; short covered, long marked at zero: $+30.40 / $+30.40 net (D4/D5) | Sold 195C $0.63; bought 192.5C $0.29 on 08-26 09:33. No long-call closing bid; positive conservative mark is not a full close. Expiry caps exit at 08-28. |
| TSLA 09-02 | 4.14Δ / 14.77% / 2.26 ATM moves | age 1; high 6/20 days; expanding; 0.00 pts below episode peak | 41.7/40.7; 43.0/56.2 | Unavailable | Second leg completed; closing outcome unavailable | Sold $0.91; bought nearer at $0.40 on 09-04 09:31. Exit 09-09 is beyond 09-04 cutoff. |


**Read “within 4–5 days” here as trading sessions, with the sale session counted as
day 1.** The CSV also records elapsed calendar days and whether expiry shortened the
window. Thus MSTR's day-4/day-5 exits are August 26/27 after an August 21 sale: five/six
elapsed calendar days. This does not answer a different four/five-calendar-day rule.
TSLA's September 3 entry would reach session 4 on September 9, its expiry; September 7
is a holiday. Both requested horizons are therefore outside the September 4 data cutoff.

The replay attempted a sale at just **10:01 ET on the next trading day** and required
at least **$0.20 per share, or $20 per standard contract**. NVDA, BE, SMCI and JNJ offered
$0.15, $0.05, $0.15 and $0.04 respectively at that minute, so no simulated position was
opened for those four examples. The timing and $0.20 cutoff are project assumptions
for this comparison, not Pandar requirements. A sale on the signal day or at another
minute could have a different result; this comparison did not test those alternatives.
COIN (August 20), STX and MSTR completed their second leg on the entry day; COIN
(August 21) and MRNA did so on the next session. TSLA also completed on the next
session but lacks a mature closing outcome. No entry or second-leg time was chosen
after comparing profitable alternatives.

**Buying the nearer call cost more than it added at the common exit in all five mature
completions.** The comparison holds the original short sale and exit deadline fixed:

| Signal | Conversion net, D4 / D5 | Simply cover the short, D4 / D5 |
| --- | --- | --- |
| COIN 08-20 | +$11.40 / +$6.40 | +$194.70 / +$188.70 |
| COIN 08-21 | +$9.40 / +$10.40, zero-bid-long marks | +$17.70 / +$18.70 |
| STX 08-24 | +$2.40 / +$2.40, zero-bid-long marks | +$203.70 / +$203.70 |
| MSTR 08-20 | +$10.40 / +$36.40 | +$65.70 / +$42.70 |
| MRNA 08-24 | +$30.40 / +$30.40, zero-bid-long marks | +$60.70 / +$60.70 |

Covering the short at the same late deadline leaves more upside exposure during the
intervening period than completing the spread earlier. The P&L advantage is not a
risk-adjusted dominance claim or a recommendation to remain short without protection.

COIN 08-21, STX and MRNA had no executable long-call bid at the closing reference. The
calculation covers their short at the ask, values the remaining long at zero and
reserves all four fees. It is a conservative marked result, **not proof that both legs
were sold/bought to close**. An extra one cent of adverse slippage on each action turns
STX's +$2.40 mark into **−$1.60**. The two fully quoted closing examples remain positive
under that sensitivity. A one-minute NBBO snapshot is still a hypothetical fill, not
an executed order; it does not capture every intraminute price or quote-age risk.

The new replay uses **18 ThetaData contract-history requests plus two existing cached
histories**, with no missing nearer-call minute rows in the admitted windows. Invalid
quotes (including empty opening snapshots) were not executable and could not trigger
a purchase. The [20-row ledger](review_45_session_replay.csv) keeps both horizons for
every example, including rejected entries and censored deadlines. Each horizon is a
separate counterfactual; the same position cannot be closed twice. These selected
examples do not establish a win rate, and none is earnings-cleared under the new rule.


The full CSV includes all 73 selections, both original delta/OTM coordinates and current
surface-stage inputs, plus the previously verified HIRO capture status. It retains
unavailable outcomes. A fading stock price with rising IV is a separate adverse-vol
regime; it must not be mistaken for a call-wing crush or successful nearer-call purchase.
The refreshed histories reproduce 70 of the 73 original front-wing ranks exactly;
the other three differ by 0.397 percentile points, equivalent to one prior observation
out of 252, with no change to the 85 threshold classification. The original ranks remain
visible alongside the new computed ranks in the [reconciliation](recent_rank_reconciliation.csv).

## Artifacts and limits

- [Review protocol](review_followup_protocol.md), [exact four/five-session replay](review_45_session_replay.csv),
  [quote provenance](review_quote_manifest.json), [earnings audit](review_earnings_73.csv),
  [earnings source dates/hashes](review_earnings_sources.json), and [Feynman-style review](feynman_review.md).
- [Protocol](research_protocol.md), [persona decisions](persona_decisions.md),
  [full fixed-comparison results](ablation_results.csv), and
  [starting-state comparisons](starting_state_comparisons.csv).
- [All daily features/outcomes](daily_features_and_outcomes.parquet),
  [high-rank and first-exit ledger](high_rank_signal_ledger.csv),
  [73 exact-call coordinate/journey rows](recent_73_calls_with_journey.csv), and
  [delta versus % OTM counts](delta_otm_counts.csv).
- [Requested-stock coverage](coverage.csv), [source hashes](data_sources.csv),
  [frozen membership](hiro_universe.csv), and [request ledger](api_manifest.json).

This tests some of the user's proposed predictors across historical HIRO ticker names.
It does not establish an optimal delta/OTM band, an intraday HIRO edge or optimal
second-leg timing. Exact-price examples now exist for the ten selected rows, under the
specific clock rule and unresolved earnings admission above; they do not validate the
strategy across the historical universe. The earlier HIRO-based MSTR replay remains
separate. The fixed reference/entry times, selection bias and small sample prevent
interpreting these examples as a portfolio return or a fitted profitable trading rule.

## Four-paragraph Feynman-style summary

Start with COIN’s August 20 signal. At 10:01 the next session, selling one 220 call
brought in $202. At 10:41, buying the closer 215 call cost $189. That long call limited
the damage from a later rally and created possible upside between the two strikes. But
protection costs money: it consumed nearly all the short-call premium. The $13 left
after the purchase was a premium balance before fees; both options were still open.
At 15:50 ET on August 26, selling the long at $0.07 added $7 and covering the short at
$0.06 cost $6. After four $0.65 transaction fees, profit was $11.40. Keeping only the
original short until that same exit produced $194.70 after two fees.

The larger study gives a clue about volatility, not a trade result. Over two holding
sessions, the stock and ten-day at-the-money implied volatility both fell in 23.8% of
high-skew observations. When that elevated skew had persisted for at least six sessions,
the rate rose to 28.6%, while the average stock return was effectively flat. The useful
signal here is modest volatility cooling, not dependable stock weakness. Those
percentages count joint stock-and-volatility outcomes. They are not option-profit win
rates, because profit depends on the exact contracts, entry and exit quotes, timing,
spreads, and fees.

A “skipped sale” means the replay checked one chosen moment—10:01 on the next trading
session—and required a bid of at least $0.20 per share, or $20 for one standard contract.
These are project replay choices, not Pandar requirements. NVDA and SMCI offered $0.15,
BE $0.05, and JNJ $0.04, so this replay opened no trade in them. That tells us nothing
conclusive about another time or whether the underlying Pandar setup worked. Among the
five mature constructed spreads, two had quoted exits for both legs. Three had positive
conservative marks, but their long calls had zero bids and therefore were not executable
closing sales. TSLA’s required exit had not yet occurred by the data cutoff.

The requested earnings rule excludes a stock with earnings on the signal date or within
the next 30 calendar days, checked again at the actual entry. Available dated schedules
were stale, so these cases remain unknown under that rule; they are not known to have
forthcoming earnings. To learn when to sell, we need to compare fixed same-day,
next-session, and later entries using archived HIRO signals, exact option quotes, the
earnings calendar known at the time, and identical exits. That focused comparison would
show whether HIRO or waiting improves entry. Until then, the evidence supports modest
volatility cooling and a few instructive cash-flow examples, not a validated trading edge.
