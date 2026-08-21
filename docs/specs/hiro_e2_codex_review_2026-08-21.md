## Codex Review — Verdict: FAIL

**Scope**: Single-file review, emphasizing E2 correctness and trading-decision reliability
**Files reviewed**: 1

### Findings

| # | Finding | Severity | File:Line | Description |
|---|---------|----------|-----------|-------------|
| 1 | E2 control omits treatment’s price-state condition | HIGH | scripts/hiro_experiments.py:94 | The treatment requires `close` below the 30-bar midpoint, but the purported “same bounce without divergence” control does not. It therefore mixes different price-location regimes and cannot isolate the C/P divergence. On the current data, adding the missing condition changes the control from 19 episodes with an 84.2% −3 fill rate to 16 episodes with an 87.5% rate, materially weakening the apparent incremental E2 effect. |
| 2 | Rolling state leaks across session boundaries | HIGH | scripts/hiro_experiments.py:77,113-116 | `shocked`, `shock_recent`, `diff(3)`, and the post-transform shifts operate across the concatenated multi-day frame rather than within each day. Although this does not contaminate E2, it silently creates invalid E1/E4 state at session boundaries. In the current data, grouping only `shock_recent` by day removes a false E4 episode at 08:22 on 2026-08-21. |
| 3 | E2 report lacks an uncertainty guard for a trading decision | MEDIUM | scripts/hiro_experiments.py:93-95 | The report presents 9/9 as a point estimate without confidence intervals, day-clustered resampling, or a direct treatment-versus-state-control test. The existing control is already 16/19, and the correctly midpoint-matched control is 14/16; a one-sided Fisher comparison against the corrected control is not significant (`p=0.40`). The script can therefore promote a small-sample descriptive result as actionable evidence. |

### Dimension Summary

| Dimension | Rating |
|-----------|--------|
| API correctness | Pass |
| Logic errors | Fail |
| Data contracts | Fail |
| Edge cases | Concern |
| Silent failures | Fail |
| Security | Pass |
