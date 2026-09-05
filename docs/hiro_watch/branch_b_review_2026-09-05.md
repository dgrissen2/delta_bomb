# Branch B failure modes — Charlie McElligott and Brent Kochuba (GPT-6 Astra, high reasoning), 2026-09-05

Inputs: `branch_b_brief_2026-09-05.md` (rules verbatim, every B trade in v1 and `a_depth_m4` with flow
readings, entry prices, exit reason, MAE; refusals; the three B bombs' marks). Run separately through
`/codex-strategy-review` on `gpt-6-astra` / `high` (skill bumped today; Codex CLI 0.144 → 0.153).
Raw outputs: `branch_b_astra_charlie-mcelligott_2026-09-05.md` (7 findings, FAIL),
`branch_b_astra_brent-kochuba_2026-09-05.md` (6 findings, FAIL). An earlier GPT-5.6-Sol pass by Brent
(`branch_b_sol_brent-kochuba_2026-09-05.md`) reached the same conclusions.

Both Astra runs caught three errors in my brief, since corrected: "+$610 = A +$1,260 + B −$360"
mixed MTM with cash (cash is +$900; the −$290 is the inventory difference); "turning any block off
loses money" contradicted LATE-off +$45; and the bomb pays the full $500 **at or below** the lower
strike, not only between the strikes. Brent's Sol pass also caught "all bombs planted in the first
hour" (one was 11:34).

## The question
Branch B (sell the −0.20Δ put first, rest the buy 5 strikes higher at −10¢) lost −$260 in v1 and
−$620 in `a_depth_m4` on identical rules. Why does B lose, which failure modes are structural, which are
capacity artefacts, and should B exist?

## Charlie — in simple terms

**1. B has to be *paid* to become a spread, and it's exposed until then.** After selling the lower put,
the higher put has to get *cheaper* than what you sold for before the buy fills. That needs the market
to go up. If it goes down instead, the put you're short gains value and gets worse the further it falls
(negative gamma). Nothing about the finished spread protects the unfinished one. This belongs to the
sell-first sequence itself; freeing capacity only decides how many trades are exposed to it.

**2. Every one of the seven failures ended the same way: the flow that justified the entry stopped.**
Four scratches (−$320) — flow fell ≥ 0.3 $B within 3 minutes; three veto exits (−$330) — the flow veto
flipped on while short. No timeout, no cap. Entry-time flow strength said nothing about whether it
would persist: the 08-25 scratch had the strongest run in the set (2.26 $B, r15 +1.14) and was gone in
five minutes. "Scratch" sounds small; it averaged −$80. Once the 3-minute window closes you're carried
until another rule fires — 08-28 reached −$290 before the veto took it out at −$220.

**3. Capacity explains the *extra* loss, not the loss.** The three trades v1 refused (A leg open /
3-per-day used) are exactly −$360 and added no bombs, so the whole v1→a_depth deterioration is those
three. But v1's own seven were already −$205 including inventory. Capacity happened to shelter B from
three more losers; it didn't give B an edge.

**4. Verdict: B hasn't earned a place.** Ten attempts → three spreads, $30 of credits, $55 of current
marks, −$650 of failed attempts = −$565. Even the successful 51-minute fill sat −$90 underwater first.
Keep B off on this evidence — as a decision about the evidence, not a proof sell-first can never work;
all ten trades are discovery, and the one confirmation session had no B trade.

**5. Two specific things to watch.** The LATE suppression cleared on 08-25 at 11:37, three minutes after
suppressing at 11:34 — a threshold that clears *as flow slows* is admitting the trade exactly as support
fades. And "zero cap exits" is not safety: nothing here shows the 3.5-pt cap survives a gap.

## Brent — in simple terms

**1. The financing step creates the exact risk the finished spread is supposed to remove.** Selling the
lower put first is being short downside convexity while waiting for downside protection to become
affordable. A drop or a vol spike makes the protection dearer *and* hurts the short at the same time.
Flow gates can't turn a naked short put into a protected spread; only the second fill can.

**2. What the exits demonstrate is failed flow persistence, not contained risk.** Same seven flow exits.
The scratch window is an early escape hatch; after it, you're exposed until something else fires.
"Zero caps and timeouts" tells you nothing about a gap. Even the winners spent 10, 12 and 51 minutes
exposed.

**3. Capacity accounts for the full −$360 and excuses nothing.** The three admitted trades failed the
same two ways the original seven did. They weren't uniquely bad signals because capacity let them in;
capacity was incidentally rationing exposure to a branch that already lost.

**4. The sample says disable *this implementation*, not that sell-first is impossible.** −$565 all-in.
The three spreads are worth $55 today, but that's an interim mark — at or below the lower strike each
pays $500 — so the inventory's *potential* is not zero. Still, nothing here shows enough benefit to keep
B active. No out-of-sample B trade exists.

**5. What's missing is the mechanism.** Positive HIRO flow describes the entry moment. It does not show
dealer gamma sign, a cliff, a void, or whether the short-put interval is protected from dealer-amplified
downside. Without that, "positive flow → safe to be short a put for an hour" is an assumption, and seven
of ten trades say it's a bad one.

## Where they agree (both Astra runs, independently)

| | structural or artefact? |
|---|---|
| Naked short put until the second leg fills; needs the market to rise to complete | **structural** to sell-first |
| All 7 failures are flow exits (4 scratch, 3 veto) — flow at entry does not persist | **structural** to using flow as the entry |
| The 3-min scratch window, then exposed until another rule fires (08-28: −$290 MAE) | structural |
| The extra −$360 under `a_depth_m4` | **capacity artefact** — v1's shallow A legs were rationing B |
| "Zero cap exits" ≠ safe in a gap | unmeasured risk |
| B all-in: −$565 (v1: −$205); 3 bombs marked $55 | **disable this implementation on current evidence** |

Neither said "B can never work"; both said there is no evidence it works *as built*, and no confirmation
data on it at all.
