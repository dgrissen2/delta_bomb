# Charlie McElligott’s three-method call-side verdict

## Bottom line

These are three different strategies. They are not Good, Better, and Best versions of one call trade.

They can use the same surface vocabulary, but they enter opposite regimes, take different first-leg risks, and need different events to make money.

1. **Buy-first call puke:** buy a tiny, complete bull-call spread after a selloff as right-tail rebound inventory.
2. **Buy-first call standard:** buy a directional call in a constructive trend, then try to sell the next strike into a chase.
3. **Sell-first call grab:** sell an overpriced front call tail, then try to buy the adjacent nearer call after the grab collapses.

The shortest accurate identities are:

- Puke = **defined-risk convexity inventory**.
- Standard = **directional long-call execution alpha**.
- Sell-first = **short-volatility grab fade with a hoped-for convex residual**.

## The decision map

| What the tape is saying | First action | Durable method |
|---|---|---|
| The stock has puked and upside is priced as implausible | Buy the complete cheap spread | Buy-first call puke |
| The trend is intact, calls are cheap, and a chase may arrive | Buy the lower call | Buy-first call standard |
| The stock is ripping and the front call wing is being grabbed | Sell the far call | Sell-first call grab |

## Detailed three-way comparison

| Dimension | Buy-first call puke | Buy-first call standard | Sell-first call grab |
|---|---|---|---|
| Core purpose | Accumulate cheap right-tail convexity after a selloff: the “what if we moon?” hedge. | Exploit a prospective repricing window and use a rip to finance a vertical. | Monetize temporary right-tail demand and, if the buy fills, retain a credit-carried bull spread. |
| Provenance | Substantially Pandar-style. His examples bought complete far-OTM call spreads on puke days. | White paper’s call-side mirror plus our surface and technical screen. Not Pandar’s documented call method. | Pandar explicitly sold rich front call tails. P1’s systematic call buyback is a mechanized extension with only partial full-cycle fidelity. |
| Market state | At least 8% below the 20-day high with a negative five-day return. The long-term trend may be damaged. | Above the 200-day, no more than 15% above the 50-day, and positive 63-day relative strength. | Within 5% of the 20-day high with positive five-day momentum and a one-sided spot-up/vol-up call grab. |
| Positioning story | De-grossing makes investors pay for puts while a sharp rebound is treated as implausible. | Upside is cheap before a possible momentum chase, squeeze, or gap. | The crowd is paying for the far front call wing during a squeeze. The trade fades that temporary demand. |
| Surface minimum | RR Rank ≥60, call-skew rank ≤40, IV Rank ≤65. | Good/Better/Best cheap-call tiers, including 30-day call-wing limits. | Front 5-delta call-wing rank ≥85, kink ≥70, RR Rank ≤10, opposite put wing <70, and IV Rank 30–70. |
| Meaning of IV Rank | It may remain moderately high because shock-bid puts lift the whole surface while calls stay cheap relative to them. | The first leg is a larger standalone call, so the whole surface must be genuinely cheap. | The goal is local front-wing richness, not indiscriminate short vol. Midrange IV separates a grab from very cheap total vol and extreme event vol. |
| Instrument | Complete 20–35%-OTM, 30–90 DTE bull-call spread. | Roughly 10–15-delta, 30–60 DTE long call; next listed call is the intended short. | Nearest 5–12 DTE, fallback through 19 DTE; sell the 2–6-delta call nearest 4 delta, then buy one strike nearer. |
| Initial cash | Small debit, usually pennies to a few dimes. | Full price of the long call, often several times the concurrent spread debit. | Cash credit received, but substantial margin is committed while the call is naked. |
| Risk before completion | Defined from inception. Maximum loss is the debit. | Bounded but larger: the entire long-call premium can be lost before pairing. | Theoretical loss is unbounded. It also carries gap, margin-expansion, assignment, and forced-liquidation risk. |
| What must happen | A sharp rebound must inflate the distant spread enough to monetize. It never needs to plant. | The upper call must rise above the lower call’s original cost plus the target credit. | The chase must stall or reverse, and the nearer call must fall below the resting buy despite being intrinsically more valuable. |
| Mechanical catalyst | Short covering, stabilization, vol-control re-risking, CTA re-chasing, and possible dealer upside hedging. | Gap/rip, delta and gamma lift, and sometimes spot-up/vol-up call demand. | Call-demand exhaustion, spot stall, front-wing IV crush, theta/weekend decay, and dealer hedge unwind. The dealer story is an inference, not measured fact. |
| P&L character | Many small predefined losses, occasional 3–5× rebounds, and rare right-tail payoffs. | A timely rip can manufacture a zero-cost or credit vertical; a slow tape leaves a decaying long call. | Many small retained-credit wins can be offset by rare severe squeeze losses. A filled buy converts the risk into a defined bull spread. |
| Management | Scale complete spreads around 2×/3×/5×; roll remaining inventory before decay dominates. | Rest the upper sale immediately. Enforce price and time stops while unpaired; monetize the paired spread during elevated probability. | Size to survive the naked phase. Rest the buy immediately. Cover or cap when the breakout tell fires; suppress additional sales during the same squeeze. |
| Primary failure | The rebound is too weak or distant-strike liquidity consumes the theoretical edge. | No prompt chase: theta and falling vol erode the long, or the technical trend breaks. | The “grab” is a real breakout. Spot and wing IV keep rising, the buy never fills, and the short becomes increasingly negative-convex. |
| Strategy identity | Convexity inventory and portfolio hedge. | Directional call during the unpaired period; credit-spread construction only after a fill. | Short call-wing vol before pairing; a credit-carried bullish vertical only after pairing. |

## What the surface ranks mean

**RR Rank** means risk-reversal rank, not risk/reward. The raw measure is 25-delta put IV minus 25-delta call IV.

Its rank compares today’s value with the prior 252 sessions. High RR means puts are rich relative to calls. Low RR means calls are rich relative to puts.

**Call-skew rank** compares the 25-delta call with ATM. Low call skew supports the buy methods because the call is cheap or flat relative to ATM.

High call-skew rank corroborates a sell-first grab, but it is not a hard trigger. The sell-first instrument lives much farther out on the 5-delta wing.

**Front call-wing rank** asks whether 5-delta front calls are unusually rich versus front ATM IV. This is the sell-first trade’s primary local-richness tell.

**Call-kink rank** compares the 5-delta front call with the 5-delta 30-day call. A high kink says the richness is concentrated in the front tenor.

**IV Rank** locates the whole 30-day surface between its trailing one-year low and high. It is an absolute-volatility filter, not a direction signal.

The ranks do not prove that a stock will reverse. They also do not directly prove dealer positioning, call-OI stacking, or executed hedge flow.

## Why the buy methods have different IV limits

Puke can allow IV Rank up to 65 because put demand may elevate the whole surface while the complete call spread still costs very little.

Standard buys a materially larger naked call first. Its Good/Better/Best tiers therefore require progressively cheaper outright volatility.

| Tier | IV Rank | RR Rank | Call-skew rank | 30-day call wing |
|---|---:|---:|---:|---:|
| Good | ≤50 | ≥60 | ≤40 | ≤+3 vols |
| Better | ≤35 | ≥80 | ≤25 | ≤+2 vols |
| Best | ≤25 | ≥90 | ≤10 | ≤+1 vol and normal IV30 < IV90 contango |

Sell-first uses IV Rank 30–70 for a different reason. It wants the local call tail to be abnormally rich without selling a very cheap surface or confusing a broad event-vol shock with a one-sided grab.

## Method 1: Buy-first call puke

The stock has already undergone forced selling. Puts remain bid, while the market treats a sharp upside rebound as implausible.

The trade buys both legs immediately. That caps the upside but fixes the maximum loss, reduces theta and vega, and removes all dependence on a future upper-call fill.

Our implementation is broader than Pandar’s clearest examples. His examples were often about $5 wide, 25% or more OTM, and near $0.10 or less.

The accurate claim is “Pandar-style,” not “Pandar’s exact rule.”

### Sequence

1. Find RR ≥60, call-skew rank ≤40, IV Rank ≤65, drawdown ≤−8%, and a negative five-day return.
2. Buy the complete 20–35%-OTM, 30–90 DTE call spread.
3. Treat the debit as hedge inventory, not as a precision directional entry.
4. Scale out into a rebound, commonly near 2×/3×/5×.

## Method 2: Buy-first call standard

This trade needs more than cheap calls. It needs a reason for those calls to become expensive soon.

The technical overlay asks for an intact trend, controlled extension, and positive relative strength. Stronger tiers prefer improving trend and cohort structure.

Until the upper call sells, this is simply a long call with theta, vega, and directional risk.

### Sequence

1. Find a Good, Better, or Best cheap-call surface with the constructive technical overlay.
2. Buy the roughly 10–15-delta, 30–60 DTE lower call.
3. Rest the adjacent upper-call sale at the lower call’s cost plus the target credit.
4. If filled, manage the resulting vertical. If not, obey the price and time stops.

A gap or ripping morning works best because both adjacent calls can jump together. A slow grind may lift spot while falling IV prevents the upper call from reaching the sale.

## Method 3: Sell-first call grab

This is the opposite surface and tape from the puke trade. Calls are being grabbed while the stock is already near its recent high.

The trade is not a cheap-call buy. It begins by selling a far call during a one-sided spot-up/vol-up event.

### Exact surface trigger

| Gate | Requirement | Meaning |
|---|---:|---|
| Front 5-delta call-wing rank | ≥85 | The traded tail is unusually rich versus ATM. |
| Call-kink rank | ≥70 | Richness is concentrated in the front tenor. |
| RR Rank | ≤10 | Calls are rich relative to puts. |
| Opposite put-wing rank | <70 | This is one-sided grabbing, not a two-sided shock smile. |
| Five-day return | >0 | Spot has moved toward the call side. |
| 20-day drawdown | ≥−5% | Spot remains near the recent high. |
| IV Rank | 30–70 | Total vol is midrange while the local wing is extreme. |
| Earnings | Not near front expiry | Avoid the event that can justify the wing premium. |

### Exact contract gate

Use the nearest listed expiry with 5–12 DTE, falling back through 19 DTE. Select the 2–6-delta call nearest 4 delta.

Require a far-call bid of at least $0.20, a quote width no greater than $0.10, OI of at least 25, and call IV at least two points above same-expiry ATM.

### Sequence

1. Sell the far call at the bid.
2. Immediately rest a buy for the adjacent lower-strike call at sale minus $0.10, floored at $0.10.
3. If the buy fills, retain the credit and hold a long-nearer/short-farther bull-call spread.
4. If spot and wing IV continue higher, cover or cap the short. Do not add another short into the same breakout.

The buyback is harder than it sounds. The nearer call is intrinsically more expensive, so the grab must collapse enough for it to fall below the earlier far-call sale.

### Why the risk is categorically different

Receiving a credit does not make the trade cheap or free. Before the second leg fills, the position is a naked short call with theoretically unbounded loss.

The danger is path-dependent. A gap can move through the stop, expand margin, and force liquidation before an end-of-day rule can react.

Pandar’s defense was sizing: sell few enough that a strike touch does not push the book past its point of no return.

P1 adds a research override. If wing rank rises further while spot advances at least 5% toward the strike, buy back or cap the short and stop adding.

After a fill, “free spread” is accounting shorthand. Buying the nearer call may retain less cash than simply closing the far short at the same time.

The vertical’s later payoff must justify that opportunity cost.

### Provenance correction

Pandar explicitly sold front-weekly NVDA calls when the call tail was overpriced. That gives the first leg strong Pandar fidelity.

His broader process also says to sell expanded tails and buy nearer options after the crush. The clearest documented call conversion in the thread, however, belongs to Kreisleriana.

Therefore the full sell-and-convert cycle is **Pandar-derived**, not a documented Pandar call recipe.

Pandar’s January 31, 2025 call sale was also a post-shock smile, not this RR≤10 grab subtype. Sell-first grab is only one branch of call-tail selling.

## Updated replay evidence: August 11–27, 2026

The expanded replay contains 87 assigned ticker/date rows across 49 unique tickers.

| Method | Surface rows | Unique tickers | Exact-chain rows | Exact-chain tickers |
|---|---:|---:|---:|---:|
| Buy-first call puke | 41 | 24 | 15 | 10 |
| Buy-first call standard | 25 | 13 | 0 | 0 |
| Sell-first call grab | 21 | 13 | 4 | 1 |
| **Total** | **87** | **49 across the complete set** | **19** | **11 finalists after scenario/ticker deduplication** |

These rows are repeated daily observations. They are not independent episodes, completed trades, fills, profits, or expectancy estimates.

The classifier assigns sell-first before puke and puke before standard. Two rows met both buy conditions but were assigned to puke, so category counts are not natural frequencies of independent strategies.

### The four sell-first confirmations are one MSTR episode

| Signal date | Expiry | First sale | Resting buy | Screen interpretation |
|---|---|---|---|---|
| Aug 19 | Aug 28 | Sell 140C at ≥$0.24 | Buy 135C at $0.14 | First exact MSTR grab signal. |
| Aug 20 | Aug 28 | Sell 150C at ≥$0.32 | Buy 145C at $0.22 | Same squeeze; breakout override was already activating. |
| Aug 21 | Aug 28 | Sell 160C at ≥$0.26 | Buy 155C at $0.16 | Do not treat as an independent fresh short. |
| Aug 24 | Aug 28 | Sell 155C at ≥$0.22 | Buy 152.5C at $0.12 | Same expiry and continuing episode. |

From Aug 19 to Aug 20, MSTR advanced more than 5% and the front call-wing rank rose. Under the breakout rule, the original short should be covered or capped.

The Aug 20 150C sale then marked at a $0.50 ask on Aug 21 versus the $0.32 sale. The 145C ask was $0.71, far above the $0.22 resting target.

That is an unpaired $18 loss per contract at the close proxy, before fees. It proves the screen found a genuine grab; it does not prove the grab was profitable to fade.

Seventeen of 21 sell-first surface rows failed strict chain validation. Aggregate ticker liquidity did not guarantee a tradable 4-delta call.

Likewise, zero exact standard tickets is an operational result for this sample. It is not proof that the method has negative expectancy.

## Evidence limitations

The 398-name HIRO list was refreshed on August 28 and applied retrospectively. It is not historical HIRO membership.

The original 58 rows through August 21 remain frozen point-in-time. One LCID rank moved slightly below 60 after ORATS refreshed its history, but the originally identified row remains in the baseline.

Only MSTR passed the sell-first exact-chain gate, and all four passes belong to one squeeze and one expiry. That is too little episode diversity to establish positive expectancy.

HIRO follow-through was captured for all 49 qualifying tickers, but provider retention left many older sessions unavailable. The capture is useful context, not execution proof.

Contract confirmation uses the signal-date historical chain. It does not prove that the same price was executable at the next session’s open or that the resting second leg filled.

The proper sell-first validation unit is the squeeze episode, with intraday NBBO sequencing, gap and margin stress, and comparison against immediate vertical and same-time buy-to-close controls.

## Durable labels going forward

Use these names in reports and code:

1. **Buy-first call puke**
2. **Buy-first call standard**
3. **Sell-first call grab**
4. **Buy-first put-tail inventory** — Pandar's separate penny put-spread inventory program; it is not one of the three call methods analyzed above.

For **Sell-first call grab**, the optional subtitle is **Pandar-derived spot-up/vol-up fade**.

Avoid calling all three “call bombs” without the qualifier. The shared payoff shape hides three different first legs and three different ways to lose.

## Local evidence

- `docs/delta_bombs.html`, critical provenance reread and Pandar call evidence around lines 719–761.
- `docs/specs/p1_nvda_tail_sale_backtest.md`, trigger, instrument, entry, breakout, and counterfactual rules around lines 56–110.
- `docs/specs/p1_nvda_tail_sale_backtest_charlie-mcelligott_review.md`, risk and validation critique.
- `docs/replay/hiro_daily_2026-08-11_to_2026-08-27/hiro_all_qualifying_strategy_signals.md`, complete 87-row set.
- `docs/replay/hiro_daily_2026-08-11_to_2026-08-27/hiro_call_path_daily_table.md`, 19 exact-chain rows.
