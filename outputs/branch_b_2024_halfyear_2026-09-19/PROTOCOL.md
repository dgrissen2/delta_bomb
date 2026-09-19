# 2024 extension and half-year comparison

Defined before generating or scoring new events on 19 September 2026. Audit all
252 NYSE sessions in 2024 and preserve the earlier 429-session 2025–2026 audit
through September 18, 2026. No date sampling, cutoff search or recipe changes.

Use the third-tranche provenance parser unchanged: same-date positive VT, matching
saved preopen note, explicit Eastern publication labels all before 09:30, no
conflicting values. Preserve missing/late/conflicting evidence as exclusions.
No inferred, shifted, after-open or carried-forward VT. Prior-evening notes remain
excluded under the existing same-date rule. Historical publication labels do not
prove contemporaneous capture or absence of revisions.

Require a complete valid native 390-minute SPX session and open strictly above VT.
Keep early closes excluded under the inherited full-session rule. Audit every
date, including dates without signals. Reuse immutable native cache first. Fetch
missing 2024 SPX sessions with ThetaData Python SDK index_history_ohlc at 1 minute,
including ineligible dates needed for chronological indicator history. Do not
repair invalid bars, substitute synthetic prices or overwrite a prior source.
Use the existing two-attempt transport ceiling. Stop the queue on a provider
gateway failure and retain explicit pending dates; never call them below VT.

Preserve previous cohort memberships, with all qualifying 2024 dates in new_2024.
Ten original dashboard-development dates remain separate and excluded from every
primary half-year and combined research result. The partial 2026 H2 window ends
September 18. It is not a full half-year or a holdout. Prior reviewed data remain
unchanged. New history may change indicator initialization: record native source
additions/replacements and compare earlier event identities BEFORE scoring. If
any earlier identities change, report the exact differences, then rescore them
consistently; do not choose history based on which results look better.

Use all eight committed frozen entry modules from branch_b_150d_rerun_2026-09-19.
Keep all thirteen rows B01–B10, original clocks and state machines. B03 includes
thrust plus staircase; it is not a pure staircase test. B10 uses the completed
09:30–09:34 opening range. No new IV features, filters or options downloads.

Primary entry gate: every observed minute low from 09:30 through the minute before
entry is strictly above that date's VT, and entry open is strictly above VT. A
prior touch/breach blocks later entries. Do not use the entry minute's subsequent
low or the future full-day status. Other VT gates may appear only as diagnostics.

Score +5 SPX points before −15 within 60 native minute intervals from entry open.
Both first touches in one minute are ambiguous; neither and ambiguous stay in
the denominator. Posttarget reversals have no bearing on success. Count unique
variant/date/entry-minute opportunities, retaining raw overlapping setup records.

Report all six half-years, pooled new_2024, prior_239, pooled research, earlier
cohorts and development separately. Show successful entries/N, hit rate, active
dates, neither/adverse counts, and 95% whole-date bootstrap intervals with 10,000
draws and seed 20260919. Include zero-event qualifying dates. First-per-day and
fixed 60-minute spacing are predeclared sensitivities, not optimized rules.
Preserve prior diagnostic bins. Earlier-hour B01 controls are selected-path
timing diagnostics, not causal uplift. Compare fixed-time period rates descriptively.
Small-N leaders are hypotheses; period variability and dependent signals matter.

Before final reporting, independently reread selected native sources and check
each VT gate, barrier outcome, cohort/period membership and aggregate row. Verify
frozen source hashes and quantify any changes to earlier results. Data, requests,
features, ledgers and manifests go only in:
`/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_2024_halfyear_2026-09-19-v1/`.
Code and findings go in this isolated project slug. Update namespace/root data
dictionaries and changelog, then commit only the scoped new work and registry changes.
