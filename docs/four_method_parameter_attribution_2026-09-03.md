# The four single-name trades: what Pandar, Charlie, and Brent actually support

Date: 2026-09-03

## Bottom line

There is no honest “three experts agree on one parameter card” answer.

- **Pandar directly owns the buy-first put-tail inventory concept and the sell-first call-tail first leg.** His call-puke comments are real but sparse. He did **not** document the 15-delta buy-first call standard method.
- **The exact Charlie numbers in this project are a Charlie McElligott-persona synthesis**, built from Pandar’s notes, the Delta Bombs white paper, and our NVDA replay. Direct published McElligott material validates the flow logic—crash-up, dealer hedging, overwriter squeezes—but not our DTE/delta thresholds.
- **Brent supplies the surface, tenor, gamma, and flow discipline.** He does not prescribe Pandar’s penny-spread inventory or our naked 4-delta call conversion. His explicit risk rule is fixed-risk, which conflicts with the naked phase of sell-first call grab.

The exact current project cards are therefore **our best-supported synthesis**, not co-signed prescriptions from all three.

## The working cards

Premiums below are quoted per share; multiply by 100 for one standard option contract.

| Method | Entry ticket | Exactly what Pandar supports | “Complete” means | Expected clock | Monetization target |
|---|---|---|---|---|---|
| **Buy-first call puke** | Buy complete 20–35%-OTM, 30–90 DTE bull-call spread; approximately $5 wide. Pandar-style price is near or below $0.10; the current research scanner permits $0.05–$0.50. | **Direct:** he bought call spreads on large down days in NVDA/SPX and bought farther-out call spreads as protection against a 15–20%+ upside year. **Borrowed from his put book:** penny pricing, roughly $5 width, and maintaining cheap convexity as inventory. **Not Pandar:** the fixed 20–35% OTM and 30–90 DTE ranges, the $0.05–$0.50 scanner band, the immediate-complete requirement, the rebound clock, and 2×/3×/5× exits. | The vertical exists immediately; there is no second-leg risk. | Rebound inventory: days to roughly two weeks, not an intraday plant. | Rest 2×/3×/5× of debit. A $0.10 spread means $0.20/$0.30/$0.50. |
| **Buy-first call standard** | Buy roughly 10–15Δ, 30–60 DTE lower call; rest the adjacent upper-call sale at original cost +$0.10. Use +$0.25 only for the strongest tier. | **Direct:** only the broad ideas that calls can sometimes be cheap and that call spreads can hedge an upside year. **Not Pandar:** buying a 10–15Δ naked call first, 30–60 DTE, the adjacent upper-call sale, cost +$0.10/+$0.25, the 1–5-session completion window, $1/$2/$3 exits, and the price/time stops. This method is the white-paper mirror plus our Charlie/replay overlay. | The upper call sells, leaving a bull-call spread for zero cost or a credit. | The NVDA replay’s useful window was 1–5 sessions; the spread generally peaked 1–2 weeks later. | For a $5-wide vertical, scale around $1/$2/$3—20%/40%/60% of width. Do not use a percentage return once cost basis is zero/credit. |
| **Sell-first call grab** | Historical/P1 form: sell a 2–6Δ call in the nearest 5–12 DTE, fallback through 19; rest one-strike-nearer call buy at sale −$0.10, with a $0.10 price floor. | **Direct:** sell far OTM front-weekly calls only when that specific call tail is overpriced; on 2025-01-31 he chose Feb-7 190C+ and expected a large post-weekend crush. He deliberately remained naked and sized so a move to 190 would stay inside his margin/PNR cushion and could be held to expiry. He also supports the general expanded-tail → cheaper nearer-leg → low-cost/free-spread process. **Only Pandar-derived:** applying that conversion systematically to calls; the clearest actual call conversion was another trader’s. **Not Pandar:** 2–6Δ/nearest 4Δ, 5–12 DTE/fallback 19, bid/width/OI filters, sale −$0.10, five-session evaluation, and the breakout override. | The nearer call buys and caps the short, ideally leaving a $0.05–$0.10 credit plus the bull-call spread. | Expected hours to a few days; five sessions is the research evaluation window, not a proven fill statistic. | Completion credit is the first objective. There is no validated post-fill spread multiple. |
| **Buy-first put-tail inventory** | Buy complete current/next-monthly put spread, normally about $5 wide and ≤$0.10. The project scans 25–45% OTM; Pandar actually chose black-swan-reachable strikes rather than a fixed delta. | **Direct:** 1:1 put verticals; usually roughly $5 wide and under $0.10; normally the next two monthly expirations; ladder “reasonable” black-swan-reachable strikes rather than choose by delta; accumulate during calm/complacency and over time; exploit roughly weekly expansion/crush cycles; take any small gain when inventory is already large; as DTE falls, sell for the smallest feasible loss and replace farther out. **Important difference:** Pandar personally often bought the long put first and legged the short later—he did not require an immediately complete vertical—and recommended sell-first as safer for most traders. **Not Pandar:** the fixed 25–45% OTM band, mandatory complete-at-entry execution, and universal 3×/5× exits plus a residual. | The project vertical exists immediately. Pandar’s actual long-first version could remain unpaired; the *book* takes weeks/months to accumulate. | Buy during calm/euphoria; recycle around weekly vol expansion/crush; hold residual inventory as a hedge or roll before expiry decay dominates. | Pandar often took any small gain when inventory was already large. The project operationalizes 3×/5× scale-outs; a fully ITM $5 spread bought for $0.10 is 50×, but that is tail payoff, not the routine target. |

## One metric warning before using any RR number

The repository’s historical screen defines risk reversal as:

> local RR = 25Δ put IV − 25Δ call IV

SpotGamma officially defines it in the opposite direction:

> Compass RR = 25Δ call IV − 25Δ put IV

SpotGamma therefore says **high official RR = calls rich** and **low official RR = calls cheap**. The old local ranks read the other way. As a rough translation, local RR rank 80 is official RR rank 20, although ties and lookback details prevent treating the ranks as exact complements. This is confirmed in the [SpotGamma Compass User Guide](https://spotgamma.com/wp-content/uploads/2025/03/SpotGamma-Compass-User-Guide.pdf).

| Method | Old local RR gate | Approximate official-Compass reading |
|---|---:|---:|
| Buy-first call puke | ≥60 | ≤40: calls relatively cheap |
| Buy-first call standard | ≥60 / ≥80 / ≥90 by tier | ≤40 / ≤20 / ≤10: progressively cheaper calls |
| Sell-first call grab | ≤10 | ≥90: calls relatively rich |
| Buy-first put-tail inventory | ≤50 | ≥50: puts relatively cheap to calls, then confirm with low put-skew rank |

## 1. Buy-first call puke

### What Pandar supports

Pandar explicitly said he bought call spreads on large down days when upside protection was cheap, including farther-out calls as a hedge against a strong year. He did not give a fixed call DTE, delta, or percent-OTM rule in the transcript. His better-documented put practice supplies the price/width DNA: narrow spreads, often about $5 wide, bought for pennies, in a highly liquid chain that repeatedly expands and crushes. See the [Pandar transcript](sources/discord_transcript_clean.txt#L494) and the later [call/put discussion](sources/discord_transcript_clean.txt#L639).

The key correction is that **20–35% OTM and 30–90 DTE are our mechanization**, not a verbatim Pandar rule. The unified review says this plainly: [Pandar-style, not Pandar-exact](replay/hiro_daily_2026-08-11_to_2026-08-27/three_call_methods_charlie_analysis.md#L79).

The best high-fidelity ticket is:

- complete vertical at entry;
- about $5 wide when the strike grid supports it;
- 20–35% OTM and 30–90 DTE as the current project search envelope;
- **≤$0.10 as A-grade Pandar fidelity**; $0.11–$0.50 is the broader research lane;
- buy only after forced selling, not because a cheap far call always deserves to be owned.

### What Charlie says

The project’s Charlie review requires an actual puke: at least 8% below the 20-day high and a negative five-day return, with cheap calls on the local RR/call-skew surface. It buys the complete spread, so the position is defined-risk immediately, and scales around 2×/3×/5×. Those exact rules are in the [unified Charlie analysis](replay/hiro_daily_2026-08-11_to_2026-08-27/three_call_methods_charlie_analysis.md#L79).

Direct McElligott research supports the *why*, not the ticket. His “spot up, vol up” work shows that upside-call demand can force dealers and call overwriters to buy into a rising market—the right-tail crash-up that cheap puke-day calls hedge. His public Nomura deck also shows why selling calls mechanically can be dangerous once overwriters are being forced to cover ([Nomura Overwriting Analytics](https://www.nomuranow.com/portal/static/common/images/email-headers/vow23/charlie-mcelligott.pdf)).

### What Brent says

Brent does not give a 20–35%-OTM, 30–90 DTE puke-spread prescription. His applicable rules are:

- buy calls when they are cheap in both absolute IV and relative skew—not merely because spot fell;
- use roughly two weeks to one month as the cleanest surface anchor; one week is noisy and liquidity thins beyond about 30 days in many names ([December 2025 SpotGamma session](https://spotgamma.com/optimizing-credit-spread-selling-strategies-using-spotgamma-compass-and-implied-volatility-insights/));
- match the trade to EquityHub gamma/key levels and real-time flow. HIRO/price divergence can identify mean reversion, while a break into negative gamma can turn a dip into acceleration ([SpotGamma HIRO guide](https://spotgamma.com/real-time-options-flow-hiro-indicator-can-help-0dte-traders/)).

For this method, Brent is best used as a **location veto**: prefer a puke into meaningful support with flow stabilizing; do not mistake a negative-gamma air pocket for an automatic V.

### Completion and exits

The ticket is complete immediately. The relevant clock is monetization. Our NVDA reconstruction found the strongest complete puke spreads monetized during the next several sessions through roughly two weeks; 2×/3×/5× scale-outs fit the nonlinear payoff. This is replay evidence, not a Pandar or Brent statistic.

## 2. Buy-first call standard

### What Pandar supports

**Pandar does not document this method.** He bought complete penny call spreads on down days and sold rich front-weekly calls into grabs. The structure “buy a 15Δ call for dollars, then wait to sell the next strike” came from the white paper’s call-side mirror and our NVDA replay, not his thread. The [provenance correction](delta_bombs.html#L719) is decisive here.

### What the white paper actually says

The white paper specifies 20–40 DTE, a narrow five-point spread, and an entry around one standard deviation OTM. Its study says successful two-leg plants completed in roughly seven minutes, while failed plants were held around 60 minutes before exit. For 57 closed five-point spreads, the median exit was $1.45; $2.90 was offered as a reasonable standing exit, with outliers near $3.90. See the [white-paper text](sources/delta_bombs_white_paper.txt#L91).

Those numbers are mostly an **SPX put-side/intraday sample**. They cannot be transplanted to single-name calls as if NVDA also completes in seven minutes.

### What Charlie says

The project’s Charlie card is:

- lower call at 10–15Δ;
- 30–60 DTE monthly;
- adjacent upper call—often $5 higher in NVDA;
- rest the sale immediately at long-call cost +$0.10;
- +$0.25 only in the strongest surface/technical tier;
- constructive trend: above the 200-day, not excessively above the 50-day, positive relative strength;
- price stop on a close below the 50-day;
- absolute time stop at half the remaining DTE.

The 2026 NVDA replay found that the best zone was usually **7–12% OTM and 25–35 DTE**, with the upper sale filling on the first gap/ripping morning in **1–5 sessions**. Farther strikes—17–24% OTM—or 50+ DTE often completed too, but their verticals generally had less pop. The completed spread commonly peaked 1–2 weeks later, and many later expired worthless. See the [replay synthesis](delta_bombs.html#L709).

For a five-point vertical, the practical scale is $1/$2/$3. That is 20%/40%/60% of width. It is more intelligible than “X times return” because the leg-in aims to make the net cost zero or a credit.

### What Brent says

Brent’s direct tenor discussion aligns most closely with this method: a 30-day surface is a useful anchor, around two weeks may work in modern single-name options, one week contains too much noise, and trading interest often falls beyond 30 days. He also stresses decomposing RR into call-versus-ATM and put-versus-ATM skew instead of treating RR alone as proof that calls are cheap.

That supports a **roughly one-month liquid call** and a surface check; it does not independently validate 15Δ, an adjacent $5 short, cost +$0.10, or the 1–5-session clock.

Brent’s gamma overlay should decide placement:

- long call near support/positive flow, not directly beneath a hard call wall;
- treat a call wall as a plausible upper-leg/monetization zone;
- if spot loses support into negative gamma while the long is still unpaired, exit rather than wait for the calendar.

### Completion and exits

Use two clocks:

1. **Plant clock:** one to five sessions is the observed useful NVDA window. Beyond that, the position is increasingly just a decaying long call. The half-DTE rule is an outer boundary, not permission to ignore a failed first week.
2. **Spread clock:** once paired, rest $1/$2/$3 exits immediately and favor the first local top over expiry. The replay’s repeated “later zero” outcome makes hold-to-expiry a poor default for alpha inventory.

## 3. Sell-first call grab

### What Pandar supports

Pandar’s January 31, 2025 NVDA example is explicit: one front weekly was unusually overpriced, he sold 190C and higher, expected a large post-weekend crush, and sized the naked calls so a move to the strike would remain inside his portfolio-margin safety boundary. He also generally preferred shorter than 26 DTE for tails and later said weeklies through the next monthly crush fastest. See the [January call-tail exchange](sources/discord_transcript_clean.txt#L276) and [weekly-expiry guidance](sources/discord_transcript_clean.txt#L730).

But Pandar also said he was **only selling naked calls in that episode**, not buying the lower call. The clearest documented call conversion belongs to another participant. The whole sell-and-convert cycle is therefore Pandar-derived, not a fully documented Pandar call recipe.

### What Charlie says

The project’s exact one-sided-grab card is:

- front 5Δ call-wing rank ≥85;
- front-versus-30-day kink rank ≥70;
- old-local RR rank ≤10, approximately official Compass RR ≥90;
- IV Rank 30–70;
- positive five-day return and within 5% of the 20-day high;
- no earnings event inside the sold expiry;
- nearest 5–12 DTE, fallback through 19 DTE;
- sell the 2–6Δ call nearest 4Δ;
- require bid ≥$0.20, quote width ≤$0.10, OI ≥25, and call IV at least two vol points above same-expiry ATM;
- immediately rest the adjacent lower-call buy at sale −$0.10, floored at $0.10;
- if wing rank keeps rising while spot moves at least another 5% toward the strike, cover or cap and stop adding.

These exact rules are in the [Charlie/P1 analysis](replay/hiro_daily_2026-08-11_to_2026-08-27/three_call_methods_charlie_analysis.md#L116). Five sessions is a **research fill window**, not an established success probability.

Direct McElligott research is actually the strongest warning against careless use. His Nomura work documents “crash-up” conditions in which systematic call sellers are forced to cover as upside calls acquire delta. That is precisely the path that can destroy a naked short call before a resting nearer-call buy ever fills.

### What Brent says—and where he disagrees

Brent’s direct rule is to sell rich volatility through **defined-risk credit spreads, not naked options**. When call skew was extreme in a broad equity chase, he sold approximately one-month 25Δ call spreads and expected consolidation to develop over the following week, while explicitly avoiding crypto/COIN-like names where a 10% move could run over the position. That is a slower, safer, less tail-sensitive trade than our 4Δ front-weekly grab.

On September 2, 2026, he gave an event-specific example with AVGO at official RR rank 97: sell the front-weekly 400C and buy the following week’s same-strike 400C for about a $1.40 debit, targeting the expected 15–20-vol-point earnings crush. That is a **calendar completed at entry**, not our naked sell-first conversion ([SpotGamma recap](https://spotgamma.com/how-options-positioning-could-limit-a-major-selloff/)).

So there are two non-equivalent implementations:

| Version | Structure | DTE/delta | Completion | What it bets on |
|---|---|---|---|---|
| Pandar/Charlie research form | Naked far-call sale, then nearer-call buy | 2–6Δ, 5–12 DTE; fallback 19 | Hours to a few days; research window ≤5 sessions | Far front wing crushes faster than spot approaches |
| Brent-compliant form | Call credit spread or front/back calendar, both legs placed together | His cited skew sale was about one month/25Δ; event calendar used adjacent weeklies | Immediate | Rich skew or front-event IV normalizes with capped loss |

### Completion and exits

For the Pandar/Charlie form, the target is not “spread up 3×.” It is:

1. sell the far call for enough premium to matter;
2. buy the nearer call for $0.05–$0.10 less than that sale;
3. retain the resulting credit and defined-risk vertical;
4. treat the vertical’s later value as optional convexity, not as a validated expected return.

There is no robust post-fill multiple in the evidence. A May 2026 reconstruction sold a far call at $0.62 and could buy the nearer call around $0.38–$0.40 four sessions later, retaining roughly $0.22–$0.24 plus the spread. That is an example, not a target distribution.

## 4. Buy-first put-tail inventory

### What Pandar supports

This is the method with the strongest Pandar fidelity. His direct rules are:

- buy 1:1 verticals, typically about $5 wide;
- normally pay less than $0.10;
- own a ladder of reasonable strikes rather than pretending to know the exact crash landing zone;
- choose strikes capable of becoming relevant in a black-swan-like move, not by a fixed delta;
- usually work in the next two monthly expirations, although actual inventory was sometimes accumulated months ahead;
- buy during calm/complacency and over time, not after a large decline has already made protection expensive;
- exploit a liquid, tight chain that repeatedly cycles between tail expansion and collapse;
- when lower DTE approaches, sell for the smallest feasible loss and replace farther out;
- if inventory is already large, accept any small gain; otherwise keep convexity available for the rare large payout.

The direct evidence is concentrated in the [December construction discussion](sources/discord_transcript_clean.txt#L46), [price/width and exit discussion](sources/discord_transcript_clean.txt#L110), [strike selection](sources/discord_transcript_clean.txt#L245), and [calm-market sequencing](sources/discord_transcript_clean.txt#L333).

Two nuances matter:

1. The project ticket buys the complete spread at once. Pandar personally often bought the long put first and later sold the lower put, although he repeatedly said the safer/more reliable path for most people was the opposite—sell a small tail first and buy the nearer put after a crush.
2. Pandar did not set a universal 3×/5× profit rule. He sometimes sold for any small gain when his book was already full. The 3×/5× scale is our way to mechanize the inventory, not a direct quote.

### What Charlie says

The project’s Charlie-style operational card narrows Pandar’s qualitative strike choice into:

- low IV Rank, low put-skew rank, and puts cheap relative to calls;
- current and next standard monthly;
- 25–45% OTM;
- approximately $5 wide;
- ≤$0.10 debit;
- standing 3× and 5× scale-outs, with residual inventory rolled or retained as the hedge.

Direct McElligott material supports accumulating convexity when volatility is crushed and positioning is crowded, because calm conditions can seed the next instability. It does not supply the 25–45% band, ten-cent cap, or 3×/5× ladder.

### What Brent says

Brent’s closest direct example is tactical rather than permanent tail inventory. In January 2026, with correlation at an extreme and options relatively cheap, he bought one-to-two-month SPY puts and discussed put spreads/VIX call spreads. He expected the corrective catalyst within one to two weeks and said he almost certainly would not hold to expiration. He preferred outright puts in his own small allocation to retain vega if volatility spiked, while saying the put spread probably made more economic sense. See the [January 26 SpotGamma session](https://spotgamma.com/spotgamma-market-insights-elevated-volatility-single-stock-correlation-extremes-and-strategic-put-spread-setups-ahead-of-fomc-and-earnings/).

Compass supplies the clean screen translation: **low IV Rank + high official RR Rank** means options are cheap overall and puts are cheap relative to calls, a sensible region to investigate put purchases. But Brent then requires a catalyst and positioning map. On September 2, he explicitly said substantial positive gamma below spot limited near-term downside; a break into negative gamma would change the read. That is why cheap puts alone are not a timing signal.

### Completion and exits

The current ticket is complete immediately, but the *inventory program* is deliberately slow. Pandar described waiting for good prices, building over time, and then trading the book about weekly as vol ebbed and flowed.

Use three monetization lanes:

- **Book already full:** take small gains to recycle cost, consistent with Pandar.
- **Normal shock:** project scale-outs at 3×/5×. For $0.04 debit, those are $0.12/$0.20; $0.30 is 7.5× and should be treated as an opportunistic overshoot, not the baseline objective.
- **True tail:** retain a small residual for the width payoff. A $5 vertical bought for $0.10 can theoretically reach 50×, but Pandar himself described spectacular percentage gains as materially luck-dependent.

## What I would freeze as the research specification

This is the most defensible consolidated specification—not personal investment advice and not a claim of proven expectancy.

| Method | Freeze | Do not claim |
|---|---|---|
| Buy-first call puke | Complete 20–35% OTM, 30–90 DTE, roughly $5 wide; tag ≤$0.10 as A-grade; scale 2×/3×/5× | That Pandar or Brent chose these exact ranges |
| Buy-first call standard | 10–15Δ, 30–60 DTE monthly; adjacent upper at cost +$0.10; expect ≤5 sessions; $1/$2/$3 exits on $5 width | That the white paper’s seven-minute statistic applies to NVDA |
| Sell-first call grab | Keep the 2–6Δ/5–12 DTE card only as a research variant with mandatory breakout cap; create a separate defined-risk Brent variant | That the naked phase is “free,” or that a five-session fill rate is known |
| Buy-first put-tail inventory | Complete current/next monthly, black-swan-reachable/25–45% OTM, about $5 wide, ≤$0.10; 3×/5× plus residual | That 3×/5× came from Pandar, or that every cheap penny spread is useful |

## Evidence limits

- Pandar’s record is a Discord transcript and examples, not a controlled backtest.
- The white paper’s timing and exit distribution are SPX-dominant and do not establish single-name call performance.
- The “Charlie” exact tickets are simulated persona work inside this repository, not Nomura-authored recommendations.
- Brent’s direct material supports different structures in several places; his generic 30–40% profit targets in Compass examples are for other trades and should not be copied into these four.
- Our 2026 NVDA replay is historical and selection-sensitive. It shows path mechanics, not out-of-sample expectancy.

## Primary sources consulted

- [Local Pandar transcript](sources/discord_transcript_clean.txt)
- [Delta Bombs white-paper extraction](sources/delta_bombs_white_paper.txt)
- [Unified Charlie call-side analysis](replay/hiro_daily_2026-08-11_to_2026-08-27/three_call_methods_charlie_analysis.md)
- [NVDA replay and attribution audit](delta_bombs.html)
- [SpotGamma Compass User Guide](https://spotgamma.com/wp-content/uploads/2025/03/SpotGamma-Compass-User-Guide.pdf)
- [SpotGamma: Optimizing Credit Spread Selling](https://spotgamma.com/optimizing-credit-spread-selling-strategies-using-spotgamma-compass-and-implied-volatility-insights/)
- [SpotGamma: Correlation Extremes and Put-Spread Setups](https://spotgamma.com/spotgamma-market-insights-elevated-volatility-single-stock-correlation-extremes-and-strategic-put-spread-setups-ahead-of-fomc-and-earnings/)
- [SpotGamma: September 2, 2026 Brent recap](https://spotgamma.com/how-options-positioning-could-limit-a-major-selloff/)
- [SpotGamma HIRO trade-flow guide](https://spotgamma.com/real-time-options-flow-hiro-indicator-can-help-0dte-traders/)
- [Nomura Vol: Overwriting Analytics](https://www.nomuranow.com/portal/static/common/images/email-headers/vow23/charlie-mcelligott.pdf)
- [MacroVoices: direct Charlie McElligott interview](https://www.macrovoices.com/podcast-transcripts/1104-charlie-mcelligott-is-there-another-shoe-to-drop-for-equities)
