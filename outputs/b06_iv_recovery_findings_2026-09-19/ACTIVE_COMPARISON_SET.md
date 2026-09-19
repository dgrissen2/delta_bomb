# Fixed B06 / IV comparison set

Frozen 19 September 2026 by user instruction, before collecting or scoring the additional 100 days. This is the complete set being carried forward; no row is dropped because another has a higher observed hit rate.

| ID | Rule applied to B06 | Original 50-day signals | +5 first | Hit rate | Improvement over B06, pp | Active dates |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| baseline | Plain B06; no IV selection | 374 | 239 | 63.9% | — | 49 |
| original | Six falling-and-accelerating sectors; original validity | 93 | 67 | 72.0% | +8.1 | 35 |
| midpoint | Same condition; recover when bid IV fails | 112 | 78 | 69.6% | +5.7 | 39 |
| guarded_100 | Midpoint recovery plus quote guards; spread/midpoint ≤ 1.00 | 69 | 49 | 71.0% | +7.1 | 32 |
| guarded_50 | Midpoint recovery plus quote guards; spread/midpoint ≤ 0.50 | 29 | 22 | 75.9% | +12.0 | 17 |

The objective remains **SPX +5 before −15 within the original sixty minutes**. Accuracy has first priority; opportunity count second. Later reversals do not change a success. None of these rows has an established future advantage merely because it beat B06 in the original sample.

## Identical signal and measurement

Use the same eleven ETFs, constant 30-calendar-day spot-ATM midpoint IV, original strike-variance / expiry-total-variance / call-put-variance interpolation, and all thirty observed minutes T−35…T−6. No time filling. For each fifteen-sample half, b = Σ(i−7)IV_i / 280; a = (b_second−b_first)/15. The same six or more ETFs must satisfy b_second < −1e−12 and a < −1e−12. Denominator is eleven, with yes/no/unknown bounds preserved.

Original requires positive finite ordered bid/mid/ask IV as well as dollar quotes and inherited endpoint/underlying/expiry checks. Midpoint drops only the bid-IV validity and bid-IV ≤ midpoint-IV tests; positive dollar bids, positive finite ordered midpoint/ask IV, and all other checks remain.

Both guarded versions first select midpoint-recovery constituents, then reject the complete ATM minute if any selected constituent fails the spread ceiling, lacks positive ordered same-contract quotes exactly one minute earlier, or has:
- bid < 0.50 × previous bid AND ask ≥ 0.90 × previous ask; or
- ask > 2.00 × previous ask AND bid ≤ 1.10 × previous bid.

Never substitute farther strikes to evade guards. Do not grandfather originally valid quotes. Do not equate zero bid IV with a zero dollar bid. Missing expiry brackets and other unrecoverable observations stay unavailable.

## Interpretation to retain

The midpoint row is an explicit candidate: it keeps all 93 original qualifying entries and adds nineteen, including eleven additional successes. It must not disappear from the shortlist. The 100% guard row remains even though original rules had a slightly higher observed rate and more entries; it tests a different measurement policy. The 50% row is retained as a selective candidate, not declared a proven winner.

The previous “primary” and “sensitivity” labels describe the recovery experiment's prespecified roles. The user now requests this entire four-policy comparison set. All four will be reported without selecting a winner on the new data or revising thresholds.

See [extensive findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/FINDINGS.md) and [archived evidence](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/evidence.json). The expansion protocol is [here](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_expansion_150d_2026-09-19/PROTOCOL.md).
