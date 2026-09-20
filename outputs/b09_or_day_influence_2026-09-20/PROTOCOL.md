# B09 OR day influence — fixed diagnostic

Requested September 20, 2026. This is a post hoc sensitivity check of the existing
B09 + (sector F4 OR SPX_F) cohort, without spacing. No rule or outcome is changed.
The objective remains +5 before −10 in 60 native minute bars including entry;
only target_first is a win, and all other outcome labels stay in the denominator.
Entries use the original causal above-VT eligibility, not future session prices.

Reuse the frozen memberships, outcomes and 239 research dates from
`/Users/dgrissen/Dev/central_trade_data/thetadata/mad_transfer_spx_2026-09-20-v1`.
Check their recorded SHA-256 hashes before calculation. These are selected research
dates, not every market session. Scope is January 2025–September 18, 2026.

For the pooled period and each half-year, remove each research date in turn,
including zero-entry dates. For W wins and N signals, removing a day with w wins
and n signals yields (W−w)/(N−n). Report the change in percentage points and
remaining outcome counts. Undefined ratios stay missing, never zero. Verify every
row independently by filtering original entry records and recounting outcomes.

Report daily signal/winner counts; active and winning days; top 1/3/5 day shares
of all wins; and leave-one-day-out minimum/maximum rates with dates. Define the
"most-winner day" by absolute target count, breaking ties by earliest date and
recording all ties. Separately identify the day whose deletion reduces hit rate
most; these are different definitions and can select different dates.

For context only, remove the same dates from plain B09 and report the change in
the descriptive OR-minus-parent hit-rate gap. No new filter, cohort search or
inferential claim is introduced. Sensitivity ranges are NOT confidence intervals;
they do not adjust for rule selection, serial dependence or regime changes.
Concentrated winners need not mean erroneous or untradeable entries; repeated
signals may share the same market move. Do not count them as independent trials.

Save derived tables and a hashed receipt under
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_or_day_influence_2026-09-20-v1`.
Keep code and findings in this project slug. Preserve original datasets, notebook,
dashboard and unrelated work. No new data requests or external reviewers.
