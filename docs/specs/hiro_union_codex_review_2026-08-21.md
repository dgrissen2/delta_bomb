## Codex Review — Verdict: FAIL

**Scope**: Full review of the HIRO minute-level lab table builder and U1–U6 union-rule executor
**Files reviewed**: 2

### Findings

| # | Finding | Severity | File:Line | Description |
|---|---------|----------|-----------|-------------|
| 1 | Incomplete sessions are silently accepted as full days | CRITICAL | scripts/hiro_lab.py:31-32 | The inner merge has no session-completeness validation. The generated 2026-08-21 table contains only 358 rows ending at 15:27, versus 391 rows through 16:00 on the other days, yet it is counted as the eighth session. This silently understates trigger opportunities and biases per-day portfolio statistics. Missing HIRO minutes are also converted to zero flow by the earlier reindex rather than distinguished from capture gaps. |
| 2 | Truncated horizons are mislabeled as timeouts | CRITICAL | scripts/hiro_union_rules.py:90-104 | `min(..., n - 1)` shortens a trade at the end of available data, but the result remains `"timeout"` instead of censored/undefined. This occurs by construction for sufficiently late U3 and U6 triggers even on a complete day: their allowed trigger times plus 30/45-minute horizons extend past 16:00. The final-bar fallback can additionally execute at that bar’s close using a condition learned from the same close. |
| 3 | Timeout horizon is off by one and uses the wrong execution price | CRITICAL | scripts/hiro_union_rules.py:90-104 | Entry begins at `i + 1`, but `end = i + 1 + TIMEOUT` combined with an inclusive loop evaluates `TIMEOUT + 1` bars. A synthetic 60-minute timeout is reported as 61 minutes. On timeout, the executor then exits at `close[end]`, contradicting the documented next-bar-open convention and using a price that cannot be acted upon after observing that completed bar. |
| 4 | Adverse excursion uses inconsistent holding intervals | HIGH | scripts/hiro_union_rules.py:93-105 | `worst` is updated with the entire completion bar before testing the touch, so it may include an extreme occurring after completion even though intrabar order is unknown. Conversely, a scratch exits at `open[j+1]`, but that exit price is excluded from adverse excursion. This can both overstate and understate risk; current fills already disagree with the lab’s touch-bar-excluded metric. |
| 5 | A valid no-trade result crashes after overwriting output | HIGH | scripts/hiro_union_rules.py:137-142 | If no portfolio rule fires, `port` has no columns. The code first overwrites `union_trades.csv` with an empty file and then raises `KeyError: 'day'` during `groupby`. No-trade periods are a legitimate executor outcome and require a structured empty result. |
| 6 | Portfolio statistics omit zero-trade days | MEDIUM | scripts/hiro_union_rules.py:141-148 | `byday` is built only from days represented in `port`. Any session with no trades disappears from the printed table, and `byday.fills.min()` cannot report the correct zero minimum. Reindexing to all `days` is required before calculating daily statistics. |
| 7 | Missing SpotGamma daily features fail silently | MEDIUM | scripts/hiro_lab.py:79-80 | Missing dates are silently replaced with `NaN` without validation or warning. This is occurring for 2026-08-21, where every `vt` and `sgidx` value is missing. Downstream comparisons can then silently exclude that session instead of exposing an incomplete input contract. |

### Dimension Summary

| Dimension | Rating |
|-----------|--------|
| API correctness | Pass |
| Logic errors | Fail |
| Data contracts | Fail |
| Edge cases | Fail |
| Silent failures | Fail |
| Security | Pass |
