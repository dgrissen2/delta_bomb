# Reproducing the SPX measurement

Use the project Python environment with the installed ThetaData SDK and the
existing authenticated data subscription. The native and derived dataset lives
under central_trade_data; it is intentionally not duplicated into this repository.
Its immutable protocol manifest identifies every scientific input by SHA-256.
REPRODUCTION_FILES.json inventories the project files needed by the adapter.

The SPX adapter reuses the earlier sector calculation without editing it. The
legacy collector imports sample_days.py and fetch_spx_coverage.py and reads its
historical selected_days.csv at import time. Those files are included only to
preserve the existing module import contract. SPX uses its own full calendar and
all regimes; the old 50-day sampling logic and outcome calculations do not run.
The guarded-recovery functions are extracted from the already committed evidence
archive. Their source hash and boundary checks remain in the frozen protocol.

This run also has a frozen additive endpoint-pairing exception for June 9, 2026.
From the archived native inputs, run `repair_endpoint_superset.py` before the final
`spx_mad.py --phase derive`; it reuses or creates the paired view and records its
provenance. Then run `verify_endpoint_pairing.py` and `diagnose_gaps.py` before
`report.py`. The original native manifests are intentionally unchanged. The
addendum explains the strict-superset boundary; this is not a general inner-join
fallback for missing Greek data.

While a collector is active, do not start a second collector. After it finishes,
`spx_mad.py --phase derive` reuses captured inputs, runs derivation if needed, and
verifies the result. `report.py` produces the coverage tables and magnitude plots.
`register.py` records the dataset dictionary, inventory and root registry entries.
Writes to existing frozen files must match exactly; do not overwrite caches to
make a changed calculation appear to be the original experiment.

Scientific inputs and prior data remain unchanged. The operation adds SPX native
options and derived features only; it neither changes B0x signals nor joins trade
outcomes. The inherited root and per-dataset central manifests are prerequisites,
so this project commit alone is not a redistribution of the licensed raw data.
