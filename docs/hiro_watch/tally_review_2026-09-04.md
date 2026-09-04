# What is broken — Charlie McElligott and Brent Kochuba on the tally through 2026-09-04

Inputs: `tally_brief_2026-09-04.md` (the numbers), the two `/codex-plan-review` runs beside this file
(`*_charlie-mcelligott_plan_review.md`, `*_brent-kochuba_plan_review.md`; Charlie 5 findings, Brent 6,
both verdict FAIL on the program's economics). Below, each reviewer's findings rendered in plain terms,
faithful to what they wrote; then a Feynman explanation of the two explanations.

## The tally (18 sessions 08-12 → 09-04, marked at the 09-04 close, SPX 7718)

| candidate | A trades/bombs | B trades/bombs | cash | inventory | MTM | vs v1 |
|---|---|---|---|---|---|---|
| **v1 baseline** | 24 / 13 | 7 / 3 | −1,470 | +590 (16 bombs) | **−880** | — |
| `a_depth_m4` | 5 / 5 | 10 / 3 | −570 | +300 (8) | −270 | +610 |
| `credit030` | 24 / 13 | 7 / 1 | −1,110 | +550 (14) | −560 | +320 |
| `diag_late_off` | 24 / 13 | 7 / 3 | −1,450 | +615 (16) | −835 | +45 |
| `diag_levels_off` | 24 / 13 | 10 / 3 | −1,840 | +590 (16) | −1,250 | −370 |
| `diag_vt_off` | 24 / 13 | 13 / 7 | −1,790 | +705 (20) | −1,085 | −205 |

16 discovery sessions, 1 confirmation session (09-03), 1 NFP stand-down (09-04). Confirmation 1/10.

---

## Charlie McElligott — in simple terms

**1. The trade doesn't pay for itself.** Every finished bomb earns $10. Every failed attempt — where you
bought the first leg and the second never filled — loses on average about $100. Over 31 attempts you
banked $160 and lost $1,630. A 52 % completion rate sounds fine until you notice the wins are $10 and
the losses are $100: you need to complete about ten for every one you fail just to break even. This is
the lead fact and everything else is downstream of it.

**2. The open inventory is hiding how bad the cash is.** The −$880 headline is −$1,470 of real cash
lost plus +$590 of paper value on 16 open put spreads. Those 16 are not 16 separate wins — they are one
bet (SPX down 2–4 % by late September) marked 16 times. That mark went +$1,265 → +$165 → +$590 across
three sessions. Any "candidate X is $610 better" number that depends on that mark can reverse on one
day's tape.

**3. The tape has confirmed almost nothing.** There is exactly one confirmation session. On it, two
shallow-flow Branch-A entries lost $420 during an 80-point rally and the −4 gate skipped both. That
confirms "the gate avoided those two losses." It does not confirm that deep-flow signals work, because
no deep-flow signal occurred. The NFP day adds nothing.

**4. The −4 gate is discovery-selected and regime-confounded.** Its 5-for-5 record comes from three
falling sessions — the tape where downside-flow entries are supposed to work anyway. The −1 version of
the same idea already failed its test. What the evidence supports is "shallow signals are harmful,"
not "−4 is a durable edge."

**5. Neither Branch B nor the wider credit fixes the engine.** B is too scarce to matter (7 trades in
17 sessions), and turning its safety rules off made things worse — the rules are blocking bad flow, not
suppressing a hidden opportunity. `credit030` keeps every losing A attempt and loses two of the three
B completions. These variants move exposure around; they do not address the adverse-selection and
legging-loss problem.

## Brent Kochuba — in simple terms

**1. The economics are broken, and it is the naked leg.** Same arithmetic as Charlie: $160 earned vs
$1,630 lost, roughly 10-to-1 the wrong way. The mechanism: the program is repeatedly left holding one
directional put on its own, and those one-leg losses swamp the tiny credit the structure was designed
to collect.

**2. Inventory disguises the loss and is one correlated position.** +$590 of unrealized value on 16
bombs that all pay or all expire together; it dropped by $1,100 in one rally. Realized cash loss and
concentrated inventory risk should be read as two separate facts, never netted into one "MTM" number.

**3. No repair has been confirmed.** One session; the gate avoided two shallow-flow losses; that is
all. `a_depth_m4`'s discovery record — five fills from three falling sessions — is regime-confounded.

**4. The evidence never established the dealer-hedging premise.** HIRO flow triggered the entries, but
nothing in the tally shows the synthetic-gamma sign, the strike "cliff," the void, or the reachability
of the traded strikes. So it cannot show what dealers were forced to do, or whether price ever entered
an amplifying regime. The defensible statement is narrow: shallow negative-flow readings have been bad
triggers in this sample.

**5. Branch B has no demonstrated edge and is not a fallback.** Three bombs from seven trades; loosening
VT and levels protections increased activity and worsened results; capacity freed by the stricter A
gate flowed into losing B trades. "Starved" is not "promising but underused."

**6. The downside is unbounded until the second leg fills.** The spread only has defined risk once both
legs are done. Before that you own a lone put and rely on a 60-minute timer and a nominal 3.5-point cap.
The tally already shows a −$350 cap exit and repeated timeouts, and nothing demonstrates the cap survives
a gap, a fast transit, or vanishing liquidity. Rejecting the $150 stop was correct, but it does not
solve this exposure — it documents that the current entry needs substantial adverse movement to succeed.

---

## Richard Feynman explains what they just said

Start with the simplest question: what does the trade actually do? You buy one put, then try to sell a
cheaper put ten cents lower so the pair costs you nothing and pays $10. If the second sale never
happens you own a single put for up to an hour. Both reviewers looked at the ledger and found the same
thing: the $10 events happened 16 times, the "stuck with one put" events happened 15 times, and the
average stuck-with-one-put event cost about $100. Sixteen tens is $160; fifteen hundreds is $1,630.
That is the whole diagnosis. The completion rate — 52 % — is the wrong thing to look at, because it
treats a $10 win and a $100 loss as the same-sized coin. You would need to complete ten pairs for every
one you fail, and you are completing one for one.

Second, the number that makes the book look survivable — the +$590 of "inventory" — is not money. It is
today's guess about what sixteen put spreads might be worth, and all sixteen are the same guess: that
the market falls 2–4 % in the next three weeks. When the market rallied 80 points on the 3rd, that guess
lost $1,100 in one session; when it dropped 30 points on the 4th, it got $425 back. So when you read
"candidate A is $610 better than the engine," ask how much of that is cash and how much is the same
guess counted differently. Both men say: keep the cash column and the guess column apart, because the
guess column can change sign on a Tuesday.

Third — and this is the part people hate — the promising fix has not been tested yet. The −4 gate looks
wonderful on the sixteen days it was chosen from: five trades, five completions. But it was chosen
because it looked wonderful on those days, and three of those days were the market falling, which is
exactly when buying a put and selling a lower one tends to work. That is not evidence; that is the
selection. The one day of genuinely new data showed the gate skipping two bad trades — good — but no
deep-flow trade actually happened, so the claim "deep flow works" was never put to the test. Nine more
sessions before the first honest reading. Meanwhile Brent adds a harder question: the story behind the
trade is that dealers are forced to hedge in a way that pushes price toward your strikes, and nothing
in the ledger measures that story at all. The data only says "weak flow readings were bad triggers."

So what is broken? Not the software — the software reproduced the engine to the row and caught its own
mistakes twice. What is broken is the shape of the bet: a tiny fixed payoff against an uncapped
naked-leg loss that a 60-minute timer and a 3.5-point cap only partly bound, dressed in a mark-to-market
number that borrows from a single correlated position. The candidates rearrange that shape; none of
them changes it. The right response is the boring one: keep running the frozen engine and the six
candidates every evening, keep the cash and the guess in separate columns, and refuse to believe the
gate until ten real sessions have said so. If, at that point, the naked-leg losses still eat the
credits ten to one, the answer will not be a better filter; it will be a different trade.
