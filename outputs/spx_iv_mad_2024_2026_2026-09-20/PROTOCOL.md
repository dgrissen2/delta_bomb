# SPX IV acceleration and MAD history from 2024

Authorized September 20, 2026. Target every completed regular cash-equity session
January 2, 2024–September 18, 2026 (681 sessions), in every regime. Include sixty
prior sessions beginning October 5, 2023 (741 dates total). Reuse the verified
2024–2026 calendar, including January 9, 2025 closure. Added warmup holidays:
November 23 and December 25, 2023; November 24 closes early. Reference:
https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx

Underlying is SPX. Request only native SPXW PM-settled options, without mixing
AM-settled SPX contracts. SPXW options are on SPX itself, not an ETF proxy.
https://docs.thetadata.us/Articles/Data-And-Requests/Symbology.html
https://docs.thetadata.us/Articles/Data-And-Requests/Data-Issues.html

Same frozen scientific functions as the eleven-sector run: 30-calendar-day ATM
IV, selected listed expirations bracketing 30 within 8–65 DTE; an exact 30-day
expiry alone is sufficient. Spot-strike interpolation and call/put variance
average. Native SDK IV and matching first-order histories, both rights, one-minute
interval, strike_range=30, SOFR/latest/default model. The provider model is not
overridden. Match both endpoint quote keys and prices. Request09:30–14:29 ET;
derive through12:59 on early closes. This retains the earlier measurement hours.

Strict exact → strict ±2-minute source → original-minute guarded recovery. All
sources stay within the actual thirty-minute window and target's hourly block;
earlier source wins ties. No recursive fill or farther-strike reselection.
Recovery requires the inherited quote guards and100% spread ceiling; positive
dollar bid/ask and underlying price remain mandatory. A zero bid IV is not a
zero dollar bid. Deduplicate actual timestamps. Actual-time OLS in each fifteen-
minute half, a=(b2−b1)/15; inherited minimum two distinct observations per half.

For each date/hour, exactly60 strictly prior calendar sessions, same instrument
and endpoint block, both signs/all regimes, equal total weight per contributing
date. Exact integer-weight lower median and MAD; scale=1.4826×MAD. At least10
contributing dates and scale>1e−12, else unavailable. Signed score=−a/scale;
absolute magnitude=abs(a)/scale. Downward-only also requires b2<−1e−12 and a<−1e−12.
These are measurement features, not probabilities or new strategy thresholds.

Separate additive central namespace:
/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1
Native responses, parameters, hashes, date/expiry choices, source minutes, window
support, historical baseline ledgers, scores and missingness are retained. No
prior native or sector file is modified. Exact matching external cache is reused.
Registry operation: reversible additive backfill; journal and dictionary updated
and committed before declaring completion.

Four SDK workers and two calculation workers. Maximum12000 explicit attempts.
Two normal attempts per request; one separately logged exclusive30-second-cooled
third attempt only for INTERNAL. HTTP502/503 pauses the queue. No continuing
outage is relabeled as absent historical data. Boundary probes use needed inputs
on first warmup, first target and last target dates; their files are reused.

Verify calendar and half-day boundaries, unchanged quote rules and formula,
every baseline through independent rational-CDF inequalities, every historical
date/count ledger, every score and actual-time OLS, and source-prefix causality.
Independent verifier is the earlier verifier with dynamic target count and added
2023/2024 prefix cases; original sources stay immutable. Produce coverage and
half-year magnitude plots. No B0x outcome test is included in this request.
