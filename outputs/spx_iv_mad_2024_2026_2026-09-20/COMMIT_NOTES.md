# SPX IV/MAD history and extensive learning notes

Add the isolated SPXW calendar/contract adapter, verified native-data measurement,
coverage tables, score links, half-year plots and reproducibility documentation.
Record all results and limitations in canonical notebook section 11.33.

681 target sessions plus 60 warmup; 183,844/184,011 scored windows (99.91%);
3,405/3,405 usable hourly baselines. Preserve 167 missing windows on three dates,
including documented native strike-range limitations on two large-move dates.
Keep identical sector formulas, tenor interpolation, actual-time slopes, neighbor
rules, fallback guards, prior-history construction and exact weighted calibration.

A one-date native IV/Greek contract-set inconsistency initially stopped derivation.
Preserve the original failure and raw files; document and freeze a strict IV-
superset pairing repair, with unchanged native values and every Greek key retained.
Six fail-first boundary tests and an independent real-data merge replay validate
that repair. The full runner then completes all original verification checks.

Thirteen tests and Ruff pass; independent rational-CDF checks verify all baselines,
all date/count ledgers and scores reconcile, OLS errors remain below 2.70e-15,
and 36 source-prefix checks pass. Preserve prior scientific code unchanged; include
its previously untracked source dependencies and import-only support files so the
new adapter is reproducible. Licensed raw payloads stay under central_trade_data;
project data artifacts are symlinks to that central namespace.

No B0x strategy outcome study or new threshold search is included. The separate
Claude strategy review remains in c2cd887 with its conditional verdict and scope
disclosure. All unrelated project edits remain unstaged.

Central registry commit: 82df4f5a30a95b153df5b0973c244eaead6c818b.

Update the active follow-up proposal’s SPX readiness status after completion; preserve both reviewed snapshots and their actual verdicts.
