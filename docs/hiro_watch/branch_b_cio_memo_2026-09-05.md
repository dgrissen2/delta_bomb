# CIO memo — what Charlie and Brent advise on Branch B (2026-09-05)

*Sources: `branch_b_actions_brief_2026-09-05.md` (the ten Branch-B trades with what flow and price did
after each entry), reviewed separately by Charlie McElligott and Brent Kochuba on GPT-6 Astra (high):
`branch_b_actions_astra_charlie-mcelligott_2026-09-05.md`, `branch_b_actions_astra_brent-kochuba_2026-09-05.md`.
Both: CONDITIONAL PASS. Their rankings agree.*

**What is actually wrong.** Branch B sells a put and then needs the market to go up a little so the
put it wants to buy gets cheaper. Being naked short for that hour is the design — HIRO flow is what is
supposed to make the hour safe. The ten trades say the flow gate is letting B in at the wrong moment.
Every one of the seven losers was sold after a tiny 3-to-7-point wiggle in the index; the two clean
wins were sold after a real 12-point dip. And the four largest flow runs — the ones that look the most
convincing on the screen — all lost, while the wins came off small, young runs. Read together: B has
been selling *late*, after the buying is already spent and the dip is too shallow to bounce from. The
rule that was meant to stop that (the LATE suppression) let one trade through three minutes after
blocking it, and that trade lost in four minutes.

**What they advise, in order.** First, raise the pullback required to arm B from 3 points to 8. On the
ten trades that keeps only the two clean wins (+$20 instead of −$620) and drops everything else,
including one slow winner. Both reviewers rank this first because it is the strongest separation in the
data and it tests one idea cleanly: B needs room to bounce. Second, cap the size of the flow run at $1
billion — do not sell into a run that has already spent more than that. That keeps all three wins and
cuts five of seven losers (−$110 on five trades). Third, stop asking for a dime of credit on the second
leg for B; rest it at the sale price. That makes the pair complete sooner and shortens the naked hour;
the cost is the $10 credit, which is trivial next to the −$65 average loss. Fourth and fifth, lower
priority: make the LATE block stick for the rest of the episode, and separately test a 15-minute run-age
cap. Both said: one change per candidate, never combined, or you cannot tell which one worked.

**What they reject, and what they insist on.** Reject widening the 3-minute scratch window — a longer
window does not delay the exits that fired, it just adds later ones, and tolerating deeper flow
deterioration has no evidence behind it. Reject a 10-point pullback as a separate test — no trade sits
between 8 and 10, so it would be the same test twice. Keep "B off" (zero B entries a day) running as the
control, but do not call it the winner: the brief cannot show what A earns with B's capacity, and it
never counted what the three completed spreads could still pay at expiry (up to $500 each). Charlie's
first finding is that the scorecard has to carry the bombs' final payoff alongside the cash, or a filter
that sacrifices a bomb will be ranked wrongly.

**The honest bottom line.** These are ten trades from sixteen days that were used to find the pattern,
so nothing here is proven; the reviewers said so plainly. What they gave us is a short, ordered list of
single-knob candidates that the watch can score on the next ten to forty real sessions without touching
the engine: B-PULL 8 first, B-SIZE 1.0 second, B-CREDIT-0 third, B-OFF as the control, LATE-sticky and
age behind them. Register them now, before Monday's data, and let the tape decide. If B-PULL keeps its
discovery shape in confirmation, Branch B stops being a $600 drag and becomes a small, rare, mostly
clean planter; if it does not, B-OFF is already running and the decision makes itself.
