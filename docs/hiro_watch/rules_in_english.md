# The rules in English — what every knob and flow number means (2026-09-06)

HIRO (SpotGamma) is **estimated dealer hedging pressure** inferred from options transactions — not
customer buying, not open interest, not gamma exposure. A rising line means dealers are being pushed
to **buy** stock; a falling line means they are pushed to **sell**. On the call side a rising line
comes from customers *buying* calls; on the put side a rising line comes from customers *selling*
puts. Both are supportive of equities. (`~/.claude/skills/hiro-learnings` — non-negotiable meanings.)

## The flow numbers the engine computes every minute (from the S&P 500 basket, `all` series)

| symbol | what it is | in English |
|---|---|---|
| `L` | cumulative HIRO total since 09:30 | the running tally of dealer hedging pressure today |
| `r15`, `r30` | change in `L` over the last 15 / 30 minutes ($B) | net hedging pressure *right now* (15) and over the last half hour (30). Positive = dealers pushed to buy; negative = pushed to sell |
| `run` | rise in `L` since the current run began ($B) | the size of the current wave of upward pressure. A run starts when `L` turns up and ends when it falls ≥ 0.6 $B from its peak |
| `dur` | minutes since the run began | how old the wave is |
| `rate` | `run ÷ dur`, in $B/hour | how fast the wave is accumulating |
| `ΔC`, `ΔP` | call-line and put-line change during the run | pressure from call *buyers* and from put *sellers* |
| `cpr` | min(ΔC, ΔP) ÷ max(ΔC, ΔP) | balance between the two sources; 1.0 = equal |
| `weak side` | min(ΔC, ΔP) | the smaller source, in $B |
| `ΔN`, `share` | next-expiry line change during the run; its share of the run | how much of the wave is short-dated (dealers hedge that most aggressively) |
| `dd` | drawdown of `L` from its peak within the run | has the wave already broken |
| `pull30` | SPX high of the last 30 min − current SPX | how far price has dipped from its recent high |
| `mid30`, `bounce30`, `range60` | 30-min midpoint; bounce off the 30-min low; prior-60-min range | Branch-A price context: below the midpoint, has bounced, and the day has expanded |

## Branch B (sell the −0.20Δ put first, rest the buy 5 strikes higher)

| rule | value | in English |
|---|---|---|
| HIRO fresh | required | the feed updated in the last few minutes |
| `dur` | ≥ 10 min | the upward-pressure wave has lasted at least 10 minutes — not a blip |
| `rate` | ≥ 2 $B/hr | it is accumulating fast enough to matter |
| `ΔC` > 0 and `ΔP` > 0, `cpr` ≥ 0.25 | both | call buyers AND put sellers are both pushing dealers to buy; neither source is less than a quarter of the other |
| `ΔN` > 0, `share` ≥ 0.5 | both | at least half the wave is in the nearest expiry |
| `dd` | < 0.6 $B | the wave has not broken |
| `pull30` | ≥ 3 pts (`b_pull_min_pts`) | SPX has dipped from its 30-min high — sell the put into the dip that supportive hedging should reverse. **B-PULL candidate: 8** |
| `r15` | > 0 | the support is present right now, not just earlier in the run |
| time | ≤ 14:30 | no new naked leg late in the day |
| `weak side` | ≥ 0.15 $B | both sources are real |
| not LATE | blocked if `rate` ≥ 4 **and** `r30` ≥ 1 | fast AND already a billion in the last half hour = late to the wave. **Knob `late_enabled`; `late_sticky` = once LATE fires the episode stays blocked** |
| **`run`** | **≤ `b_run_max`** (v1: unbounded; **B-SIZE candidate: 1.0 $B**) | total pressure since the wave began. Above a billion most of the dealer buying it implies has already happened — do not sell a put into a spent wave. The floor is implicit: 10 min × 2 $B/hr ≈ 0.33 $B |
| `dur` | ≤ `b_dur_max` (v1: unbounded; B-AGE candidate: 15 min) | do not sell into an old wave |
| `b_enabled` | true (false = B-OFF control) | switch the branch off entirely |
| second leg | rest the buy at fill − `credit_b` (v1: 0.10) | the credit B asks for; every extra dime has cost a bomb |

Plain version: **put sellers and call buyers are forcing dealers to buy stock, the dip is being
absorbed, and the wave is still young — sell a put into that and rest the buy five strikes up.**

## Branch A (buy the −0.20Δ put first, rest the sell 5 strikes lower)

| rule | value | in English |
|---|---|---|
| `range60` | ≥ its 75th percentile | the day has expanded — enough movement for the put to reprice |
| `bounce30` | ≥ 3 pts | price has bounced off its 30-min low (buy the put on the bounce, not the low) |
| SPX | < `mid30` | still in the lower half of the last 30 minutes |
| `r30` | < 0 in v1; **< `a_r30_lt`** (**a_depth candidates: −2, −4 $B**) | net hedging pressure over the last 30 min is *downward*: customers buying puts / selling calls hard enough that dealers must sell stock. −2 = at least $2B of it |
| HIRO fresh | required | as above |
| time | ≥ 10:35, ≤ 14:30 | window |
| second leg | rest the sell at fill + `credit` (v1: 0.10; candidates 0.20, 0.30) | A's fills have reached 30¢ without losing a fill on the v1 trade set (one lost in the −2 grid cell) |

Plain version: **dealers are being forced to sell into a day that is already moving — buy the put and
let the selling wave carry it to your resting sell.**

## Exits (both branches, unchanged in every candidate)
fill (bomb, credit banked) · Branch-B scratch within 3 min if `L` drops ≥ 0.3 $B or the run breaks ·
veto exit if the flow veto (r15 and r15n < −0.8) turns on while short · 3.5-pt cap on the lone leg ·
60-minute clock. A completed bomb pays $500 at expiry at or below the lower strike, proportionally
between the strikes, plus the credit already banked.
