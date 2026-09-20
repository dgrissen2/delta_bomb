

### 11.33 — September 20: SPX IV acceleration/MAD history from 2024 complete

The same measurement is now calculated on SPX itself using native PM-settled SPXW
options: 681 target sessions January 2, 2024–September 18, 2026, plus 60 preceding
sessions beginning October 5, 2023. All regimes are included. No SPY proxy, AM/PM
root mixture, parent-signal restriction or outcome-based date selection is used.
The original sector measurement hours remain 09:30–14:29 ET; complete window
endpoints are 09:59–14:29, and early closes stop at 12:59. This is not a claim of
closing-hour or future-2026 coverage.

| Year | Target sessions | Scored / expected windows | Coverage | Usable baselines |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 252 | 68,022 / 68,022 | 100.00% | 1,260 / 1,260 |
| 2025 | 250 | 67,313 / 67,480 | 99.75% | 1,250 / 1,250 |
| 2026 through September 18 | 179 | 48,509 / 48,509 | 100.00% | 895 / 895 |
| Total | 681 | 183,844 / 184,011 | 99.91% | 3,405 / 3,405 |

**Measurement unchanged.** Thirty-calendar-day ATM IV, exact tenor or a true
8–65-DTE bracket, spot-strike interpolation and call/put variance average. First
use strict exact observations, then strict ±2-minute neighbors within the actual
window and target hour, then original-minute recovery with the existing 100%
spread/prior-quote/shock guards. Positive dollar bid/ask remains mandatory. Actual
source timestamps are deduplicated. The two actual-time fifteen-minute slopes
produce acceleration a=(b2−b1)/15. No new cutoff or trade filter was fitted.

**The historical ruler.** Exactly 60 strictly prior sessions, same instrument/hour,
both acceleration signs and every regime. Each contributing date gets equal total
weight. Compute the exact lower weighted median, then the weighted median absolute
distance from it. Scale=1.4826×MAD: 1.4826 is the conventional reciprocal of the
standard normal's 75th percentile, approximately 0.67448975. It is a scale
conversion, not a claim that acceleration is normal. Absolute magnitude is
abs(a)/scale; the signed score is −a/scale, positive for downward acceleration.
The numerator is zero-anchored, not median-centered. Whether IV is already falling
is separately recorded through b2. These scores are not probabilities.

**Coverage is very good, not perfect.** All baselines are usable; the first four
blocks have 60 contributing prior dates, and the last has 58–60 (median 59).
A usable historical baseline does not imply a usable current window. The 167
unknown target windows are 65 on April 9, 101 on November 20 and one on November
28, 2025. The first two days' sampled failures show spot outside an expiry's
returned strike range, preventing ATM interpolation. This is a collection-range
limit, not proof that the market lacked quotes. The final one-window gap remains
a missing-source/quality gap without a more specific root-cause claim. No
extrapolation, farther-strike substitution or silently broader request was used.

**Neighbor use is explicit.** 807 usable target windows use at least one nearby
source; none needs guarded bid-IV recovery. Available windows have at least 23
unique actual observations, with maximum source shift two minutes. The earliest
window usually has 29 unique sources. A reused observation is never treated as
an additional independent observation. Original source and support ledgers remain
available for every date/window.

**One provider alignment anomaly was repaired transparently.** June 9, 2026's IV
endpoint returned 79,200 rows versus 36,000 Greek rows. Every Greek key existed in
IV; the extra 43,200 IV-only rows could not be paired. The original exact-key guard
stopped the first derivation run. An additive frozen repair retains every Greek
key and its unchanged IV counterpart in a separate paired view. It does not drop
missing-Greek keys from the Greek response, invent values, or weaken quote checks.
Both original native responses and manifests are preserved; the receipt connects
the paired view to their hashes. All 271 windows on that day are usable. A separate
merge-based verification confirms key/value preservation and immutable originals.

**Verification and provenance.** Thirteen boundary tests pass (seven calendar/
transfer tests and six alignment tests), plus inherited quote-guard checks and
Ruff. Every baseline median/MAD satisfies independent rational-CDF inequalities;
all historical date/count ledgers, 200,181 calendar window slots and 184,011 target
score slots reconcile. Independent OLS error is at most 2.70e−15; 36 prefix checks
include 2023/2024 boundaries. This is independent calculation methodology within
the same assistant task, not a separate external review of the new SPX code.
All 2,847 native data requests succeeded with zero service-error attempts. The
pairing correction required no new call. Central payload inventory: 8,684 files,
2,197,682,952 bytes, excluding its inventory/dictionary and root registry Markdown.
Central registration/provenance commit: `82df4f5a30a95b153df5b0973c244eaead6c818b`.

**What this establishes.** The SPX historical measurement and its same-hour ruler
are ready for a separately defined outcome comparison. The half-year plots describe
absolute acceleration magnitude in historical MAD-scale units, both signs, with
coverage shown; overlapping endpoints are not independent trials. Partial 2026 H2
ends September 18. This does not show that SPX IV improves B09, B07 or B05, nor
extend the existing sector MAD history back into 2024. No such outcome test ran.

- [Full SPX findings and calculation](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/FINDINGS.md).
- [Half-year magnitude plot](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/magnitude_bins_by_half_year.png).
- [Protocol](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/PROTOCOL.md) and [pairing addendum](/Users/dgrissen/Dev/delta_bomb/outputs/spx_iv_mad_2024_2026_2026-09-20/PROTOCOL_ADDENDUM.md).
- Central native/derived dataset: `/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1`.
