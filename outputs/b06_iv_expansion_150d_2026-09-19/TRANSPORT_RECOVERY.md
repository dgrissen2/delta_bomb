# SDK authentication recovery, recorded before new outcomes

The first collection stopped after 507 of 1,941 date/ETF/expiry pairs were
checkpointed. Some late requests returned UNAUTHENTICATED; those are transport
failures, not absent market data. The interrupted manifest is preserved in
`collection_interrupted_auth.json`, and every attempted request remains in the
central `requests.jsonl`. A freshly authenticated client successfully recovered
the first failed implied-volatility request (XLY, September 18, 2025, expiry
October 17, 2025: 23,400 rows).

`resume_collect.py` supplies a client that renews authentication every five
minutes, after its existing calls finish. A first authentication failure can
trigger renewal and the one remaining request attempt. A second authentication
failure stops the queue. The original maximum of two attempts per request key
still applies, including attempts in the interrupted run and the recovery probe.

This is a transport-only change. The frozen sampling, collection parameters,
source cache identity, expiry limits, interpolation, four IV policies, feature
windows and outcome score are unchanged. Successful cached responses are read
without refetching. Frozen `collect.py`, `iv_rules.py` and `recalculate.py` are
unchanged. All new raw responses and derived minute and sector features live
under `/Users/dgrissen/Dev/central_trade_data/thetadata/b06_iv_expansion_150d_2026-09-19-v1/`.

This recovery was implemented while the feature watcher was still collecting
inputs and before scoring the additional 100 days. No replacement dates were
selected. The 22 sector-days without an allowed expiry bracket remain missing.

## Final validation compatibility, also before new outcomes

All 1,941 pairs completed with zero final failed pairs. Final feature validation
then stopped because pandas retained object dtype for a numeric acceleration
column after concatenating zero-row panels. NumPy's `isnan` rejected that
container, before the feature freeze or new outcome scoring.

`resume_features.py` converts only already-real numeric object containers to
float64 at the assertion boundary. Strings and other nonnumeric values are
rejected. All original tolerance options, values and classifications stay the
same; `recalculate.py` and cached panel files remain unchanged. The adapter and
its SHA-256 are recorded in `validation_compatibility.json` before new outcomes.
Checks confirm NaN preservation, rejection of nonnumeric values, and failure of
an assertion outside the unchanged tolerance. This is a representation fix in
verification, not a relaxed comparison or a strategy/data-quality rule change.
