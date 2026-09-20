# SPX IV acceleration and MAD history — complete

**681 target sessions, January 2, 2024–September 18, 2026**, plus 60 prior warmup
sessions beginning October 5, 2023. Underlying is SPX itself; consistently use
the native SPXW PM-settled option root. No ETF proxy or AM/PM root mixing.

**183,844/184,011 current windows scored
(99.91%).** Baseline status:
`{"ok": 3405}`. A usable historical baseline does not
guarantee a usable current-minute observation. Unavailable measurements remain
explicitly unknown. Missing target-date expiry brackets: **0**.

| Year | Dates | Expected windows | Scored windows | Window coverage | Usable baselines |
| --- | --- | --- | --- | --- | --- |
| 2024 | 252 | 68022 | 68022 | 100.00% | 1260/1260 |
| 2025 | 250 | 67480 | 67313 | 99.75% | 1250/1250 |
| 2026 | 179 | 48509 | 48509 | 100.00% | 895/895 |

Current-window support under the unchanged rules:

| Year | Usable windows | With neighbor sources | With guarded recovery | Minimum unique sources | Maximum shift minutes |
| --- | --- | --- | --- | --- | --- |
| 2024 | 68022 | 252 | 0 | 29 | 1 |
| 2025 | 67313 | 376 | 0 | 23 | 2 |
| 2026 | 48509 | 179 | 0 | 29 | 1 |

Neighbor and recovery counts can overlap. A usable window need not contain thirty
distinct strict observations. Reused source timestamps are deduplicated before
the slope calculation; none is counted twice as an independent observation.

Dates with unavailable target windows:

| date | window_slots | measured_windows | unavailable_windows |
| --- | --- | --- | --- |
| 2025-04-09 | 271 | 206 | 65 |
| 2025-11-20 | 271 | 170 | 101 |
| 2025-11-28 | 181 | 180 | 1 |

Recorded missing-source windows remain unknown. The native-input gap inspection
is saved separately in `gap_diagnostics.json`; it samples the first and last
unavailable endpoint on each affected date. An underlying price outside a
downloaded expiry's strike range cannot support ATM interpolation. Such a gap
is a collection-range limitation, not proof that the market had no quote. No
strike-range expansion, extrapolation or quality relaxation was applied here.

Same existing calculation: 30-calendar-day ATM IV; 8–65 DTE bracketing, call/put
variance average, native IV and matched first-order quote histories. Strict exact,
then strict ±2-minute neighbors inside the actual window/hour, then guarded
original-minute recovery with 100% spread ceiling. Positive dollar bid/ask required.
Actual-time fifteen-minute slopes; acceleration=(b2−b1)/15. Sixty strictly prior
sessions per endpoint-hour block, both signs, equal total date weight, exact lower
weighted median/MAD. Scale=1.4826×MAD; at least 10 contributing dates and positive
non-tiny scale. Signed score=−a/scale; absolute magnitude=abs(a)/scale; downward-only
also requires falling IV and negative acceleration. No thresholds fitted.

## The calculation in plain language

At each minute endpoint, use the preceding thirty completed minute observations.
Fit IV's rate of change separately over the first fifteen minutes and the last
fifteen minutes. Call those slopes b1 and b2. Acceleration is (b2 − b1) / 15;
the divisor is the fifteen-minute separation between the two half-window centers.
Its units are IV percentage points per minute squared. A negative value means the
IV slope is becoming more negative; IV may still be rising, just more slowly.

Compare that acceleration with its own SPX history in the same hourly block over
exactly sixty prior sessions. First find the weighted historical median, then the
weighted median distance from that median: MAD. Each contributing date has the
same total weight. Multiply MAD by 1.4826, the conventional conversion factor
1 / 0.67448975, where 0.67448975 is the standard normal's 75th percentile. It puts
MAD on a standard-deviation-like scale under a normal reference; it does not
assume these accelerations are normal or turn the score into a probability.

Divide the current absolute acceleration by that scale for magnitude. Keep the
raw sign separately, or use −acceleration / scale so positive means downward
acceleration. The numerator is measured from zero, not from the historical
median: this preserves physical acceleration direction. Whether IV is actually
falling is a separate b2 check. All inputs stop at the endpoint; an entry at T
would use the endpoint T−1. No future observations enter its score.

![SPX half-year magnitude](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/magnitude_bins_by_half_year.png)

Bars use available minute endpoints, both signs, equally weighted per endpoint.
Half-years have unequal lengths and overlapping windows are not independent.
2026 H2 stops September 18. Scope remains 09:30–14:29 ET observations, giving complete
window endpoints 09:59–14:29; early-close endpoints stop 12:59. This does not extend
the previous intraday measurement scope to the closing hour.

## Verification and provenance

Thirteen boundary tests pass; inherited quote-guard checks pass. Every baseline
is checked by independent rational-CDF inequalities, every prior-date/count ledger
and score is verified, and every usable OLS fit is replayed independently.
36 prefix checks include 2023 warmup and 2024 target
boundaries. Frozen inherited calculation/quality dependencies stay unchanged.
Boundary probes used required actual data at the first warmup, first target and
last target dates; all inputs were reused by the full run.

One native alignment exception is explicitly recorded. On June 9, 2026 the IV
endpoint returned 79,200 rows, a strict superset of all 36,000 Greek keys. A separate
paired IV view retains every Greek key and its unchanged IV counterpart; 43,200
unmatched IV-only rows are excluded. Original responses remain immutable, all
quote/IV checks remain unchanged, and independent pairing verification passes.
All 271 windows on that date are available. See the protocol addendum and pairing
receipt; this is a documented input repair, not a silent alteration of the original
protocol or a missing-Greek fill. No extra data request was made.

2,847 explicit SDK data attempts; 2,847 successful new responses;
0 recorded error attempts; no unresolved requests. Authentication is
excluded from data-call counts. Original sector data is unchanged. Native inputs,
expiry selections, dates, source/window tables, support and missingness, baseline
ledgers, scores and all hashes are in `/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1`.

This builds the requested measurement history. No B0x outcome test, ranking cutoff,
probability or option-profitability claim is introduced.

- [Scores](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/scored_windows.parquet)
- [Daily/hourly baselines](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/block_baselines.csv)
- [Daily coverage](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/daily_coverage.csv)
- [Hourly coverage](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/hourly_coverage.csv)
- [Window support](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/support_summary.csv)
- [Half-year counts](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/magnitude_bins.csv)
- [Protocol](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/PROTOCOL.md)
- [Endpoint pairing addendum](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/PROTOCOL_ADDENDUM.md)
- [Gap source inspection](/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1/gap_diagnostics.json)

Calendar reference: [NYSE/ICE 2023 calendar](https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx).
Contract-root reference: [ThetaData symbology](https://docs.thetadata.us/Articles/Data-And-Requests/Symbology.html).

Central registry/provenance commit: `82df4f5a30a95b153df5b0973c244eaead6c818b`.
