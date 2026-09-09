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

Under the original project surface gates, there are **{{total_rows}} ticker/date
surface candidates: 24 call-grab rows and
{{put_rows}} put-inventory rows**. After auditing alternative call contracts, exact-chain
checks retain **{{total_exact}} rows: {{call_exact}} calls across COIN, LRCX and MSTR,
and {{put_exact}} puts**. The original one-contract selector retained only MSTR;
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

{{daily}}

### Why the earlier put days were missing—and the correction

**This was an inherited research-scope omission, not a lack of eligible puts.** The
master combined an August 11–27 call scan with a later four-method scan whose put start
date was August 24. That later run described the put coverage as an extra week added
to its August 28–September 2 call window. The master retained those date boundaries
instead of scanning both Pandar-style families over the full window. I then carried
the omission into this report rather than closing it. [Earlier scan's date scope](/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/replay/hiro_daily_four_methods_2026-08-24_to_2026-09-02/README.md:24).

The **nine omitted sessions, August 11–21, have now been scanned** with the same
recorded put rules. They added **{{early_rows}} surface-qualified ticker/date rows and
{{early_exact}} exact-chain confirmations**. The daily table and all-candidate appendix
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
The [{{total_rows}}-row complete-window CSV](pandar_eligibility_complete_window.csv) also includes raw surface
values, trend/liquidity/earnings fields and available contract details. The
[{{total_exact}}-row exact-leg CSV](pandar_exact_legs_complete_window.csv) includes both legs' Greeks and
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

{{expanded_call_search}}

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

{{calls}}

The table now includes the three recovered alternative-contract passes. Remaining
failures preserve the original selected-contract reason; the exhaustive audit and
separate filter sensitivities above explain the scope of those rejections.

### All nine exact call qualifications: % OTM and both deltas

The first strike is the **short farther call**, the second the **prospective long nearer
call**. Delta below is the positive **option** delta ×100, not signed position delta:
selling a 4Δ call creates approximately −4 shares of position delta per contract.
Moneyness for calls is `100 × (strike / stock − 1)`.

{{call_legs}}

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

{{richness}}

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

{{executions}}

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

All {{put_exact}} confirmed put rows follow, including the {{early_exact}} newly backfilled rows.
Each satisfied IVR ≤35, local RR rank ≤50,
put-skew rank ≤25 and the recorded exact-quote gates. `% OTM = 100 × (1 − strike / stock)`.
The first strike is the higher **buy** put; the second is the lower **sell** put.

**Put delta convention:** the source's `leg1_delta` is ORATS's call-coordinate delta,
often near 0.99 for these strikes. Printing it as a +99Δ put would be wrong. The tables
show the approximation **put option delta = call-coordinate delta − 1**, multiplied by
100; the CSV retains both raw coordinates and the conversion label. These are model
approximations, not independently supplied American-put Greeks. A short put reverses
the displayed option-delta sign at the position level.

{{puts}}

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
