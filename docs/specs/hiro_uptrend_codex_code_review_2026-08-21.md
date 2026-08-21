## Codex Review — Verdict: FAIL

**Scope**: Full correctness, causality, data-contract, edge-case, silent-failure, and security review of the UP-trend HIRO dashboard and confirmation pipeline.
**Files reviewed**: 2

### Findings

| # | Finding | Severity | File:Line | Description |
|---|---------|----------|-----------|-------------|
| 1 | Post-entry invalidation is used as an entry gate | CRITICAL | scripts/hiro_uptrend_confirm.py:92-103 | `invalidated()` examines flow during `t+1…t+3`, but `~e.inval` is then included in `SIMPLE (all four)` and the survivors are reported as “entries.” Because execution occurs at `t+1` open, this is future information, producing survivor/look-ahead bias. The current data improve from 0.59 to 0.65 `w5` and from 0.18 to 0.10 `a10` after this retrospective removal. Invalidation must instead be modeled as post-entry trade management with an explicit exit outcome, or execution must be delayed until the window closes. |
| 2 | Episode selection permits overlapping active trades | CRITICAL | scripts/hiro_setup_dashboard.py:71-79 | A new episode is created whenever fire observations are separated by more than two minutes, without requiring a run break or checking whether the prior +5/60-minute trade remains active. The confirmation script evaluates every such row independently. In the supplied artifacts, 12 of 32 entries occur before the preceding modeled +5-or-60-minute exit, violating the stated one-unpaired-leg constraint and silently overstating the executable sample. |
| 3 | Right-censored outcomes are counted as failures | CRITICAL | scripts/hiro_setup_dashboard.py:83-91; scripts/hiro_uptrend_confirm.py:84-86 | Fires are allowed through 15:45, but market data end at 16:00. Rows after 15:00 therefore lack a complete 60-minute horizon. Missing touches are stored as `NaN`, then comparisons such as `min_to_5 <= 60` convert them to `0.0`. The current sample includes fires at 15:09 and 15:10; excluding incomplete horizons changes `w5` from 0.531 to 0.567 and its clock-matched baseline from 0.413 to 0.440. Outcomes need horizon-completeness flags, and each statistic must exclude censored rows. |
| 4 | “30-bar” pullback can use as few as five bars | HIGH | scripts/hiro_setup_dashboard.py:47 | `rolling(30, min_periods=5)` does not implement the documented 30-bar rolling high. It admits early-session signals with materially shorter histories; the current 09:47 fire uses only 18 session bars. Require 30 observations or explicitly redefine and label the feature as an available-history/session-high pullback. |
| 5 | Steep states are labeled “no entry” but still fire | HIGH | scripts/hiro_setup_dashboard.py:69-70 | `steep` is calculated, but `fire` does not exclude it. Eight of the 32 current `fire_first` rows are steep, so they enter dashboard statistics and appear as entry markers inside shading described as “no new entry.” Either apply `& ~steep`/the approved steep gate to entries or relabel steep as diagnostic-only and keep it out of no-entry claims. |
| 6 | Confirmation glob can silently mix stale sessions | MEDIUM | scripts/hiro_uptrend_confirm.py:22-31 | `docs/dashboard/hiro_setup_2026-*.parquet` loads every matching artifact, although the analysis claims exactly five captured sessions. A stale or newly generated 2026 parquet silently changes the sample, and no expected-day, schema, uniqueness, or row-range validation exists. Use an explicit manifest/day list and validate each input contract. |
| 7 | Intended secondary run-rate axis is not created | MEDIUM | scripts/hiro_setup_dashboard.py:141-142 | Passing `yaxis="y4"` is overridden when `add_trace(..., row=3, col=1)` assigns the trace to `y3`; the subplot has no `yaxis4`. Run rate and 15-minute flow therefore share one scale, while the threshold line is also placed on the flow axis. Configure row 3 with `secondary_y=True` and add/update the trace and threshold on that axis. |
| 8 | Empty input or no-fire cases crash | MEDIUM | scripts/hiro_uptrend_confirm.py:28-60; scripts/hiro_uptrend_confirm.py:75-79 | No matching parquet files cause `pd.concat([])` to fail, while an empty fire set causes `np.average()` to raise `ZeroDivisionError`. These are plausible out-of-sample states. Validate inputs explicitly and return/report an empty analysis without calling clock-matched aggregation. |

### Dimension Summary

| Dimension | Rating |
|-----------|--------|
| API correctness | Concern |
| Logic errors | Fail |
| Data contracts | Concern |
| Edge cases | Fail |
| Silent failures | Fail |
| Security | Pass |
