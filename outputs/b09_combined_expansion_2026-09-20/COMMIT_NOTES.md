Test the fixed combined B09/B05/B07 expansion with exact overlap and policy accounting

Follow the user's explicit request to combine all three previously separate
opportunity expansions. OR existing B09 F4-or-SPX, B05 F4, five-endpoint B09
persistence and original B07 six-sector acceleration; do not change definitions,
apply persistence to other parents, add volume/skew, or sweep thresholds/subsets.

Use unchanged 239 research dates in 2025 through September 18, 2026. Preserve
native SPX entries, strict causal above-VT admission, +5 before -10 in 60 native
minute bars including entry, and all non-target outcomes in the denominator.

Deduplicate exact Eastern execution minute, retaining all contributing routes.
The separate additions 105+174+90=369 share two timestamps. One shared B05/B07
entry wins and one shared persistence/B07 entry reaches neither barrier. Distinct
additions are 367 with 229 wins; combined is 427/685=62.3%, versus198/318=62.3%.
Added-only rate62.4%; active dates121 to163, median research-day signals1 to2.

Report all halves: combined127/205,159/268,115/173,26/39 versus baseline58/96,
78/130,50/74,12/18. Preserve sparse final-half uncertainty. Pooled whole-date95%
interval57.5–66.8%; paired accuracy change+0.07pp[-3.82,+4.04], not noninferiority.

Recompute spacing on the full union rather than summing component policies.
60-minute baseline107/175=61.1%, combined191/327=58.4%; newly kept184/108 winners,
displaced32/24, net+152/+84. First/day70/121 to95/163. Keep the weaker2025H2
spaced52.5%; no policy selection or rescue filter from these results.

Expose concentration: additions on already-active dates189/279=67.7%, entirely
new dates40/88=45.5% across42 dates. Date labels can depend on later baseline
signals and cannot be used as live gates. Single-date deletion leaves61.8–62.8%;
top-five winning days49/427=11.5%. Sensitivity is not a confidence interval.

New outcome-free membership freeze hashes source data, protocol and reused
helpers before scoring this union, while acknowledging component outcomes were
already known. Four boundary tests/Ruff; independent reconstruction of685route
memberships and native entry/VT/barrier paths,239source hashes,35summary rows,
15policy changes,19route pattern rows,10new-date rows,956day deletions and5000
pooled paired-bootstrap draws;60previous component summary cells reconcile.

Write all derived data centrally with dictionary, changelog, hashes and receipts.
No new provider calls, modifications to source data, dashboard or trading rules.
The earlier Claude proposal review is not approval of these new results. Prior
search, reused history and clustered dates remain; no independent reviewer ran.
Preserve unrelated concurrent changes; commit only this combined experiment.
