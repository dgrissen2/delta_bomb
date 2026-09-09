# Pandar-style inventory: daily eligibility, strike richness and leg timing

**New hypothesis study:** [June eligibility, exact leg timing and profit comparisons](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/pandar_trade_results.md) now test one frozen higher-delta variant with refreshed actual earnings, prior strike-richness histories and quote-event age checks. [Charlie/Quant decision memo](/Users/dgrissen/Dev/delta_bomb/hypothesis_tracking/memo-pndr_pandar_call_research.md).

<!-- BEGIN ELIGIBILITY AUDIT -->
## What comes from Pandar, and what comes from our scanner

**The 2–6-delta band did not come from Pandar.** The exact instruction to select the
2–6Δ call nearest 4Δ appears in the project's
[Charlie/P1 analysis](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/replay/hiro_daily_2026-08-11_to_2026-08-27/three_call_methods_charlie_analysis.md:137).
That is a **Charlie McElligott-persona research synthesis**, not a rule documented by
Pandar or a published McElligott recommendation. The
[parameter-attribution audit](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/four_method_parameter_attribution_2026-09-03.md:23)
and [strategy memory](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/strategy_names.md:29)
explicitly classify the delta band, DTE window and quote filters as project extensions.

Pandar's documented call example selected **unusually overpriced far-OTM front-weekly
calls**, compared expirations, anticipated a crush, and sized for a move to the strike.
On January 31, 2025 he identified NVDA February 7 190C and higher; he did not specify
a delta band. In that episode he explicitly kept the calls naked. The systematic
nearer-call conversion is also an extension of his process, rather than his fully
specified call recipe. [Original exchange](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/sources/discord_transcript_clean.txt:287).

**Consequently, “eligible” below means passed the recorded project implementation of
the two Pandar-style families. It does not mean Pandar endorsed that contract, or that
contracts outside our search envelope were unsuitable.** In particular, an 8.1Δ call
is not disqualified by a documented Pandar rule. The original scanner rows and replay
are preserved, with the early put dates added separately; this does not establish
2–6Δ as the correct search boundary for future research.

## Daily eligibility: which names and which trade

Under the original project surface gates, there are **1,788 ticker/date
surface candidates: 24 call-grab rows and
1,764 put-inventory rows**. After auditing alternative call contracts, exact-chain
checks retain **151 rows: 9 calls across COIN, LRCX and MSTR,
and 142 puts**. The original one-contract selector retained only MSTR;
the correction below recovers three additional call ticker/dates without loosening
the original numerical gates. The separately labelled wider search below finds
**73 quote-qualified call stock-days across 33 names at 2–10Δ**; the original table
is no longer the complete call research universe.
These include repeated daily observations of the same contracts. A surface candidate,
a quote-qualified contract, a HIRO-triggered entry and a profitable modeled exit are
four different stages.

**Pandar-approved core** in the headers refers to the call-tail sale/crush mechanism
and put-tail inventory program. Candidate selection and exact-chain pass/fail use our
project rules; Pandar did not approve individual ticker/date entries or the systematic
call conversion.

| Signal date (EOD) | Call surface candidates (original project screen) | Call-sale core: exact 2–6Δ passes (Pandar-approved mechanism) | Put surface count (project screen) | Put inventory: exact passes (Pandar-approved core) |
| --- | --- | --- | --- | --- |
| 2026-08-11 | FANG | None | 80 | APA, CCL, CELH, DAL, GOOG, LYFT, NVDA, PLTR, UAL |
| 2026-08-12 | FDX, LRCX | None | 99 | CCJ, CELH, DAL, GOOGL, NVDA, PLTR |
| 2026-08-13 | LRCX, SMCI | None | 96 | AMZN, ASTS, CRWV, DAL, GOOGL, NVDA, PLTR, TGT, TSLA |
| 2026-08-14 | None | None | 126 | AMZN, BA, CRCL, CRWV, GM, GOOG, GOOGL, NVDA, PLTR, QBTS, SBUX, TSLA |
| 2026-08-17 | GS, LRCX | LRCX | 104 | AMZN, CRWV, GOOG, GOOGL, HOOD, NVDA, PLTR, SEDG |
| 2026-08-18 | None | None | 97 | AMZN, GOOG, GOOGL, HIMS, NVDA, PLTR |
| 2026-08-19 | COIN, MSTR | COIN, MSTR | 97 | AMZN, CCJ, GOOG, GOOGL, HIMS, NVDA, TGT |
| 2026-08-20 | COIN, MSTR, NEM | COIN, MSTR | 87 | CRWV, GOOG, GOOGL, NVDA, SEDG |
| 2026-08-21 | MRK, MSTR, NEM | MSTR | 85 | AMZN, CRWV, GOOG, GOOGL, NVDA |
| 2026-08-24 | CPNG, JNJ, MSTR | MSTR | 89 | CCJ, CRWV, GOOG, GOOGL, NVDA, PLTR, TGT |
| 2026-08-25 | ABBV, CPNG | None | 92 | BE, CRWV, GOOG, GOOGL, IREN, NVDA, SCHW, SOFI |
| 2026-08-26 | None | None | 102 | AMZN, BE, BMNR, IREN, MRNA, NVDA, PLTR |
| 2026-08-27 | GAP | None | 92 | AMZN, CRWV, GOOG, GOOGL, NBIS, NVDA, PLTR |
| 2026-08-28 | CPNG | None | 107 | BMNR, CRWV, CVNA, GOOGL, HOOD, MRVL, NVDA |
| 2026-08-31 | MSTR | MSTR | 110 | AMZN, BE, BMNR, CRWV, GOOG, GOOGL, HOOD, MRVL, NVDA, OKLO, PLTR, SHOP |
| 2026-09-01 | None | None | 96 | AMZN, BMNR, CVNA, GOOGL, HOOD, MRVL |
| 2026-09-02 | None | None | 99 | AMZN, ANET, BE, BMNR, CRWV, GOOG, GOOGL, IREN, MRVL, NVDA, SOFI |
| 2026-09-03 | MSTR | MSTR | 106 | AMZN, BE, BMNR, CRWV, GOOG, MRVL, MSFT, NBIS, NVDA, RTX |
| 2026-09-04 | Unavailable | Unavailable | Unavailable | Unavailable |


### Why the earlier put days were missing—and the correction

**This was an inherited research-scope omission, not a lack of eligible puts.** The
master combined an August 11–27 call scan with a later four-method scan whose put start
date was August 24. That later run described the put coverage as an extra week added
to its August 28–September 2 call window. The master retained those date boundaries
instead of scanning both Pandar-style families over the full window. I then carried
the omission into this report rather than closing it. [Earlier scan's date scope](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/replay/hiro_daily_four_methods_2026-08-24_to_2026-09-02/README.md:24).

The **nine omitted sessions, August 11–21, have now been scanned** with the same
recorded put rules. They added **871 surface-qualified ticker/date rows and
67 exact-chain confirmations**. The daily table and all-candidate appendix
now include them; there are no remaining “Not scanned” put rows in that interval.
Put-skew ranks reconstructed from prior-only historical data reproduced all **1,156
overlapping ticker/date ranks** from the existing scan. Every one of the new candidates
received an exact-chain check; failures remain in the ledger.

This addition expands **eligibility coverage**. The profit/timing study below remains
the original frozen **81-qualification cohort**. The new early put confirmations have
**not yet received the same minute-quote/HIRO leg-timing replay**; no profit, loss or
HIRO availability is inferred for them from the original results.
[Early candidate and chain audit](early_put_backfill/all_chain_checks.csv),
[new exact confirmations](early_put_backfill/exact_confirmations.csv).

Every surface-qualified ticker, its daily IV/skew ranks and its exact-chain rejection
reason appears in the [complete daily tables](pandar_all_daily_surface_candidates.md).
The [1,788-row complete-window CSV](pandar_eligibility_complete_window.csv) also includes raw surface
values, trend/liquidity/earnings fields and available contract details. The
[151-row exact-leg CSV](pandar_exact_legs_complete_window.csv) includes both legs' Greeks and
moneyness. The original September 4 qualification outage is **missing data**, not a
zero-opportunity result. The frozen [917-row inventory audit](pandar_eligibility_enriched.csv)
and [81-row exact-leg audit](pandar_exact_legs_enriched.csv) remain available to reproduce
the earlier timing study.

### What each rank means

All qualification values are **signal-date EOD observations**, usable prospectively
from the following session. Ranks are on a 0–100 scale. The historical skew ranks use
the prior 252 sessions, require at least 126 valid observations, and count prior values
strictly below the current value. They exclude the current observation.

| Metric | Definition in this inventory | What it tells us |
| --- | --- | --- |
| IV Rank (`ivRank1y`) | ORATS one-year IV range rank: current IV's location between the year's low and high | Broad IV level; **not** a historical percentile and **not** the sold strike's IV rank |
| Local RR rank (`rr25_pct252`) | Historical percentile of earnings-adjusted 30D **25Δ put IV − 25Δ call IV** | A low local rank means calls rich relative to puts; this is the opposite sign from official Compass RR |
| Call-skew rank | Percentile of earnings-adjusted 30D 25Δ call IV − ATM IV | Separates call-wing richness from broad IV |
| Put-skew rank | Percentile of earnings-adjusted 30D 25Δ put IV − ATM IV | Low values identify relatively cheap downside skew |
| Front call-wing rank | Percentile of 10D 5Δ call IV − 10D ATM IV | A fixed 5Δ/10D surface proxy; **not** the exact selected strike |
| Call-kink rank | Percentile of 10D 5Δ call IV − 30D 5Δ call IV | Front-tenor richness relative to the farther tenor |
| Opposite put-wing rank | Percentile of 10D 5Δ put IV − 10D ATM IV | Helps distinguish one-sided call demand from both tails expanding |
| Selected-contract wing | Selected call midpoint IV − nearest-to-50Δ same-expiry call midpoint IV | Original contract-level screen check, in volatility points |

Raw ORATS strike IV values are decimal fractions; displayed IV percentages and excesses
multiply them by 100. ORATS supplies the strike bid-IV/mid-IV and fixed-delta/tenor
surface fields used here. [ORATS field definitions](https://orats.com/docs/definitions).
Do not relabel the local RR numbers as official Compass ranks or mechanically subtract
them from 100 without accounting for ties and different histories.

### The numerical gates that produced this inventory

**These numerical gates are project rules.** They describe the existing population;
their inclusion here is not evidence that Pandar prescribed them.

| Stage | Sell-first call grab | Buy-first put-tail inventory |
| --- | --- | --- |
| Surface | IVR **30–70**; local RR rank **≤10**; front call-wing rank **≥85**; kink rank **≥70**; opposite put-wing rank **<70** | IVR **≤35**; local RR rank **≤50**; put-skew rank **≤25** |
| Trend / event | Five-day return **>0**; within **5%** of the 20-day high; no near-front earnings flag; no earnings inside selected expiry | No equivalent trend gate; earnings metadata retained, not an automatic veto |
| Shared liquidity | Average option volume **≥2,000/day**, total OI **≥25,000**, stock dollar volume **≥$20m**, core confidence **≥50**, within the scanner's stock universe | Same shared gates |
| Contract search | **2–6Δ nearest 4Δ**, nearest expiry **5–12 vendor DTE**, fallback through **19**; adjacent lower-strike call as prospective long | First two standard monthly expiries in **14–75 vendor DTE**; long put **25–45% OTM**; width **$2.50–$7.50**, prefer **$5** |
| Exact quote gate | Far-call bid **≥$0.20**; spread **≤$0.10**; OI **≥25**; nearer-call ask positive; selected call IV **≥2 points above ATM** | Complete spread debit **$0.00–$0.10** at long ask minus short bid; positive leg bids/asks; combined quoted widths **≤$0.10**; each OI **≥25** |

Vendor DTE is retained as recorded; it can differ from simple expiration-date minus
trade-date arithmetic. It is also the DTE coordinate used in the richness comparison.
Pandar's direct put practice supplies cheap narrow tail inventory, generally roughly
$5 wide and under a dime across the next two monthlies. **Fixed 25–45% OTM and mandatory
immediate completion are ours**; his own long-first inventory could be legged over time.

## Why the original screen showed only MSTR—and the calls it missed

**The MSTR-only result was too narrow. The scanner selected one call nearest 4 delta
before checking its bid, width and other quote gates. If that one call failed, it
rejected the ticker without checking whether another strike or expiry passed.**

A September 6 audit tested every available alternative within the same 2–6Δ and
5–19-vendor-DTE envelope, keeping the original surface gates, bid ≥$0.20, quoted
width ≤$0.10, OI ≥25, nearer-call ask and ≥2-point selected-wing checks. It recovered
**three previously missed ticker/dates**, bringing the original 24 surface candidates
to **nine exact passes across COIN, LRCX and MSTR**.

| Signal date | Ticker | Original selected call / failure | Alternative that passes unchanged gates | Δ ×100 | % OTM | Bid / ask | OI | Mid IV − ATM (points) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aug 17 | LRCX | Aug 21 395C, $0.16/$1.21: insufficient bid and excessive width | **Aug 21 400C** | **3.13** | **16.73%** | **$0.31/$0.37** | 4,888 | 8.33 |
| Aug 19 | COIN | Aug 28 205C, $0.12/$0.67: insufficient bid and excessive width | **Aug 28 200C** | **5.01** | **25.77%** | **$0.43/$0.50** | 429 | 18.17 |
| Aug 20 | COIN | Aug 28 225C, $0.29/$0.42: thirteen-cent width | **Aug 28 220C** | **5.02** | **28.24%** | **$0.41/$0.50** | 480 | 23.13 |

All **22 original selected contracts** with identified strikes reproduced their frozen
bid, ask, delta and underlying in the new historical-chain pull. The other two rows
were NEM's missing-contract results. This establishes a selection omission rather than
a changed quote snapshot. The LRCX 395C/400C quotes are unusually inconsistent across
strikes, which also makes quote-quality review material; an EOD bid/ask snapshot is
not an actual fill.

The daily table and complete-window CSV now use these recovered contracts. The frozen
917-row source audit and original P&L cohort retain their old selections. **The three
recovered call pairs have not yet received the minute-quote/HIRO replay**, so this
finds eligible call sales, not three proven profitable trades.
[Recovered contracts and original failures](call_exclusion_audit/recovered_original_rule_contracts.csv).

### What the other filters excluded

Even this correction is restricted to our original 24 surface candidates. Before the
project's IVR 30–70, near-high and near-earnings gates, the same one-sided call-grab
surface appeared on **56 ticker/dates across 33 stocks**. The broader audit retained
those exclusions instead of silently calling them non-Pandar trades.

| Audit comparison | Ticker/dates with a passing contract | Distinct stocks | Interpretation |
| --- | --- | --- | --- |
| Original surface + original one-contract selection | 6 | MSTR | Frozen result; incomplete search |
| Original surface + every contract under unchanged contract gates | **9** | **COIN, LRCX, MSTR** | Corrects selection without relaxing a threshold |
| Original surface; remove only the 2–6Δ band | 12 | COIN, GAP, JNJ, LRCX, MSTR, SMCI | Sensitivity, not additional Pandar approvals; some calls are much nearer ATM |
| Original surface; remove only the ten-cent absolute quote-width ceiling | 12 | COIN, GS, LRCX, MSTR | Sensitivity that admits wider execution costs |
| All 56 grab-surface rows; original contract gates | 11 | AVGO, COIN, LRCX, MRNA, MSTR | Two further dates were excluded by the project surface overlays |

Examples that show why the project boundaries matter:

- **SMCI, Aug 13:** Aug 21 49C quoted **$0.20/$0.26**, **9.26Δ**, **24.78% OTM**.
  It passes the original surface and the other tested contract gates. Only the 2–6Δ
  contract band excludes it. That band is not a documented Pandar rule.
- **MRNA, Aug 24:** Aug 28 195C quoted **$0.26/$0.36**, **3.15Δ**, **40.24% OTM**.
  It passes the original contract gates but was **17.54% below its 20-day high**,
  outside the project's within-5%-of-high condition.
- **AVGO, Sep 2:** Sep 11 455C quoted **$0.72/$0.81**, **3.88Δ**, **23.67% OTM**.
  It passes the original contract gates; IVR **22.03** and a **13.56% drawdown**
  excluded it before the original contract selection.

These are historical qualification alternatives, not executed or profitable trades.
The audit uses signal-day weeks-to-earnings estimates for expiry-event checks. Exact
strike-history z-scores have been calculated only for the six original MSTR calls;
the alternatives above have current strike-versus-ATM checks and the existing surface
ranks, not matched-history proof of extreme richness. The 56-row audit still inherits
the front-wing, kink, RR and positive-return proxy rules; it is **not an exhaustive
search for everything Pandar might have considered**.
[All surface exclusions](call_exclusion_audit/surface_exclusions.csv),
[every alternative contract check](call_exclusion_audit/every_contract_check.csv), and
[ticker/date filter comparisons](call_exclusion_audit/ticker_day_exclusion_summary.csv).

## Wider call search and a controlled delta-band comparison

**The delta band was only part of the omission.** Keeping 2–6Δ but removing the
additional IVR, RR, kink, opposite-wing, trend and near-front-event surface vetoes
finds **51 quote-qualified stock-days across 23 names**. Widening that broader search
to **2–10Δ finds 73 stock-days across 33 names**.
The comparison keeps the contract quote, OI, selected midpoint-wing and selected-expiry
earnings checks fixed. It does not select on subsequent profit.

Discovery checked **413 stock-days across 134 stocks** with front 5Δ/10D call-wing
rank ≥85, within the existing liquid-stock universe. This remaining rank threshold
is also a project proxy. It is a broader search, not an exhaustive inventory of
everything Pandar might trade. September 4 remains unavailable. **TFC August 19** has
no OTM call with a nearer strike in the returned 1–30-DTE slice; that coverage
limitation is retained in the ledger rather than treated as a complete chain rejection.

| Delta band (×100) | Original surface: dates / names | Grab surface: dates / names | Rich-front discovery: dates / names | Rich-front selections: 5–12 / 13–19 DTE |
| --- | --- | --- | --- | --- |
| 2–6 | 9 / 3 | 11 / 5 | 51 / 23 | 45 / 6 |
| 2–8 | 9 / 3 | 12 / 5 | 62 / 29 | 56 / 6 |
| 2–10 | 11 / 5 | 15 / 7 | 73 / 33 | 64 / 9 |
| 1–10 | 11 / 5 | 15 / 7 | 77 / 34 | 68 / 9 |
| 2–15 | 11 / 5 | 18 / 9 | 83 / 38 | 74 / 9 |


Counts are ticker/dates with at least one qualifying contract, followed by distinct
stock symbols; they are **not independent trades**. One contract is shown per date:
earliest passing expiry, then closest to 4Δ. The all-contract ledger retains the other
choices. Widening the band can change the selected expiry/strike even on an existing
passing date. The 13–19-DTE fallback is shown separately from the front 5–12-DTE bucket.

For the **original 24-row surface**, fixing selection recovers three dates: **6 → 9**.
Widening only its delta band to 2–10 adds **SMCI Aug 13 and JNJ Aug 24**: **9 → 11**.
The broader surface contributes the other **62** dates at 2–10Δ: **11 → 73**.
Thus neither “only MSTR qualified” nor “the delta band caused all the omissions” is accurate.

**Use 2–10Δ as the next research search envelope**, with 2–6 as its benchmark,
while treating both as project parameters. Retain % OTM and approximate ATM
expected-move units separately: SMCI's 9.26Δ call was 24.78% OTM; JNJ's 9.43Δ call
was only 3.56% OTM. The latter needs a separate far-tail judgment. No outcome-based
optimal delta band has been established. Selection nearest 4Δ is a reproducibility
convention, not evidence that it is the richest strike; subsequent richness review
should compare all the passing strikes.

The shared scanner now checks every candidate's quote before selection, tries later
expiries when needed, and accepts an explicit **--call-delta-max 0.10** override.
Its original default remains reproducible. **22 scanner tests pass**, and its selections
agree with the independent audit for **826 comparisons across all 413 stock-days**.

### Are the actual calls rich enough to sell?

The midpoint wing check alone is insufficient. Among the 73 selected 2–10Δ calls:

- **65** have bid IV at least two points above the same-expiry nearest-50Δ call's midpoint IV.
- **71** have a supported 20–30-DTE matched-delta comparison; **37** have front bid IV
  above that deferred midpoint IV.
- **33 selected calls** pass both diagnostics. Their deferred expiries also fall
  before the signal-day earnings estimate. This is a review subset, not a new
  backtested admission rule or proof of overpricing.

For example, **MRNA Aug 24, Aug 28 195C**, was 3.15Δ / 40.24% OTM with a
$0.26/$0.36 quote, bid IV **32.96 points above ATM** and **38.10 points above the
deferred matched-delta mid IV**. It was excluded by the within-5%-of-high rule.
**NVDA Aug 26, Aug 31 242.5C**, was 3.72Δ / 15.70% OTM at $0.34/$0.35;
its corresponding excesses were **+6.82 / +25.99**. Negative recent return, IVR below 30,
and distance from the recent high hid it. **TSLA Sep 2, Sep 9 407.5C**, was
4.14Δ / 14.77% OTM at $0.36/$0.37 with **+12.38 / +4.92**; local RR rank and
IVR gates hid it. Conversely, **NBIS Aug 28** had a **+12.87-point** bid wing but
was **6.77 points cheaper than the deferred call**: a rich wing does not automatically
make the front expiry unusually expensive.

The exact-strike historical z-score question remains separate. Only the six original
MSTR selections have a completed prior-60-session matched-delta/DTE z-score study.
The new CSV explicitly marks the other histories unavailable. Do not substitute a
fixed-5Δ surface percentile or the cross-expiry spread for that z-score. The existing
MSTR study interpolates ATM; the current contract check uses the nearest-50Δ call,
so small differences in their reported ATM excesses are expected. IV comparisons use
the provider's bid-IV and mid-IV fields. [ORATS definitions](https://orats.com/docs/definitions).

### Daily broader call inventory

All observations below are **signal-day EOD**, usable from the following session.
These broader discovery selections have **not received a new HIRO/minute-quote P&L
replay**. They do not establish profitable entries or successful second-leg timing.
The original nine call confirmations and 142 put confirmations remain the strict
complete-window cohort above; the 73-row research inventory is separately labelled.

| Signal date (EOD) | Rich-front stock-days checked | 2–10Δ quote passes: 5–12 DTE | 2–10Δ quote passes: 13–19 DTE | Selected calls passing both bid-richness diagnostics |
| --- | --- | --- | --- | --- |
| 2026-08-11 | 21 | SMCI | None | SMCI |
| 2026-08-12 | 27 | AAPL, GOOG, HOOD, META, TSLA, W | None | GOOG |
| 2026-08-13 | 28 | AAPL, CSCO, JNJ, NOW, SMCI, TSLA | None | CSCO, SMCI |
| 2026-08-14 | 23 | DELL, MCD | AAPL, CSCO, FCX | FCX, MCD |
| 2026-08-17 | 31 | AMAT, CSCO, DELL, GOOG, LRCX, MCD | None | AMAT, GOOG |
| 2026-08-18 | 18 | AVGO, BX, TSLA | None | None |
| 2026-08-19 | 31 | AVGO, COIN, META, MSTR, TSLA | None | COIN, MSTR |
| 2026-08-20 | 40 | AVGO, COIN, MRNA, MSTR | CSCO, WMT | COIN, MRNA, MSTR, WMT |
| 2026-08-21 | 26 | AVGO, BABA, COIN, HOOD, MRNA, MSTR, TEM, TSLA | None | BABA, COIN, HOOD, MRNA, MSTR, TSLA |
| 2026-08-24 | 16 | JNJ, MRNA, MSTR, STX | None | JNJ, MRNA, MSTR, STX |
| 2026-08-25 | 18 | None | None | None |
| 2026-08-26 | 22 | APP, AVGO, NVDA | None | NVDA |
| 2026-08-27 | 25 | CVNA, HOOD, MSTR | None | None |
| 2026-08-28 | 18 | BE, NBIS, NVDA | None | BE, NVDA |
| 2026-08-31 | 10 | MCD, MSTR | AMAT | MCD, MSTR |
| 2026-09-01 | 19 | GOOG | None | None |
| 2026-09-02 | 17 | AVGO, GOOG, GOOGL, TSLA | ON | AVGO, TSLA |
| 2026-09-03 | 23 | AVGO, CRDO, MSTR | VST, W | MSTR, W |
| 2026-09-04 | Unavailable | Unavailable | Unavailable | Unavailable |


### Which broader candidates already have HIRO for leg-timing research?

**21 of 73** selections have verified existing All Trades HIRO on the next-session entry day. **13** also pass both bid-richness diagnostics; **8** of those have captures for entry and both following sessions. The table below lists that 13-row intersection. Capture availability is not a HIRO trigger, complete minute-quote coverage, or a profitable trade. The CSV retains signal-day and next-three-session status for all 73; later dates beyond September 4 are censored, not missing-market claims.

| Signal EOD | Ticker | Next-session entry: HIRO verified | Entry +1 session | Entry +2 sessions |
| --- | --- | --- | --- | --- |
| 2026-08-20 | COIN | 2026-08-21 | verified existing capture | verified existing capture |
| 2026-08-20 | MSTR | 2026-08-21 | verified existing capture | verified existing capture |
| 2026-08-21 | COIN | 2026-08-24 | verified existing capture | verified existing capture |
| 2026-08-21 | MSTR | 2026-08-24 | verified existing capture | verified existing capture |
| 2026-08-24 | JNJ | 2026-08-25 | verified existing capture | verified existing capture |
| 2026-08-24 | MSTR | 2026-08-25 | verified existing capture | verified existing capture |
| 2026-08-24 | STX | 2026-08-25 | verified existing capture | verified existing capture |
| 2026-08-26 | NVDA | 2026-08-27 | verified existing capture | verified existing capture |
| 2026-08-28 | BE | 2026-08-31 | verified existing capture | no verified capture in frozen archive |
| 2026-08-28 | NVDA | 2026-08-31 | verified existing capture | no verified capture in frozen archive |
| 2026-08-31 | MSTR | 2026-09-01 | verified existing capture | no verified capture in frozen archive |
| 2026-09-03 | MSTR | 2026-09-04 | beyond frozen cutoff | beyond frozen cutoff |
| 2026-09-03 | W | 2026-09-04 | beyond frozen cutoff | beyond frozen cutoff |

[Verified HIRO capture paths, time coverage and hashes](call_search_expansion/hiro_capture_sources.csv).


[Every selected call, ranks, quote, delta, % OTM and exclusion](call_search_expansion/expanded_call_candidate_tables.md),
[73-row contract and prospective second-leg CSV](call_search_expansion/call_candidates_2_to_10_delta.csv),
[band comparison](call_search_expansion/band_summary.csv),
[all 413 discovery rows](call_search_expansion/surface_candidates.csv),
[chain coverage](call_search_expansion/coverage.csv), and
[scanner fix](call_search_expansion/selector_fix.patch).


## Charlie and Brent: where the call-skew journey stands

The follow-on study now tests the personas' ideas across **317 observed stocks in the
frozen HIRO ticker set**, with **173,413 eligible stock-days** from January 2024 through
September 3, 2026. It tracks episode age, cumulative richness, retreat from the known
peak, wing rollover, price/IV acceleration and 30/60-calendar-day implied-versus-realized
variance. [Full research report and chart](../pandar_skew_journey_2026-09-06/pandar_skew_journey_research.md).

The primary two-session, post-next-session-reference result was **23.8%** for spot down
and ATM IV10 down under high skew alone, **28.6%** after six or more elevated sessions,
and **27.7%** after two successive wing declines. Older episodes showed **63.2% call-wing
compression**, but average spot movement was effectively flat. Positive 30/60 variance
gaps alone did not improve this timing test; the larger combined filter weakened in 2026.
Both personas retain age and rollover as modest volatility-normalization hypotheses.

These are **daily stock/surface outcomes, not additional profitable option trades**.
The [73-call journey table](../pandar_skew_journey_2026-09-06/recent_73_calls_with_journey.csv)
adds the exact call's delta, % OTM and normalized distance alongside episode age,
high-skew days in the last 20 sessions, peak retreat, IV/RV and existing HIRO coverage.
The constant-5Δ/10D proxy's journey does not replace the sold strike's own z-score.
The [persona decisions](../pandar_skew_journey_2026-09-06/persona_decisions.md) record
their separate pre-test proposals and post-result reviews.

### The original surface and quote observations

**MSTR combined an extreme local call tail with a usable bid and a tight selected-call
quote. Overall IV Rank alone did not distinguish it.** For example, on August 20:

- MSTR: IVR **54.85**, local RR rank **0**, front-wing rank **96.43**, kink rank **88.89**;
  selected 150C quoted **$0.32/$0.38**, a six-cent width.
- COIN: IVR **68.49**, local RR rank **0**, front-wing rank **98.41**, kink rank **78.57**;
  selected 225C quoted **$0.29/$0.42**, a thirteen-cent width. Its surface qualified;
  our ten-cent quote-width rule rejected that selected contract. The new audit found
  the **220C at $0.41/$0.50**, so COIN should not have been rejected at the ticker level.
- NEM: IVR **50.83** and similarly extreme call-wing/RR ranks, but no contract in the
  project's 2–6Δ / 5–19-DTE search envelope. That says nothing conclusive about a broader
  Pandar-style strike search.

The table includes **all 24 call surface candidates**, including failures. Call-skew
rank is informative but was not an additional call-grab gate. The CSV retains opposite
put-wing rank, trend, earnings and liquidity checks too.

| Date | Ticker | IVR | Local RR rank | Call-skew rank | Front-wing rank | Kink rank | Selected-contract result |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-11 | FANG | 53.1 | 6.0 | 82.1 | 87.7 | 87.7 | far-call bid below 0.20; far-call quote wider than 0.10 |
| 2026-08-12 | FDX | 31.9 | 8.3 | 93.3 | 97.2 | 73.4 | far-call bid below 0.20; far-call quote wider than 0.10 |
| 2026-08-12 | LRCX | 56.7 | 0.4 | 96.8 | 93.7 | 77.8 | far-call quote wider than 0.10 |
| 2026-08-13 | LRCX | 57.5 | 0.4 | 99.6 | 96.8 | 79.8 | far-call quote wider than 0.10 |
| 2026-08-13 | SMCI | 63.2 | 1.6 | 94.8 | 94.8 | 80.2 | far-call bid below 0.20 |
| 2026-08-17 | GS | 37.9 | 1.6 | 95.6 | 99.2 | 86.5 | far-call quote wider than 0.10 |
| 2026-08-17 | LRCX | 50.2 | 2.0 | 94.4 | 92.9 | 79.0 | **Alternative passes**; original selected call failed |
| 2026-08-19 | COIN | 59.2 | 2.4 | 92.5 | 88.9 | 70.2 | **Alternative passes**; original selected call failed |
| 2026-08-19 | MSTR | 47.7 | 0.4 | 96.8 | 92.1 | 84.9 | **Scanner pass** |
| 2026-08-20 | COIN | 68.5 | 0.0 | 98.0 | 98.4 | 78.6 | **Alternative passes**; original selected call failed |
| 2026-08-20 | MSTR | 54.9 | 0.0 | 99.2 | 96.4 | 88.9 | **Scanner pass** |
| 2026-08-20 | NEM | 50.8 | 0.4 | 96.8 | 97.2 | 76.2 | no 2-6 delta call in 5-19 DTE |
| 2026-08-21 | MRK | 67.9 | 4.0 | 91.7 | 93.7 | 73.8 | far-call bid below 0.20; far-call quote wider than 0.10 |
| 2026-08-21 | MSTR | 55.3 | 0.4 | 98.4 | 97.2 | 79.4 | **Scanner pass** |
| 2026-08-21 | NEM | 54.5 | 2.4 | 94.4 | 96.4 | 73.0 | no 2-6 delta call in 5-19 DTE |
| 2026-08-24 | CPNG | 50.0 | 8.7 | 72.2 | 94.4 | 87.7 | far-call bid below 0.20 |
| 2026-08-24 | JNJ | 60.8 | 4.4 | 86.9 | 93.3 | 77.8 | far-call bid below 0.20; far-call quote wider than 0.10; far-call OI below 25 |
| 2026-08-24 | MSTR | 54.1 | 1.2 | 99.6 | 94.8 | 98.0 | **Scanner pass** |
| 2026-08-25 | ABBV | 40.8 | 9.9 | 86.9 | 89.3 | 79.4 | far-call bid below 0.20; far-call quote wider than 0.10; far-call OI below 25 |
| 2026-08-25 | CPNG | 47.7 | 8.3 | 82.1 | 85.7 | 73.0 | far-call bid below 0.20; far-call quote wider than 0.10; far-call OI below 25 |
| 2026-08-27 | GAP | 47.6 | 5.2 | 94.4 | 94.8 | 98.8 | far-call bid below 0.20; selected call less than 2 vol points above ATM |
| 2026-08-28 | CPNG | 45.9 | 0.8 | 83.7 | 100.0 | 96.4 | far-call bid below 0.20; far-call quote wider than 0.10; far-call OI below 25 |
| 2026-08-31 | MSTR | 40.3 | 3.6 | 93.3 | 86.1 | 73.8 | **Scanner pass** |
| 2026-09-03 | MSTR | 50.4 | 0.0 | 99.6 | 90.5 | 78.6 | **Scanner pass** |


The table now includes the three recovered alternative-contract passes. Remaining
failures preserve the original selected-contract reason; the exhaustive audit and
separate filter sensitivities above explain the scope of those rejections.

### All nine exact call qualifications: % OTM and both deltas

The first strike is the **short farther call**, the second the **prospective long nearer
call**. Delta below is the positive **option** delta ×100, not signed position delta:
selling a 4Δ call creates approximately −4 shares of position delta per contract.
Moneyness for calls is `100 × (strike / stock − 1)`.

| Signal date | Ticker | Expiry | DTE | Sell / buy strike | % OTM sell / buy | Option Δ sell / buy (×100) | Short bid / ask | Selected mid-IV − ATM (pts) | Next-session HIRO |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-17 | LRCX | 2026-08-21 | 5 | 400 / 395 | 16.7 / 15.3 | 3.13 / 4.25 | $0.31 / $0.37 | 8.33 | alternative contract not yet replayed |
| 2026-08-19 | COIN | 2026-08-28 | 10 | 200 / 195 | 25.8 / 22.6 | 5.01 / 6.85 | $0.43 / $0.50 | 18.17 | alternative contract not yet replayed |
| 2026-08-19 | MSTR | 2026-08-28 | 10 | 140 / 135 | 34.8 / 30.0 | 3.36 / 5.05 | $0.24 / $0.29 | 27.89 | hiro unavailable |
| 2026-08-20 | COIN | 2026-08-28 | 9 | 220 / 215 | 28.2 / 25.3 | 5.02 / 6.41 | $0.41 / $0.50 | 23.13 | alternative contract not yet replayed |
| 2026-08-20 | MSTR | 2026-08-28 | 9 | 150 / 145 | 33.9 / 29.4 | 4.31 / 6.05 | $0.32 / $0.38 | 28.33 | admitted |
| 2026-08-21 | MSTR | 2026-08-28 | 8 | 160 / 155 | 34.3 / 30.1 | 3.83 / 5.41 | $0.26 / $0.32 | 33.33 | admitted |
| 2026-08-24 | MSTR | 2026-08-28 | 5 | 155 / 152.5 | 26.8 / 24.7 | 3.54 / 4.52 | $0.22 / $0.27 | 30.87 | no live quote gate at flow trigger |
| 2026-08-31 | MSTR | 2026-09-04 | 5 | 160 / 157.5 | 20.7 / 18.8 | 4.26 / 5.38 | $0.23 / $0.25 | 21.82 | no live quote gate at flow trigger |
| 2026-09-03 | MSTR | 2026-09-11 | 9 | 190 / 185 | 32.5 / 29.0 | 3.44 / 4.71 | $0.25 / $0.31 | 24.03 | no live quote gate at flow trigger |


The six **original MSTR** exact passes produced only two HIRO entries; the recovered
LRCX and COIN pairs have not yet been replayed. MSTR's August 19 following session had
no captured HIRO. August 24 had a flow trigger but no qualifying live quote at that
trigger. For August 31 and September 3, the selected short never met the replay's
$0.20-bid gate on the next-session decision grid. The last two EOD qualifications were
therefore not actionable under this particular timing protocol, despite passing the
original EOD screen.

### Were the particular calls exceptionally rich?

**The useful z-score is of the strike's IV richness at matched delta (or % OTM) and
time to expiry—not a z-score of delta itself.** Raw option-price history mixes spot,
moneyness and decay; a fixed 5Δ/10D rank can also miss what the actual selected strike
offers.

For each selected MSTR call, this update measures:

`tail excess = selected call BID IV − same-tenor ATM call MID IV`

`z = (current tail excess − mean of prior matched excesses) / prior sample standard deviation`

Historical surfaces are interpolated at **that selected call's delta and vendor DTE**.
Strike interpolation stays inside observed support; tenor interpolation uses total
variance, `IV² × DTE`. The comparison uses the previous **60 trading sessions**, with
at least **40 valid matched observations**, and excludes qualification day and future
data. The bid-based tail metric examines the IV available to a seller; the CSV also
includes midpoint, absolute bid-IV, and median/MAD robustness diagnostics. These are
quote-derived surface diagnostics, not fill guarantees.

| Signal date | Sell strike | Δ (×100) | % OTM | DTE | Bid IV % | ATM mid IV % | Tail excess (pts) | Valid n / 60 | Delta/DTE z | Historical percentile | OTM/DTE history |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-19 | 140C | 3.36 | 34.8 | 10 | 102.01 | 75.93 | 26.08 | 60 | **+3.41** | 100.0 | 36; no z |
| 2026-08-20 | 150C | 4.31 | 33.9 | 9 | 110.27 | 83.80 | 26.46 | 60 | **+3.91** | 100.0 | 26; no z |
| 2026-08-21 | 160C | 3.83 | 34.3 | 8 | 114.18 | 82.82 | 31.36 | 59 | **+4.05** | 100.0 | 13; no z |
| 2026-08-24 | 155C | 3.54 | 26.8 | 5 | 122.20 | 93.57 | 28.64 | 52 | **+2.76** | 96.2 | 20; no z |
| 2026-08-31 | 160C | 4.26 | 20.7 | 5 | 100.92 | 79.90 | 21.02 | 51 | **+1.57** | 90.2 | 33; no z |
| 2026-09-03 | 190C | 3.44 | 32.5 | 9 | 98.72 | 76.69 | 22.03 | 60 | **+1.39** | 91.7 | 32; no z |


The August 20 and 21 selected calls were **+3.91z and +4.05z** in matched-delta tail
excess, despite overall IVR around **55**. That supports the specific-tail-richness
interpretation of those two cases. The August 31 and September 3 calls were only
**+1.57z and +1.39z** under this diagnostic; their high 252-session surface percentiles
did not imply the same magnitude of current strike richness.

This is a **retrospective diagnostic across all six confirmations**, not a newly
validated entry threshold or proof that a high z-score predicts profit. The historical
baseline is short, may be non-normal, and includes earnings/event regimes rather than
matching them. Delta matching is itself model-dependent. A 100th historical percentile
means higher than the finite prior sample, not a 100% chance of a reversal.

The parallel **same-%-OTM / same-DTE** test has only **13–36** valid observations in
the 60-session window. It therefore reports **no z-score** instead of extrapolating
deep-tail quotes. The downloaded chains cover 0.5–80 call delta and 1–30 vendor DTE;
that limits fixed-OTM support. Sparse OTM history is a coverage gap, not evidence that
the call was fairly priced. A later comparison can widen historical chain coverage
and control event regimes before using this as a decision gate.

[All strike-richness calculations](mstr_matched_strike_richness.csv),
[every prior matched observation](mstr_matched_strike_history.csv), and
[raw-chain provenance](richness_sources.csv).

### Qualification Greeks versus each modeled leg's execution-time Greeks

These snapshots are for the **source dime-credit target with renewed HIRO confirmation**,
whose second legs arrived two sessions later and whose modeled net P&Ls were
**+$10.40 and +$22.40**. The earlier fee-covering target and its different leg times
remain separately documented in the timing analysis below.

| Signal date | Leg time (ET) | Contract, Aug 28 expiry | Stock | % OTM | Option Δ (×100) | Theta IV % | Bid / ask |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-08-20 | Aug 21 10:41 | Sell 150C | $118.63 | 26.44 | 8.10 | 114.32 | $0.61 / $0.70 |
| 2026-08-20 | Aug 25 11:27 | Buy 145C | $125.78 | 15.28 | 8.49 | 106.71 | $0.45 / $0.50 |
| 2026-08-21 | Aug 24 10:51 | Sell 160C | $124.50 | 28.51 | 4.29 | 130.39 | $0.26 / $0.32 |
| 2026-08-21 | Aug 26 11:45 | Buy 155C | $122.42 | 26.61 | 0.80 | 124.37 | $0.03 / $0.04 |

The latest available **prior-session EOD ranks** at each leg were:

| Leg time (ET) | Leg | Rank observation date | IVR | Local RR rank | Call-skew rank | Front-wing rank | Kink rank |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Aug 21 10:41 | Sell 150C | 2026-08-20 | 54.85 | 0.00 | 99.21 | 96.43 | 88.89 |
| Aug 25 11:27 | Buy 145C | 2026-08-24 | 54.13 | 1.19 | 99.60 | 94.84 | 98.02 |
| Aug 24 10:51 | Sell 160C | 2026-08-21 | 55.29 | 0.40 | 98.41 | 97.22 | 79.37 |
| Aug 26 11:45 | Buy 155C | 2026-08-25 | 48.07 | 2.38 | 94.84 | 84.13 | 56.35 |


By the August 26 second leg, the preceding session's front-wing rank had fallen to
**84.13** and kink rank to **56.35**, below the original sale-screen gates. Broad IVR
was **48.07**. That is consistent with the earlier front-tail expansion normalizing;
the second-leg purchase was governed by its affordable ask and the frozen HIRO rule,
not a requirement that the original call-sale screen stay active. These ranks were
available before the leg; they are not intraday recomputations.
[Per-leg surface context](execution_surface_context.csv).

The August 20 screen chose a **4.31Δ, 33.9%-OTM** 150C. By its August 21 10:41 sale
it was **8.10Δ and 26.44% OTM**. That exceeded **our original screening band**; it did
**not** violate a documented Pandar delta requirement. The frozen replay selected the
prior-EOD contract and retested price/flow, without imposing a new execution-time delta
veto. These P&Ls therefore cannot be advertised as trades sold strictly within 2–6Δ.

The August 21 screen chose the 160C at **3.83Δ and 34.3% OTM**; the August 24 sale was
**4.29Δ and 28.51% OTM**. The later $0.04 long-call quote has a relatively unstable
IV estimate because the option is tiny-priced; its reported IV is descriptive.
ThetaData's contemporaneous underlying and Greeks are used in this table. ORATS EOD
Greeks and prior-minute HIRO stock readings are different observations and must not be
treated as synchronized. **Execution-time matched-surface z-scores are not available**
from these four exact-contract snapshots; the preceding z-score table is EOD only.
[Exact snapshot data](actual_execution_greeks.csv).

## Every exact put-tail qualification, with ranks and both legs

All 142 confirmed put rows follow, including the 67 newly backfilled rows.
Each satisfied IVR ≤35, local RR rank ≤50,
put-skew rank ≤25 and the recorded exact-quote gates. `% OTM = 100 × (1 − strike / stock)`.
The first strike is the higher **buy** put; the second is the lower **sell** put.

**Put delta convention:** the source's `leg1_delta` is ORATS's call-coordinate delta,
often near 0.99 for these strikes. Printing it as a +99Δ put would be wrong. The tables
show the approximation **put option delta = call-coordinate delta − 1**, multiplied by
100; the CSV retains both raw coordinates and the conversion label. These are model
approximations, not independently supplied American-put Greeks. A short put reverses
the displayed option-delta sign at the position level.


**2026-08-11 — 9 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APA | 18.6 | 1.6 | 0.0 | 2026-09-18 | 39 | 30 / 25 | 26.5 / 38.8 | -1.896 / -0.065 | $0.07 |
| CCL | 24.4 | 31.3 | 7.9 | 2026-09-18 | 39 | 20 / 15 | 27.5 / 45.6 | -1.657 / -0.004 | $0.03 |
| CELH | 31.2 | 1.2 | 1.2 | 2026-09-18 | 39 | 20 / 15 | 28.3 / 46.2 | -2.757 / -0.191 | $0.08 |
| DAL | 17.5 | 0.8 | 0.0 | 2026-09-18 | 39 | 60 / 55 | 33.9 / 39.4 | -0.086 / -0.008 | $0.07 |
| GOOG | 29.9 | 13.9 | 7.9 | 2026-09-18 | 39 | 240 / 235 | 30.1 / 31.5 | -0.339 / -0.229 | $0.06 |
| LYFT | 11.7 | 15.1 | 4.0 | 2026-10-16 | 67 | 13 / 8 | 26.5 / 54.8 | -6.325 / -0.201 | $0.07 |
| NVDA | 10.9 | 20.2 | 14.3 | 2026-09-18 | 39 | 135 / 130 | 38.0 / 40.3 | -0.780 / -0.523 | $0.03 |
| PLTR | 25.0 | 8.7 | 4.0 | 2026-09-18 | 39 | 105 / 100 | 40.2 / 43.0 | -0.982 / -0.628 | $0.06 |
| UAL | 16.3 | 8.3 | 3.6 | 2026-09-18 | 39 | 85 / 80 | 32.9 / 36.8 | -0.528 / -0.169 | $0.08 |


**2026-08-12 — 6 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CCJ | 20.9 | 14.3 | 4.4 | 2026-09-18 | 38 | 70 / 65 | 29.4 / 34.4 | -0.556 / -0.110 | $0.06 |
| CELH | 28.4 | 4.4 | 9.5 | 2026-09-18 | 38 | 17.5 / 15 | 36.2 / 45.3 | -0.399 / -0.021 | $0.03 |
| DAL | 15.3 | 0.0 | 0.0 | 2026-09-18 | 38 | 60 / 55 | 33.7 / 39.2 | -0.115 / -0.067 | $0.02 |
| GOOGL | 27.9 | 20.2 | 8.3 | 2026-09-18 | 38 | 250 / 245 | 27.4 / 28.9 | -0.410 / -0.272 | $0.07 |
| NVDA | 6.6 | 11.9 | 9.5 | 2026-09-18 | 38 | 130 / 125 | 41.5 / 43.8 | -0.113 / -0.111 | $0.04 |
| PLTR | 15.0 | 15.9 | 8.3 | 2026-09-18 | 38 | 100 / 95 | 41.6 / 44.5 | -0.228 / -0.099 | $0.06 |


**2026-08-13 — 9 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 33.4 | 14.7 | 9.9 | 2026-09-18 | 37 | 190 / 185 | 28.4 / 30.3 | -0.017 / -0.005 | $0.05 |
| ASTS | 18.1 | 25.0 | 23.8 | 2026-09-18 | 37 | 40 / 35 | 44.3 / 51.2 | -1.014 / -0.242 | $0.10 |
| CRWV | 18.6 | 1.6 | 0.0 | 2026-09-18 | 37 | 60 / 55 | 43.6 / 48.3 | -1.078 / -0.440 | $0.09 |
| DAL | 15.3 | 2.4 | 1.2 | 2026-09-18 | 37 | 62.5 / 57.5 | 31.7 / 37.1 | -0.100 / -0.008 | $0.05 |
| GOOGL | 27.3 | 5.2 | 1.6 | 2026-09-18 | 37 | 235 / 230 | 32.1 / 33.6 | -0.064 / -0.063 | $0.06 |
| NVDA | 3.6 | 15.9 | 11.9 | 2026-09-18 | 37 | 130 / 125 | 42.4 / 44.6 | -0.292 / -0.203 | $0.03 |
| PLTR | 24.8 | 8.7 | 4.0 | 2026-09-18 | 37 | 105 / 100 | 41.6 / 44.4 | -0.025 / -0.007 | $0.06 |
| TGT | 28.2 | 11.5 | 2.8 | 2026-09-18 | 37 | 110 / 105 | 29.4 / 32.6 | -0.219 / -0.120 | $0.07 |
| TSLA | 5.1 | 32.1 | 21.4 | 2026-09-18 | 37 | 235 / 230 | 30.8 / 32.2 | -0.812 / -0.565 | $0.03 |


**2026-08-14 — 12 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 26.9 | 7.1 | 4.4 | 2026-09-18 | 36 | 190 / 185 | 27.8 / 29.7 | -0.011 / -0.003 | $0.03 |
| BA | 29.4 | 9.1 | 7.5 | 2026-09-18 | 36 | 170 / 165 | 26.5 / 28.7 | -0.134 / -0.051 | $0.04 |
| CRCL | 33.5 | 22.2 | 20.6 | 2026-09-18 | 36 | 40 / 35 | 44.6 / 51.6 | -0.558 / -0.103 | $0.10 |
| CRWV | 17.3 | 4.0 | 0.8 | 2026-09-18 | 36 | 60 / 55 | 43.1 / 47.9 | -1.085 / -0.437 | $0.10 |
| GM | 31.6 | 3.2 | 4.8 | 2026-09-18 | 36 | 62.5 / 57.5 | 28.1 / 33.8 | -0.354 / -0.215 | $0.02 |
| GOOG | 12.6 | 3.6 | 0.8 | 2026-09-18 | 36 | 195 / 190 | 43.1 / 44.6 | -0.063 / -0.063 | $0.01 |
| GOOGL | 13.8 | 6.0 | 3.2 | 2026-09-18 | 36 | 235 / 230 | 31.9 / 33.3 | -0.095 / -0.079 | $0.04 |
| NVDA | 0.0 | 9.9 | 7.1 | 2026-09-18 | 36 | 125 / 120 | 44.5 / 46.7 | -0.110 / -0.110 | $0.02 |
| PLTR | 6.9 | 21.4 | 10.3 | 2026-09-18 | 36 | 105 / 100 | 39.8 / 42.7 | -0.015 / -0.004 | $0.05 |
| QBTS | 4.8 | 23.0 | 16.3 | 2026-09-18 | 36 | 12 / 9 | 43.6 / 57.7 | -1.676 / -0.077 | $0.03 |
| SBUX | 0.0 | 13.5 | 8.3 | 2026-09-18 | 36 | 80 / 75 | 25.7 / 30.4 | -0.041 / -0.002 | $0.06 |
| TSLA | 9.7 | 27.8 | 24.6 | 2026-09-18 | 36 | 200 / 195 | 41.5 / 42.9 | -0.021 / -0.011 | $0.04 |


**2026-08-17 — 8 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 30.8 | 4.0 | 5.6 | 2026-09-18 | 33 | 175 / 170 | 32.8 / 34.7 | -0.011 / -0.004 | $0.02 |
| CRWV | 21.4 | 7.9 | 5.6 | 2026-09-18 | 33 | 60 / 55 | 43.5 / 48.2 | -0.934 / -0.363 | $0.10 |
| GOOG | 16.3 | 11.9 | 7.9 | 2026-10-16 | 61 | 210 / 205 | 38.4 / 39.9 | -0.099 / -0.083 | $0.05 |
| GOOGL | 19.5 | 24.6 | 8.7 | 2026-09-18 | 33 | 255 / 250 | 25.8 / 27.2 | -0.186 / -0.125 | $0.03 |
| HOOD | 28.3 | 4.4 | 4.0 | 2026-09-18 | 33 | 55 / 50 | 42.8 / 48.0 | -0.104 / -0.016 | $0.06 |
| NVDA | 2.7 | 9.9 | 7.5 | 2026-09-18 | 33 | 130 / 125 | 42.4 / 44.6 | -0.146 / -0.124 | $0.02 |
| PLTR | 8.9 | 12.3 | 8.3 | 2026-09-18 | 33 | 105 / 100 | 39.2 / 42.1 | -0.097 / -0.036 | $0.05 |
| SEDG | 13.8 | 8.7 | 11.5 | 2026-09-18 | 33 | 20 / 15 | 35.3 / 51.5 | -3.156 / -0.142 | $0.10 |


**2026-08-18 — 6 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 32.5 | 6.0 | 3.2 | 2026-09-18 | 32 | 165 / 160 | 36.5 / 38.4 | -0.006 / -0.002 | $0.02 |
| GOOG | 19.2 | 19.4 | 15.9 | 2026-09-18 | 32 | 235 / 230 | 31.3 / 32.8 | -0.064 / -0.064 | $0.04 |
| GOOGL | 20.4 | 13.1 | 8.3 | 2026-09-18 | 32 | 250 / 245 | 27.4 / 28.8 | -0.072 / -0.067 | $0.03 |
| HIMS | 9.4 | 28.2 | 23.8 | 2026-09-18 | 32 | 20 / 15 | 27.6 / 45.7 | -4.921 / -0.128 | $0.07 |
| NVDA | 4.6 | 14.7 | 11.5 | 2026-09-18 | 32 | 125 / 120 | 43.0 / 45.3 | -0.113 / -0.113 | $0.02 |
| PLTR | 10.1 | 19.0 | 17.5 | 2026-09-18 | 32 | 110 / 105 | 35.8 / 38.7 | -0.059 / -0.017 | $0.05 |


**2026-08-19 — 7 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 33.6 | 18.3 | 11.1 | 2026-09-18 | 31 | 195 / 190 | 26.5 / 28.4 | -0.015 / -0.005 | $0.05 |
| CCJ | 15.2 | 26.6 | 23.0 | 2026-09-18 | 31 | 70 / 65 | 28.6 / 33.7 | -0.472 / -0.081 | $0.07 |
| GOOG | 25.2 | 17.1 | 6.3 | 2026-09-18 | 31 | 200 / 195 | 41.5 / 42.9 | -0.064 / -0.064 | $0.04 |
| GOOGL | 24.7 | 20.6 | 7.5 | 2026-09-18 | 31 | 235 / 230 | 31.8 / 33.3 | -0.063 / -0.063 | $0.04 |
| HIMS | 21.5 | 24.2 | 14.3 | 2026-09-18 | 31 | 20 / 15 | 35.4 / 51.6 | -1.106 / -0.009 | $0.06 |
| NVDA | 6.2 | 15.1 | 10.3 | 2026-09-18 | 31 | 125 / 120 | 42.8 / 45.1 | -0.113 / -0.113 | $0.02 |
| TGT | 14.3 | 19.0 | 23.4 | 2026-09-18 | 31 | 115 / 110 | 28.1 / 31.2 | -0.029 / -0.005 | $0.07 |


**2026-08-20 — 5 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CRWV | 17.3 | 7.9 | 4.4 | 2026-09-18 | 30 | 50 / 45 | 44.3 / 49.9 | -0.562 / -0.147 | $0.07 |
| GOOG | 23.1 | 39.7 | 23.8 | 2026-09-18 | 30 | 220 / 215 | 35.0 / 36.5 | -0.066 / -0.065 | $0.05 |
| GOOGL | 22.8 | 36.1 | 17.1 | 2026-09-18 | 30 | 235 / 230 | 31.1 / 32.6 | -0.107 / -0.085 | $0.05 |
| NVDA | 25.3 | 6.3 | 11.1 | 2026-09-18 | 30 | 120 / 115 | 44.7 / 47.0 | -0.144 / -0.126 | $0.02 |
| SEDG | 6.0 | 17.9 | 23.8 | 2026-09-18 | 30 | 20 / 17.5 | 35.3 / 43.4 | -1.688 / -0.247 | $0.09 |


**2026-08-21 — 5 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 33.9 | 19.4 | 22.2 | 2026-09-18 | 29 | 170 / 165 | 34.6 / 36.5 | -0.021 / -0.021 | $0.03 |
| CRWV | 16.5 | 9.1 | 4.0 | 2026-09-18 | 29 | 50 / 45 | 43.4 / 49.0 | -0.429 / -0.099 | $0.09 |
| GOOG | 21.5 | 13.9 | 8.3 | 2026-09-18 | 29 | 195 / 190 | 43.1 / 44.6 | -0.063 / -0.063 | $0.03 |
| GOOGL | 19.6 | 19.0 | 16.3 | 2026-10-16 | 57 | 250 / 245 | 27.7 / 29.2 | -1.786 / -1.381 | $0.09 |
| NVDA | 15.5 | 6.3 | 6.7 | 2026-09-18 | 29 | 120 / 115 | 44.3 / 46.6 | -0.158 / -0.132 | $0.03 |


**2026-08-24 — 7 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CCJ | 30.0 | 21.4 | 19.0 | 2026-09-18 | 26 | 75 / 70 | 26.7 / 31.6 | -0.698 / -0.137 | $0.05 |
| CRWV | 17.5 | 0.8 | 2.8 | 2026-09-18 | 26 | 47.5 / 42.5 | 45.0 / 50.8 | -0.280 / -0.054 | $0.05 |
| GOOG | 26.7 | 26.2 | 10.7 | 2026-09-18 | 26 | 255 / 250 | 26.2 / 27.7 | -0.066 / -0.064 | $0.05 |
| GOOGL | 29.1 | 24.2 | 9.9 | 2026-10-16 | 54 | 235 / 230 | 32.7 / 34.1 | -0.391 / -0.275 | $0.06 |
| NVDA | 16.7 | 9.5 | 10.3 | 2026-09-18 | 26 | 130 / 125 | 37.6 / 40.0 | -0.121 / -0.119 | $0.03 |
| PLTR | 17.9 | 32.1 | 24.6 | 2026-09-18 | 26 | 105 / 100 | 40.6 / 43.4 | -0.053 / -0.017 | $0.04 |
| TGT | 14.9 | 17.5 | 13.1 | 2026-09-18 | 26 | 125 / 120 | 26.2 / 29.2 | -0.077 / -0.030 | $0.02 |


**2026-08-25 — 8 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 11.7 | 18.7 | 15.9 | 2026-09-18 | 25 | 130 / 125 | 39.9 / 42.2 | -1.477 / -0.999 | $0.10 |
| CRWV | 16.6 | 6.0 | 7.1 | 2026-09-18 | 25 | 55 / 50 | 37.5 / 43.2 | -1.199 / -0.372 | $0.08 |
| GOOG | 18.8 | 6.0 | 4.0 | 2026-09-18 | 25 | 190 / 185 | 44.7 / 46.1 | -0.063 / -0.063 | $0.08 |
| GOOGL | 20.4 | 7.1 | 3.6 | 2026-10-16 | 53 | 250 / 245 | 28.0 / 29.4 | -1.007 / -0.720 | $0.05 |
| IREN | 0.0 | 15.1 | 14.3 | 2026-09-18 | 25 | 25 / 20 | 40.6 / 52.5 | -2.111 / -0.266 | $0.08 |
| NVDA | 23.0 | 7.1 | 5.6 | 2026-09-18 | 25 | 120 / 115 | 43.5 / 45.9 | -0.116 / -0.116 | $0.01 |
| SCHW | 22.1 | 8.3 | 8.7 | 2026-09-18 | 25 | 77.5 / 75 | 31.5 / 33.7 | -0.007 / -0.007 | $0.07 |
| SOFI | 17.1 | 30.6 | 15.9 | 2026-10-16 | 53 | 11 / 8 | 41.5 / 57.5 | -0.710 / -0.007 | $0.04 |


**2026-08-26 — 7 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 32.9 | 21.0 | 19.8 | 2026-09-18 | 24 | 180 / 175 | 30.8 / 32.8 | -0.017 / -0.006 | $0.03 |
| BE | 8.7 | 15.5 | 7.9 | 2026-09-18 | 24 | 135 / 130 | 38.6 / 40.8 | -1.503 / -1.033 | $0.10 |
| BMNR | 14.9 | 20.2 | 19.4 | 2026-09-18 | 24 | 18 / 13 | 28.3 / 48.2 | -4.431 / -0.092 | $0.10 |
| IREN | 0.0 | 13.9 | 12.3 | 2026-09-18 | 24 | 24 / 19 | 39.5 / 52.1 | -2.185 / -0.237 | $0.10 |
| MRNA | 24.1 | 12.7 | 11.5 | 2026-09-18 | 24 | 90 / 85 | 39.4 / 42.8 | -0.989 / -0.523 | $0.09 |
| NVDA | 27.4 | 7.1 | 5.2 | 2026-09-18 | 24 | 120 / 115 | 42.7 / 45.1 | -0.118 / -0.118 | $0.01 |
| PLTR | 23.4 | 25.8 | 23.4 | 2026-09-18 | 24 | 105 / 100 | 40.9 / 43.7 | -0.058 / -0.019 | $0.04 |


**2026-08-27 — 7 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 31.2 | 9.9 | 8.7 | 2026-09-18 | 23 | 150 / 145 | 41.6 / 43.6 | -0.004 / -0.004 | $0.01 |
| CRWV | 12.0 | 1.2 | 2.0 | 2026-09-18 | 23 | 50 / 45 | 42.3 / 48.1 | -0.221 / -0.036 | $0.05 |
| GOOG | 13.0 | 11.1 | 9.5 | 2026-10-16 | 51 | 230 / 225 | 31.9 / 33.4 | -0.353 / -0.243 | $0.06 |
| GOOGL | 12.4 | 6.3 | 3.6 | 2026-10-16 | 51 | 245 / 240 | 28.1 / 29.6 | -0.923 / -0.673 | $0.07 |
| NBIS | 24.1 | 21.4 | 15.5 | 2026-09-18 | 23 | 120 / 115 | 44.5 / 46.8 | -0.589 / -0.355 | $0.06 |
| NVDA | 9.2 | 11.1 | 23.0 | 2026-09-18 | 23 | 145 / 140 | 36.5 / 38.7 | -0.108 / -0.108 | $0.02 |
| PLTR | 22.6 | 15.1 | 8.3 | 2026-09-18 | 23 | 125 / 120 | 32.9 / 35.6 | -0.264 / -0.114 | $0.03 |


**2026-08-28 — 7 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BMNR | 10.3 | 24.2 | 19.4 | 2026-09-18 | 22 | 15 / 11 | 37.2 / 53.9 | -0.726 / -0.003 | $0.03 |
| CRWV | 4.1 | 0.8 | 2.0 | 2026-09-18 | 22 | 50 / 45 | 40.5 / 46.5 | -0.184 / -0.025 | $0.05 |
| CVNA | 23.1 | 4.4 | 4.8 | 2026-09-18 | 22 | 45 / 40 | 39.2 / 45.9 | -0.107 / -0.008 | $0.05 |
| GOOGL | 13.0 | 11.5 | 6.0 | 2026-10-16 | 50 | 235 / 230 | 32.4 / 33.8 | -0.196 / -0.141 | $0.06 |
| HOOD | 28.6 | 12.7 | 9.5 | 2026-09-18 | 22 | 70 / 65 | 32.9 / 37.7 | -0.710 / -0.200 | $0.07 |
| MRVL | 26.1 | 5.6 | 6.0 | 2026-09-18 | 22 | 140 / 135 | 35.8 / 38.1 | -0.206 / -0.126 | $0.03 |
| NVDA | 7.1 | 12.7 | 11.5 | 2026-09-18 | 22 | 135 / 130 | 37.8 / 40.1 | -0.114 / -0.112 | $0.01 |


**2026-08-31 — 12 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 32.8 | 18.3 | 16.7 | 2026-10-16 | 47 | 165 / 160 | 36.4 / 38.3 | -0.066 / -0.030 | $0.05 |
| BE | 0.0 | 11.1 | 11.5 | 2026-09-18 | 19 | 120 / 115 | 41.5 / 43.9 | -0.330 / -0.171 | $0.08 |
| BMNR | 10.8 | 24.2 | 22.2 | 2026-09-18 | 19 | 17 / 14 | 32.4 / 44.3 | -2.360 / -0.154 | $0.04 |
| CRWV | 0.9 | 1.6 | 3.2 | 2026-09-18 | 19 | 62.5 / 60 | 26.2 / 29.2 | -3.351 / -2.098 | $0.07 |
| GOOG | 17.4 | 13.9 | 9.9 | 2026-09-18 | 19 | 195 / 190 | 41.9 / 43.4 | -0.065 / -0.065 | $0.03 |
| GOOGL | 16.7 | 8.3 | 6.7 | 2026-10-16 | 47 | 240 / 235 | 29.2 / 30.7 | -0.447 / -0.299 | $0.06 |
| HOOD | 32.2 | 3.6 | 5.6 | 2026-09-18 | 19 | 65 / 60 | 38.0 / 42.8 | -0.043 / -0.005 | $0.03 |
| MRVL | 25.5 | 15.5 | 10.7 | 2026-09-18 | 19 | 135 / 130 | 36.3 / 38.7 | -0.063 / -0.024 | $0.03 |
| NVDA | 0.7 | 18.3 | 16.3 | 2026-09-18 | 19 | 130 / 125 | 40.9 / 43.2 | -0.110 / -0.104 | $0.01 |
| OKLO | 0.0 | 28.6 | 25.0 | 2026-09-18 | 19 | 30 / 25 | 26.0 / 38.3 | -2.783 / -0.157 | $0.10 |
| PLTR | 13.7 | 25.4 | 22.2 | 2026-09-18 | 19 | 105 / 100 | 43.9 / 46.6 | -0.041 / -0.040 | $0.03 |
| SHOP | 13.7 | 17.1 | 17.9 | 2026-09-18 | 19 | 95 / 90 | 35.5 / 38.9 | -0.060 / -0.057 | $0.03 |


**2026-09-01 — 6 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 29.7 | 26.2 | 19.4 | 2026-10-16 | 46 | 165 / 160 | 35.1 / 37.1 | -0.091 / -0.042 | $0.05 |
| BMNR | 9.0 | 23.8 | 24.6 | 2026-09-18 | 18 | 17.5 / 13 | 25.4 / 44.6 | -4.739 / -0.104 | $0.09 |
| CVNA | 22.4 | 7.5 | 10.3 | 2026-09-18 | 18 | 45 / 40 | 37.4 / 44.4 | -0.152 / -0.059 | $0.05 |
| GOOGL | 15.5 | 18.3 | 16.7 | 2026-10-16 | 46 | 250 / 245 | 25.2 / 26.7 | -1.082 / -0.765 | $0.05 |
| HOOD | 34.4 | 7.5 | 6.0 | 2026-09-18 | 18 | 65 / 60 | 37.3 / 42.1 | -0.107 / -0.044 | $0.03 |
| MRVL | 25.4 | 15.9 | 15.1 | 2026-09-18 | 18 | 135 / 130 | 35.6 / 38.0 | -0.138 / -0.059 | $0.03 |


**2026-09-02 — 11 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 29.6 | 12.7 | 10.3 | 2026-09-18 | 17 | 190 / 185 | 25.5 / 27.5 | -0.020 / -0.006 | $0.02 |
| ANET | 26.1 | 17.9 | 9.9 | 2026-09-18 | 17 | 130 / 125 | 30.1 / 32.8 | -0.044 / -0.013 | $0.04 |
| BE | 5.3 | 11.5 | 6.7 | 2026-09-18 | 17 | 145 / 140 | 33.0 / 35.3 | -1.745 / -1.151 | $0.09 |
| BMNR | 5.3 | 25.8 | 21.4 | 2026-09-18 | 17 | 16 / 11 | 30.8 / 52.4 | -2.708 / -0.046 | $0.05 |
| CRWV | 0.0 | 11.9 | 17.5 | 2026-09-18 | 17 | 50 / 45 | 38.4 / 44.6 | -0.124 / -0.012 | $0.02 |
| GOOG | 17.6 | 33.3 | 25.0 | 2026-09-18 | 17 | 195 / 190 | 41.6 / 43.1 | -0.065 / -0.065 | $0.02 |
| GOOGL | 15.3 | 20.2 | 8.3 | 2026-10-16 | 45 | 245 / 240 | 27.4 / 28.8 | -0.150 / -0.107 | $0.08 |
| IREN | 1.2 | 23.8 | 15.5 | 2026-09-18 | 17 | 26 / 21 | 34.4 / 47.0 | -1.375 / -0.056 | $0.06 |
| MRVL | 22.5 | 13.9 | 15.5 | 2026-09-18 | 17 | 120 / 115 | 41.9 / 44.3 | -0.009 / -0.003 | $0.02 |
| NVDA | 9.5 | 28.2 | 24.2 | 2026-09-18 | 17 | 135 / 130 | 39.8 / 42.0 | -0.107 / -0.103 | $0.01 |
| SOFI | 9.5 | 34.1 | 25.0 | 2026-10-16 | 45 | 12 / 9 | 33.1 / 49.8 | -0.904 / -0.003 | $0.04 |


**2026-09-03 — 10 put-tail scanner passes**

| Ticker | IVR | Local RR rank | Put-skew rank | Expiry | DTE | Buy / sell strike | % OTM buy / sell | Approx. option Δ buy / sell (×100) | Screen debit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AMZN | 32.2 | 14.7 | 20.2 | 2026-09-18 | 16 | 190 / 185 | 26.7 / 28.6 | -0.006 / -0.001 | $0.02 |
| BE | 7.3 | 15.9 | 17.9 | 2026-09-18 | 16 | 135 / 130 | 42.6 / 44.7 | -0.228 / -0.124 | $0.04 |
| BMNR | 14.8 | 24.2 | 19.0 | 2026-09-18 | 16 | 19 / 14 | 27.9 / 46.9 | -3.054 / -0.037 | $0.05 |
| CRWV | 2.8 | 7.9 | 4.4 | 2026-09-18 | 16 | 47.5 / 42.5 | 43.9 / 49.8 | -0.035 / -0.026 | $0.02 |
| GOOG | 18.2 | 7.9 | 4.0 | 2026-09-18 | 16 | 240 / 235 | 29.4 / 30.9 | -0.064 / -0.064 | $0.04 |
| MRVL | 23.1 | 15.5 | 13.5 | 2026-09-18 | 16 | 125 / 120 | 40.3 / 42.7 | -0.005 / -0.001 | $0.05 |
| MSFT | 31.2 | 23.0 | 21.4 | 2026-09-18 | 16 | 350 / 345 | 31.5 / 32.5 | -0.003 / -0.003 | $0.03 |
| NBIS | 16.2 | 20.6 | 14.3 | 2026-09-18 | 16 | 125 / 120 | 40.7 / 43.1 | -0.290 / -0.152 | $0.06 |
| NVDA | 8.8 | 13.9 | 17.1 | 2026-09-18 | 16 | 155 / 150 | 32.3 / 34.5 | -0.097 / -0.084 | $0.02 |
| RTX | 23.9 | 6.0 | 3.6 | 2026-09-18 | 16 | 120 / 115 | 40.5 / 43.0 | -0.019 / -0.019 | $0.03 |


These are EOD **eligibility quotes**, not fills or evidence that financing the second
leg was possible later. The original replay retains its 75 put qualifications and
missing HIRO; its primary statistics deduplicate strike pairs. The new early
confirmations are included here as eligibility findings, without replay outcomes. The timing analysis below
explains why these put entries failed the tested short completion window without
rejecting Pandar's longer-lived tail inventory program.

This audit is generated by `scripts/pandar_eligibility.py`; it uses the original source
features plus locally retained exact chain rows. Source hashes are in
[eligibility_sources.csv](eligibility_sources.csv). Run `scripts/pandar_richness.py`
for the cached matched-surface analysis and `scripts/pandar_entry_greeks.py` for the
cached execution snapshots. `scripts/pandar_call_exclusions.py --analyze` rebuilds the
alternative-contract audit from its 17 cached historical-chain batches and exports
the three corrected original-rule selections. `scripts/pandar_backfill_early_puts.py --confirm` reproduces
the early-put exact checks from the cached chains. The backfill used **90 additional
ORATS requests** under a separate allowance for this new scope; its request manifest
and source hashes are retained in `early_put_backfill/`. The preceding 414-request
ledger is preserved, making 504 recorded requests across the two scopes. No screening thresholds or earlier P&L rows were changed
to fit the new richness findings.

## Leg timing and modeled profits: original 81-qualification cohort
<!-- END ELIGIBILITY AUDIT -->

**Two MSTR call-grab examples produced profitable modeled leg-ins. The tested put-tail
entries did not produce a financed spread within the observed completion windows. Waiting
for the nearer call to cheapen helped; this sample does not establish that HIRO improved
timing.** These are one-contract historical bid/ask replays, not actual executed trades.

All times below are **America/New_York**. All option prices are dollars per share; P&L is
dollars per one-contract unit with the 100 multiplier and **$0.65 per contract transaction**.
A completed spread round trip therefore costs $2.60. No midpoint execution is assumed.

## The two useful call examples

Both use August 28 expiration. Qualification was available from the **preceding session's
EOD scan**. The first leg was sold at the next minute quote after a completed HIRO signal.

| Case | First leg | HIRO-confirmed second leg | Exit both legs | Net P&L |
|---|---|---|---|---:|
| MSTR 145/150C; qualified Aug 20 | Aug 21 **10:41**: sell 150C at **$0.61** | Aug 24 **13:24**: buy 145C at **$0.56** | Aug 26 15:50: sell 145C $0.10, buy back 150C $0.08 | **+$4.40** |
| MSTR 155/160C; qualified Aug 21 | Aug 24 **10:51**: sell 160C at **$0.26** | Aug 25 **11:27**: buy 155C at **$0.20** | Aug 27 15:50: sell 155C $0.12, buy back 160C $0.09 | **+$6.40** |

For the first case: ($0.61 − $0.56 + $0.10 − $0.08) × 100 − $2.60 = **$4.40**.
For the second: ($0.26 − $0.20 + $0.12 − $0.09) × 100 − $2.60 = **$6.40**.
The second leg arrived **one trading session after the first** in both cases; the first
case crosses a weekend. These are two overlapping observations of one ticker, not two
independent market regimes.

### Same day versus next day versus two days later

The first leg and final exit stay identical within each column. Each row below is a
separate counterfactual, not an additional trade to add to a portfolio total.

| Second-leg policy | 145/150C: purchase / net P&L | 155/160C: purchase / net P&L |
|---|---|---|
| Immediately with first leg | Aug 21 10:41, $0.95 / **−$34.60** | Aug 24 10:51, $0.47 / **−$20.60** |
| Same day, fixed 15:50 | Aug 21, $0.72 / **−$11.60** | Aug 24, $0.27 / **−$0.60** |
| Next session, fixed 15:50 | Aug 24, $0.57 / **+$3.40** | Aug 25, $0.16 / **+$10.40** |
| Two sessions later, fixed 15:50 | Aug 25, $0.45 / **+$15.40** | Aug 26, $0.15 / **+$11.40** |
| First price-only financing within +1 | Aug 24 09:46, $0.52 / **+$8.40** | **Aug 24 14:43**, $0.23 / **+$3.40** |
| First HIRO + price financing within +1 | Aug 24 13:24, $0.56 / **+$4.40** | Aug 25 11:27, $0.20 / **+$6.40** |

The second case could finance **the same day** at 14:43. An overnight requirement would
have missed that opportunity. Waiting two sessions paid more in these two paths, but
two observations cannot establish an optimal delay. Fixed +1 beat HIRO in the second
case; it was slightly worse in the first. Adding one extra cent of adverse execution
per transaction leaves the HIRO examples at **+$0.40 and +$2.40**. The same-day $3.40
example becomes **−$0.60** under that sensitivity.

### Retaining the source inventory's dime-credit target

The frozen primary test above accepted enough construction credit to cover fees. As a
separate **source-rule sensitivity**, I also checked the inventory's existing sale-minus-
$0.10 conversion formula, recalculated from the actual first-leg fill. This target came
from the supplied master, not a search over profitable parameters. It was evaluated after
the primary replay and does not replace that protocol or its summary table.

| Same first leg | First price-only dime opportunity | Dime target plus renewed HIRO exhaustion | Net P&L with HIRO completion |
|---|---|---|---:|
| Aug 21 10:41: sell 150C $0.61 | Aug 24 **14:39**, buy 145C **$0.50**; net **+$10.40** | Aug 25 **11:27**, buy 145C **$0.50** (+2 sessions) | **+$10.40** |
| Aug 24 10:51: sell 160C $0.26 | Aug 25 **09:35**, buy 155C **$0.15**; net **+$11.40** | Aug 26 **11:45**, buy 155C **$0.04** (+2 sessions) | **+$22.40** |

The exits remain Aug 26 and Aug 27 at 15:50, respectively, using the exit quotes in the
first table. The source-target HIRO versions retained **$0.11 and $0.22 gross construction
credits**, and survive the extra one-cent-per-transaction sensitivity at **+$6.40 and
+$18.40**. Neither received a HIRO-confirmed dime fill by the +1 deadline; those deadline
variants instead closed the original short. Their profits must not be called completed
spreads.

This supplies the clearest **two-days-later second-leg examples using the master target**.
In the 155/160 case, the nearer call bought for $0.04 subsequently caught part of the
Aug 27 rally. Conversion beat simply covering the short at conversion time by only
**$0.70**, which disappears with one extra cent on the two additional transactions.
The 145/150 conversion underperformed that cover alternative by $19.30. These results
strengthen the case-study inventory without establishing incremental HIRO or conversion
edge. [Every dime-target attempt](source_dime_target_sensitivity.csv).

![Second-leg timing comparison](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_leg_timing_2026-09-05/call_timing_comparison.png)

### What HIRO actually showed

The entry rule required 15-minute **call HIRO to turn negative after a positive preceding
15-minute interval**, with price below its preceding 15-minute low. It was evaluated on
five-minute decision timestamps after 10:00; execution used the following minute quote.

| Observation before execution | Stock | Latest 15m All Trades Total | Latest 15m call | Latest 15m put | RTH accumulated Total |
|---|---:|---:|---:|---:|---:|
| Aug 21 10:40: first 150C sale trigger | $118.635 | −$10.97m | −$6.79m | −$4.17m | **+$34.92m** |
| Aug 24 13:23: 145C purchase trigger | $122.09 | −$7.04m | −$6.05m | −$0.99m | −$1.09m |
| Aug 24 10:50: first 160C sale trigger | $124.68 | −$23.05m | −$17.92m | −$5.13m | **+$52.60m** |
| Aug 25 11:26: 155C purchase trigger | $125.71 | −$3.42m | −$5.13m | +$1.71m | **+$51.94m** |

The accumulated line was still positive at both initial sales. The actionable hypothesis
was **new call pressure fading while price broke a recent low**, not “daily HIRO is
negative.” At the second case's completion, put selling offset some call selling; Total
alone concealed that difference. HIRO estimates delta-notional pressure, not observed
dealer executions or gamma inventory. Its rolling measure sums new pressure over time;
call and put lines are separate components. [SpotGamma rolling-window explanation](https://support.spotgamma.com/hc/en-us/articles/50265906309907-What-does-the-Rolling-Window-setting-do-on-the-HIRO-chart),
[SpotGamma Put/Call explanation](https://support.spotgamma.com/hc/en-us/articles/12284010265363-What-does-the-Put-Call-HIRO-Stock-Chart-indicate).

![145/150 call timeline](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_leg_timing_2026-09-05/MSTR_145_150_timeline.png)

![155/160 call timeline](/Users/dgrissen/Dev/delta_bomb/docs/replay/pandar_leg_timing_2026-09-05/MSTR_155_160_timeline.png)

### Where the money came from

Holding only the original short call to the same exit would have earned **$51.70 and
$15.70** after its two transaction fees. Simply covering that short at the HIRO conversion
time would have earned **$21.70 and $11.70**. Conversion plus subsequent spread ownership
therefore earned **$17.30 and $5.30 less** than closing at that time.

Buying the nearer call acquired the remaining upside spread and bounded the remaining
position. It was a use of already-earned short-call profit. The observed call premiums
contracted even as stock observations rose between entry and exit. This replay does not
separately attribute that contraction to IV changes versus passage of time.

The worst sampled unpaired liquidation P&L was **−$36.30 and −$21.30**. Those are historical
minute observations, not maximum losses: the initial naked short call has unbounded
upside exposure until conversion or cover. The second case's long-call exit bid displayed
only **one contract**. These unit results do not establish scalable execution or returns
on margin. No account-size or portfolio-return claim is made.

## What happened to the put inventory

The 75 confirmed put rows reduce to **57 distinct strike-pair episodes**. Thirty-six have
HIRO on the next-session entry date; **27** passed both calm HIRO and live cheap-spread
quote gates. The primary put rule bought the higher put while rolling put HIRO was
positive and stock was stable/rising, then sought a bid for the lower put sufficient to
cover the first purchase and all four fees.

- **18 entries have the complete two-session financing window. Zero financed.**
- Nine more entries reach the September 4 cutoff before that deadline. None financed
  in the available portion; their later outcomes are unknown.
- Price-only and price-plus-HIRO financing produced the same result because the price
  condition itself never passed. The stricter flow gate had no financing opportunity
  to improve.
- With complete observation horizons, the failed financing attempts averaged **−$5.74**
  when closing the long the same day, **−$5.52** at +1, and **−$6.47** at +2.
- Immediate completed put spreads had **zero positive forced bid/ask exits among 27**
  available marks, of which 18 had full exit horizons. Fixed +2 completion had 14 priced
  exits and zero winners; the rest were unpriced or censored.

A useful near-miss is **PLTR September 18 125/120P**, qualified Aug 27. Calm HIRO allowed
buying the 125P on Aug 28 at 10:26 for $0.15. Selling that long at the common Sep 2 15:50
exit produced **+$0.70** after fees; the lower put never financed within two sessions.
That was an outright-put result, not a profitable completed inventory trade. Its best
later minute liquidation mark was $8.70, but selecting that time after the fact would
not be an entry/exit rule. Another $0.70 clock-entry BMNR long-put exit likewise was an
uncompleted leg and disappears under the one-cent slippage sensitivity.

**This does not reject Pandar's broader put-tail program.** The experiment tests fast
legging and near-term monetization of the inventory. These September/October contracts
have not completed their tail-insurance life cycle. Cheap, distant protection can remain
unprofitable across a short window without testing its crash payoff.

Some put-spread liquidation quotes imply paying to close a spread whose expiration
payoff cannot be negative. The ledger retains those literal leg-crossing costs as an
**execution-friction diagnostic**. Do not interpret losses beyond initial debit plus
fees as the vertical's contractual maximum risk. Declining that uneconomic close leaves
an open position; assigning it a zero-value expiry exit today would not be an observed
execution either.

## Does HIRO add value here?

On the **same two MSTR contracts**, entering the first short at the fixed 10:01 clock
and closing at the common exit would total **$77.40**, versus **$67.40** after waiting
for the HIRO entry. HIRO helped one entry by $4 and hurt the other by $14. Among the
17 put episodes with both entry modes, it improved the aggregate standalone result by
only **$4**, about **$0.24 per episode**; both cohorts still lost money overall.

That comparison controls for changing membership. A three-call clock sample contains
one early episode with unavailable HIRO and must not be compared directly with the
two-call HIRO sample as evidence of filtering skill.

The practical research rule supported by these examples is: **use a prior-session rich
call screen, watch for a local call-flow rollover, then let the actual nearer-call ask
determine whether conversion is affordable.** A positive daily cumulative reading does
not prevent a rollover. Completing merely because a new day began is not supported by
the two cases. Neither is requiring fresh HIRO confirmation after the premium target
is already available. Closing the first short belongs alongside conversion as a primary
comparison because it captured more of the observed profit.

This is a candidate rule to keep frozen for subsequent observations, not a validated
deployment recommendation. The saved Brent persona explicitly vetoes deploying the naked
short phase and cannot validate gamma terrain from HIRO alone.

## Coverage, attribution and audit

| Scope | Original rows | Distinct pairs | Next-session HIRO available, distinct | HIRO entries, distinct |
|---|---:|---:|---:|---:|
| Buy-first put-tail inventory | 75 | 57 | 36 | 27 |
| Sell-first call grab | 6 | 6 | 5 | 2 |

All original rows remain in the ledger. Across both entry modes and the frozen policies,
the replay contains **891 counterfactual rows**, not 891 independent trades. Earlier
signal-day entries were not permitted because the screen uses EOD information. Primary
deduplication keeps the earliest appearance of each ticker/expiry/strike pair, even when
that date lacks HIRO. Different pairs on the same stock can still overlap and correlate.

Data: 111 exact-contract ThetaData histories, 1-minute NBBO, through Sep 4; 122 available
individual-stock HIRO sessions across 24 names, reconstructed from immutable capture
files. The screen-day audit at 15:50 confirms a $0.10-or-less put debit in 60 of 75 rows;
the median matches the screen at $0.05. It is a different observation time from ORATS,
so individual quote differences do not by themselves establish provider error.

The narrow Pandar-direct portions are cheap put-tail inventory and the rich call-tail
sale/crush core. **HIRO thresholds, first-entry delays, financing targets, systematic
call conversion, fixed deadlines, costs and exits are project-derived research choices.**
The [source strategy memory](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/strategy_names.md)
is authoritative on those attribution boundaries. No excluded call-puke or call-standard
strategy was introduced.

- [Frozen protocol](PROTOCOL.md) and [Charlie/Brent review](PERSONA_REVIEW.md)
- [Profitable HIRO cases](profitable_hiro_cases.csv) and [call timing alternatives](call_timing_comparison.csv)
- [All attempts](all_attempts.csv), [summary](summary.csv), [coverage](coverage.csv), and [entry eligibility](entry_eligibility_audit.csv)
- [Paired entry comparison](paired_entry_comparison.csv), [screen quote comparison](screen_quote_comparison.csv), [source dime-target sensitivity](source_dime_target_sensitivity.csv)
- [HIRO source paths and hashes](hiro_sources.csv), local `quote_manifest.json`, and `data/`

Reproduction from `/Users/dgrissen/Dev/delta_bomb`: run `scripts/pandar_quote_history.py`
using the existing ThetaData subscription if the local quote cache is missing, then
`scripts/pandar_leg_timing.py` and `scripts/pandar_leg_timing_report.py` with
`/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python`. The added eligibility audit is
rebuilt with `scripts/pandar_eligibility.py` after the cached richness/Greek calculations.
Eighteen tests cover replay causality, surface matching, exact-contract/delta handling,
and alternative-call selection. Ruff passes. The frozen 917-row inventory is retained;
the complete-window inventory includes the early puts and three recovered call selections. The
vectorized minute-liquidation calculation reproduced the original
loop's entire 891-row result. All quoted fills remain modeled from
displayed snapshots; quote freshness, queue position and actual execution are unverified.
