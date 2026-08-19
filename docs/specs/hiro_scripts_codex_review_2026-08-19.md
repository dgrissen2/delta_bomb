## Codex Review — Verdict: FAIL

**Scope**: Full review of both committed analysis scripts, including causal indexing, outcome construction, state classification, source schemas, baseline weighting, and edge-case behavior.
**Files reviewed**: 2

### Findings

| # | Finding | Severity | File:Line | Description |
|---|---------|----------|-----------|-------------|
| 1 | Risk and time metrics ignore the requested horizon | CRITICAL | scripts/hiro_trend_experiment.py:104 | Adverse excursion and time-to-fill are created only from the 60-minute slice, but `evaluate()` returns them for every requested horizon. Consequently, a 15-minute report can show a median time-to-fill greater than 15, while its adverse rate measures a different 60-minute experiment. The corresponding clock-matched adverse baseline has the same mismatch. |
| 2 | Incomplete rolling windows are classified as real states | CRITICAL | scripts/hiro_legin_explore.py:86 | Comparisons with `NaN` are false, so unavailable rolling features become `FLAT`; agreement branches similarly become `MIXED` or `OTHER`. In the current data this silently classifies 45 incomplete 15-minute rows and 120 incomplete 30-minute rows as genuine states, contaminating their outcome rates with early-session observations. |
| 3 | Pullback anchors are not scoped to the active trend | HIGH | scripts/hiro_trend_experiment.py:65 | Running highs and lows begin at 09:30 and never reset when a trend starts. An UP-state rally still below an old morning high can therefore be called a pullback, while a DOWN-state decline above an old low can be called a bounce. This can systematically depress the UP branch and inflate the DOWN branch instead of measuring entries “in the middle” of the detected trend. |
| 4 | Decision and execution use the same completed bar | HIGH | scripts/hiro_trend_experiment.py:68 | State features include HIRO and price data through minute `i`, and the current bar’s close/high/low determine both the trigger and assumed close-price entry. The completed close cannot also be an attainable post-decision fill. Shift features to bars through `t-1` and execute at the next open, or explicitly frame this as a non-executable conditional study. |
| 5 | Full-sample quantiles make several states noncausal | MEDIUM | scripts/hiro_trend_experiment.py:211; scripts/hiro_legin_explore.py:108 | EMA and “strong flow” thresholds are calculated from all five sessions, including future observations relative to each classified minute. Although no outcome column is used, these states cannot be reproduced online and conflict with the scripts’ causal-state claims. Use frozen training thresholds or expanding historical quantiles. |
| 6 | Positional windows silently assume a complete minute grid | MEDIUM | scripts/hiro_trend_experiment.py:74; scripts/hiro_legin_explore.py:61 | Lookbacks and horizons slice by row position without validating consecutive minutes or a complete 60-bar tail. Missing SPX rows would make “30 minutes” span more than 30 clock minutes; truncated tails would silently count hits as false. Missing HIRO minutes are additionally imputed as zero flow by `reindex(..., fill_value=0.0)`. |
| 7 | Every qualifying minute is counted as an independent entry | MEDIUM | scripts/hiro_trend_experiment.py:136 | Continuous qualifying periods generate overlapping entries with nearly identical forward windows. The sweep’s `n >= 30` gate can therefore represent only a few trend episodes, overstating effective sample size and allowing one price move to dominate a cell. Use one entry per trend episode or report episode counts alongside minute counts. |
| 8 | Lift columns are omitted from the results artifact | MEDIUM | scripts/hiro_trend_experiment.py:197 | The CSV is written before `lift_up` and `lift_dn` are calculated. The declared results artifact therefore omits the sweep’s central comparison metric even though it is subsequently used for ranking and reporting. |
| 9 | Price-change percentage uses the wrong denominator | LOW | scripts/hiro_legin_explore.py:129 | The 15-minute price move divides by the current price rather than the lagged price. The numerical difference is small, but observations near the ±4 bp boundary can be classified incorrectly. |
| 10 | Documented retail-agreement analysis is absent | LOW | scripts/hiro_legin_explore.py:5 | The module claims to include a retail-versus-all agreement flag, but `main()` never constructs or reports that comparison. |

### Dimension Summary

| Dimension | Rating |
|-----------|--------|
| API correctness | Pass |
| Logic errors | Fail |
| Data contracts | Concern |
| Edge cases | Fail |
| Silent failures | Fail |
| Security | Pass |
