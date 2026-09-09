# Charlie Round 3: provisional minute-quote economics

**Superseded by the completed event check:** initial entries and D4 results are unchanged, but all four ORCL D5 spread results below are unavailable under the actual-event rule because the long exit quote is stale. Thus none of the eleven priced D5 completed deferred conversions beats same-minute cover; the three ORCL deferred comparisons are missing, not failures or successes. Event-level exposure also captures opening asks missed by minute snapshots. Use `event_admitted_case_comparisons.csv`, `tick_short_phase_exposure.csv`, `pandar_trade_results.md` and the actual Round 3 persona outputs for final interpretation. This working minute-only read is preserved as such.

This is a working interpretation of `admitted_case_comparisons.csv` and `policy_replay.csv`, before the actual-event quote replay. It is not the final Round 3 persona output. Prices below are diagnostics under an assumed, unverified 100-share multiplier and unverified deliverables. Fees are $0.65 per contract action plus $0.01 per share adverse slippage on each action; D4 is the primary fixed exit. The $0.02 stress holds the original action timestamps fixed.

## What the seven admitted entry policies show

The original band admits no minute-quote entries. The frozen exploratory delta-10 / at-least-5%-OTM variant admits seven entry policies across six stocks. These are not seven independent observations: MRVL has both clock and HIRO entries. Neither D5 nor the cost stress creates an independent sample.

All figures below are net dollars per assumed one-contract position. An asterisk means the nearer call was never bought: the displayed result belongs to the uncovered-short policy through its final cover.

| Initial entry, ET | Expiry; far / nearer call strikes | Immediate spread | D0 purchase arm | D1 purchase arm | D2 purchase arm | Short only |
|---|---|---:|---:|---:|---:|---:|
| PLTR Jun 12, 10:01 clock | Jun 18; 146 / 145 | -12.60 | -3.60 | -3.60 | -1.60 | +14.70 |
| DIS Jun 15, 10:01 clock | Jun 26; 107 / 106 | -16.60 | -25.30* | -25.30* | -25.30* | -25.30 |
| MRVL Jun 16, 10:01 clock | Jun 26; 425 / 420 | -93.60 | -17.60 | +46.40 | +10.40 | +168.70 |
| MRVL Jun 16, 14:16 HIRO | Jun 26; 425 / 420 | -73.60 | +69.70* | -24.60 | +69.70* | +69.70 |
| ORCL Jun 16, 10:01 clock | Jun 26; 222.5 / 220 | -42.60 | -6.60 | +26.40 | +55.40 | +72.70 |
| QCOM Jun 16, 11:11 HIRO | Jun 26; 280 / 275 | -85.60 | -20.30* | +9.40 | -20.30* | -20.30 |
| CRM Jun 17, 10:01 clock | Jun 26; 180 / 177.5 | -33.60 | -2.60 | +18.40 | +25.40 | +32.70 |

Fourteen of the 21 delayed arms purchase the fixed nearer call; seven never purchase. All fourteen completed purchases improve on buying the spread immediately, but only three improve on covering the original short at the purchase minute at D4. Only QCOM D1 improves on retaining the short to the same final deadline. These are descriptive policy comparisons, not statistical validation and not a reason to select the best delay after observing outcomes.

## The second decision must earn its place

CRM illustrates why total profit is insufficient. Sell the Jun 26 180 call on Jun 17 at 10:01, then buy the fixed 177.5 call on Jun 18 at 09:47 for a $0.12 ask. The D4 result is +$18.40, but covering the far call at 09:47 instead leaves +$19.70. Conversion costs $1.30 relative to that alternative. The positive total result does not demonstrate a good second purchase.

MRVL clock D1 makes the same point with larger amounts: buying the 420 call on Jun 17 at 09:44 produces +$46.40 at D4, against +$72.70 for same-minute cover and +$168.70 for retaining the original short to the final deadline. Waiting improves greatly on the immediate spread's -$93.60 while the later purchase still reduces profit relative to both exit alternatives.

ORCL D2 is the strongest quoted counterexample: the Jun 18 09:44 purchase produces +$55.40 at D4 against -$13.30 for same-minute cover, an incremental +$68.70. However, the far 222.5 call is quoted $0.03 / $0.94 while the nearer 220 call is $0.15 / $0.18. Avoiding that wide far-call cover ask explains much of the comparison. It may be an economic liquidity choice, but it does not establish bullish forecasting ability. Actual event age remains to be checked.

QCOM D1 produces +$9.40 at D4 versus -$11.30 for same-minute cover, an incremental +$20.70. At D5 the converted position is -$29.60, now $18.30 worse than that same cover alternative. A purchase can help at one frozen exit and hurt at the next. ORCL D1's cover advantage likewise shrinks from +$4.70 at D4 to +$1.70 at D5; the latter becomes -$0.30 under the fixed-timestamp $0.02 cost stress. At D5 only ORCL D2 retains a positive cover advantage under that stress.

## Exposure and interpretation limits

There is no later HIRO confirmation in the delayed-purchase rule. It buys the already frozen nearer strike on the first admissible financing minute in D0, D1, or D2, provided that call remains OTM with a valid positive delta and meets the frozen gates. This isolates the financing decision from a second flow-timing rule. It does not test whether a fresh bullish HIRO signal would improve purchase timing.

Known no-purchase paths remain uncovered short calls. DIS has no conversion in any delayed arm: its D4 loss is $25.30 and its D5 gain is $10.70. QCOM's D0/D2 gain of $136.70 at D5 likewise comes from never acquiring the long leg. These outcomes cannot be described as successful financed spreads or evidence of bounded risk. The purchase rule does not guarantee that a hedge will become affordable.

The minute exposure diagnostics include a conspicuous ORCL opening quote: Jun 17 at 09:31, the far call shows zero bid size and a $10 ask with one offered contract, producing a -$919.30 hypothetical cover result. The next minute's ask is $0.59. This is a one-sided opening ask observation, not an observed fill or a validated maximum drawdown. Its event timestamp must be checked before interpreting it as actionable liquidity. Even event-validated sampled marks will not establish intraminute extremes or overnight continuous tradability.

PLTR and CRM D5 spread results include zero-bid long marks. Those use a conservative zero valuation plus closing-cost reserve, not an executed sale of the long call.

MRVL is the only admitted same-stock clock/HIRO pair. Waiting until 14:16 reduces the collected far bid from $2.24 to $1.25; delta falls from 8.73 to 5.47 points and OTM distance rises from 36.31% to 45.47%. Its short-only D4 profit is correspondingly lower, $69.70 versus $168.70. This is one time-and-exposure comparison, not a general estimate of HIRO's benefit. QCOM has no admitted clock counterpart in this minute view.

The next interpretation must use the event-required replay and retain its missing-data paths. No additional delta/OTM tuning, new purchase trigger, or selected exit is justified by this small exploratory sample. Exact-strike history also remains incomplete in the forward-moneyness coordinate for MRVL and QCOM, and none of these six names is a rollover episode in the pre-outcome feature table.
