# SPX MAD history — complete

Calculated and verified for 681 target sessions, January 2, 2024–September 18, 2026,
with 60 preceding sessions beginning October 5, 2023. Underlying SPX; PM-settled
SPXW options. Native observations retain the prior 09:30–14:29 ET scope; complete
window endpoints begin 09:59, and early closes end 12:59.

183,844 / 184,011 target windows scored (99.91%); all 3,405 hourly baselines usable.
167 unavailable windows remain explicit on April 9, November 20 and November 28,
2025. The first two dates have sampled spot values outside the downloaded strike
range. June 9, 2026's native IV-superset inconsistency was resolved by the documented
lossless pairing repair, retaining every Greek key and all original native data.

All 2,847 data requests succeeded, with no service-error attempts or extra calls
for the pairing repair. Thirteen boundary tests and Ruff pass. All 3,405 baselines,
prior-date/count ledgers, 184,011 target score slots and 200,181 calendar windows
passed independent calculation checks; 36 causal prefix checks passed. The pairing
has a separate independent merge-based verification.

Report, tables and half-year plots: FINDINGS.md. Central payload and provenance:
/Users/dgrissen/Dev/central_trade_data/thetadata/spx_iv_mad_2024_2026_2026-09-20-v1
Central registry commit: 82df4f5a30a95b153df5b0973c244eaead6c818b.

No B0x transfer or SPX trading outcome test is part of this measurement task.
The separate strategy review is committed as c2cd887 (original FAIL; revised
CONDITIONAL PASS), with the remaining conditions and reviewer scope deviation
recorded in the adjacent b09_mad_followup_plan slug.
