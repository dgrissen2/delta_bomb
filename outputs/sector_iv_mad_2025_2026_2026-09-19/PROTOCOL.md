# XLRE, XLF and XLU: daily historical MAD baselines

Authorized September 19, 2026. Interpret XRE as XLRE. Complete XLRE, followed by
XLF and XLU, using the same approved measurement and date scope. All completed
NYSE sessions January 2, 2025 through September 18, 2026 (429 sessions), plus
sixty warmup sessions October 7–December 31, 2024. No future 2026 data, outcomes,
VT selection, dashboard changes, parameter optimization or tenor-policy changes.

Use the existing verified NYSE calendar (including January 9, 2025 closure).
Native one-minute quotes, 09:30–14:29 ET; on early closes use only 09:30–12:59.
No after-close observations enter. Earliest measurement is 09:59. Keep all
calendar sessions even when quotes or permitted expirations are unavailable.

Reuse immutable raw inputs with exact request parameters and verified SHA-256;
obtain missing data only through ThetaData SDK, stored under
/Users/dgrissen/Dev/central_trade_data/thetadata/sector_iv_mad_2025_2026_2026-09-19-v1/.
Dated quote-contract listings, at most65DTE; 30-calendar-day ATM IV from the same
8–65DTE bracketing selector, strike interpolation and call/put variance average.
Provider SOFR/latest/default model assumptions, both rights, strike_range30,
original 1m IV and matching first-order endpoint required. Do not substitute
current holdings, a different expiry, a different quote model, or inferred IV.
Use two request workers and the existing renewable authentication/two-attempt
cache wrapper. Budget at most10,000 explicit data attempts, immutable restart.

Primary only: strict exact → strict ±2-minute neighbor in the target's same
09:30-anchored hour block and original [end−29,end] window → guarded recovery at
the original minute. Earlier wins distance ties. Recovery uses the committed
100% spread ceiling, prior-quote, one-sided-shock and all existing positive-dollar-
quote checks. Extra guards apply to fallback only. Reuse whole observations,
deduplicate actual source timestamps, assign actual fifteen-minute halves, fit
OLS against elapsed time. Keep a=(b2−b1)/15 in IV points/min². Two distinct
points per half is mathematical identifiability, not a calibrated quality cutoff.
Preserve source provenance and actual-time support; no recursive fill.

For EVERY target date and each of five 09:30-anchored endpoint-hour blocks:
use exactly60 strictly prior calendar sessions, same ETF, both acceleration signs,
all regimes. Each contributing date receives equal total weight, and its windows
share that weight equally. Keep original left-inverse weighted median convention,
MAD=weighted_median(abs(a−median(a))), scale=1.4826*MAD. Fewer than10 contributing
dates or scale<=1e−12 is unavailable. Store center, MAD, scale, source dates and
counts. Current signed magnitude M=−a/scale; downward-only magnitude additionally
requires b2<−1e−12 and a<−1e−12. No recovered bid-IV uncertainty band is fabricated.

Recompute every current endpoint and distinguish missing current measurement,
unavailable baseline, and valid normalized score. Save calendar/date/ETF/hour
coverage and missingness, source series, windows, baselines and scored windows
centrally with project links. Retain original pilot artifacts and verify identical
XLRE pilot results. No win-rate or option-profitability claim follows from coverage.
Document actual collection counts, remaining structural gaps and verification.
