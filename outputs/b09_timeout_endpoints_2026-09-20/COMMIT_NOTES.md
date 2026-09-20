Describe 60-minute endpoints for neither-barrier B09/B05/B07 entries

Answer the user's conditional question for each standalone rule and the
deduplicated combined set: among entries that never touch+5 or-10 during the
original hour, where does SPX finish relative to entry? Keep actual minute
high/low barrier touches, native60-bar clock, strict causal above-VT and no spacing.
Do not conflate this group with all non-adverse-first entries or revise hit rates.

Neither counts43/318baseline,5/112B05F4,73/492persistence,15/91originalB07,
92/685combined. Combined endpoints median-0.33,mean-0.70,p10-5.17,p90+3.64,
min-7.48,max+4.82;43positive,48negative,1flat on57dates. Baseline median+0.07,
B05-2.14,persistence-0.26,B07-0.77. All pooled sample means are modestly negative;
small groups, especially five B05 cases, do not establish distinct behavior.

Preserve per-half distributions and sparsity: combined2025H1mean-2.65/median-2.55
on21cases;2025H2-0.22/+0.26on53;2026H1+0.25/+0.37on16;partial2026H2only2cases.
These distribution percentiles are not confidence intervals or independent trials.

Use close(T+59)-open(T) at the inheritedT+60boundary, never close(T+60).
Replay92complete native paths,5520supporting bars, immutable source hashes on57
dates, no high/low barrier touches and causal VT;43baseline endpoints exactly match
the prior path-distribution output. Reuse validated path/quantile code, separately
check endpoints and scalar quantiles/means/counts across25groups and150fixed bins.
Ruff passes and plot visually inspected. No new provider calls or data inference.

Save exact dated event values, route flags, native paths, pooled/half statistics,
fixed histograms and empirical distributions centrally. Add project findings,
common-scale five-panel chart, reproducible script/protocol and provenance receipt;
append the central dictionary/changelog without disturbing concurrent work.
All prior source outcomes and strategy definitions remain unchanged.
