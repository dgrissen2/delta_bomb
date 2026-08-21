## Brent Kochuba

Notation: ET regular session; `H/C/Pw` = All-Trades total/call/put HIRO rolling `w` minutes for the S&P 500 basket. `R15=Ct−Ct−15`; `Range60=max(H60)−min(L60)`; `PB30=max(H30)−Ct`; `BN30=Ct−min(L30)`. All tests use completed bars. Initial legs execute next-bar open; `S0` is that bar’s SPX open. Arms remain live only while every arm condition holds.

1. **Morning pressure-decay rebound — sell-first.** Arm 09:45–11:00: `PB30≥6`, `R15≤−4`, `H15<0`. Trigger: `H5t>H5t−1>H5t−2`, `H5t<0`, and `Ct>Ct−1`; sell put. Complete when `C≥S0+3`, buying `K+5`. Scratch when `C≤S0−3` or `H5=min(H5 over prior 15 bars)`. Timeout: 60 minutes. Expected: 1–2/day.

2. **Midday loud-bounce fade — long-first.** Arm 11:00–14:30: `Range60≥12`, `BN30≥6`, `R30<0`. Trigger: `C5` crosses from `≤0` to `>0`, `P5` crosses from `≥0` to `<0` on the same bar, and `C≥max(H30)−2`; buy put. Complete when `C≤S0−3`, selling `K−5`. On the third completed bar after entry, scratch unless `C5>0` and `P5<0` held on all three bars. Timeout: 45 minutes. Expected: 1–3/day.

3. **Afternoon forced-flow shutoff — sell-first.** Arm 14:30–15:40: `R15≤−5`, `PB30≥8`, `H15<0`. Trigger: `H5` crosses from `≤0` to `>0` and `Ct>max(Ht−1,Ht−2)`; sell put. Complete at `C≥S0+3`, buying `K+5`. Scratch at `C≤S0−3` or after two consecutive `H5<0` bars. Timeout: 30 minutes or 15:55, whichever comes first. Expected: 1–2/day.

## Charlie McElligott

1. **Morning de-gross snapback — sell-first.** Arm 09:45–11:00: `R15≤−0.25×Range60`, `H15<0`, `P15<0`. Trigger: two consecutive up closes and current `H5≥0`, `P5≥0`; sell put. Complete at `C≥S0+3`, buying `K+5`. Scratch after two consecutive bars with both `H5<0` and `P5<0`. Timeout: 45 minutes. Expected: 1–2/day.

2. **Midday re-lever failure — long-first.** Arm 11:00–14:30: `R15≥0.25×Range60`, `H15>0`, `C15>0`, `P15>0`. Trigger: two consecutive down closes and current `C5≤0`; buy put. Complete at `C≤S0−3`, selling `K−5`. Scratch after two consecutive bars with both `H5>0` and `C5>0`. Timeout: 60 minutes. Expected: 1–3/day.

3. **Late squeeze failure — long-first.** Arm 13:30–15:30: `Range60≥12`, `R30<0`, cumulative All-Trades total HIRO `<0`, `BN30≥3`. Trigger: first down close satisfying `C5>0` and `P5<0`; buy put. Complete at `C≤S0−3`, selling `K−5`. Scratch after two consecutive bars with `C5≤0` and `P5≥0`. Timeout: 45 minutes or 15:55, whichever comes first. Expected: 1–2/day.

## Union rule list

Global execution: only trigger while flat; completion takes priority over scratch, then timeout; every exit executes next-bar open; impose a 30-minute cooldown after exit; simultaneous triggers use lowest U-number. Expected counts are design priors, not demonstrated results.

1. **U1:** sell-first | 09:45–11:00, `PB30≥6`, `R15≤−4`, `H15<0` | `H5t>H5t−1>H5t−2`, `H5t<0`, `Ct>Ct−1` | complete `C≥S0+3`; scratch `C≤S0−3` or 15-bar `H5` low; timeout 60m | 1–2/day.
2. **U2:** long-first | 11:00–14:30, `Range60≥12`, `BN30≥6`, `R30<0` | simultaneous `C5` cross above zero and `P5` cross below zero, `C≥max(H30)−2` | complete `C≤S0−3`; three-bar flow-persistence scratch; timeout 45m | 1–3/day.
3. **U3:** sell-first | 14:30–15:40, `R15≤−5`, `PB30≥8`, `H15<0` | `H5` cross above zero, `Ct>max(Ht−1,Ht−2)` | complete `C≥S0+3`; scratch `C≤S0−3` or two `H5<0` bars; timeout 30m/15:55 | 1–2/day.
4. **U4:** sell-first | 09:45–11:00, `R15≤−0.25×Range60`, `H15<0`, `P15<0` | two up closes, `H5≥0`, `P5≥0` | complete `C≥S0+3`; scratch two bars with `H5<0` and `P5<0`; timeout 45m | 1–2/day.
5. **U5:** long-first | 11:00–14:30, `R15≥0.25×Range60`, `H15>0`, `C15>0`, `P15>0` | two down closes, `C5≤0` | complete `C≤S0−3`; scratch two bars with `H5>0` and `C5>0`; timeout 60m | 1–3/day.
6. **U6:** long-first | 13:30–15:30, `Range60≥12`, `R30<0`, cumulative `H<0`, `BN30≥3` | first down close with `C5>0`, `P5<0` | complete `C≤S0−3`; scratch two bars with `C5≤0`, `P5≥0`; timeout 45m/15:55 | 1–2/day.
