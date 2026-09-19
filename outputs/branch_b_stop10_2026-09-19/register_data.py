"""Register the paired barrier sensitivity and its exact immutable lineage."""
import json

import pandas as pd
import pyarrow.parquet as pq

from rescore import DATA, OLD, OUT, ROOT, digest, verify_freeze, write_json

SECTION = 'BRANCH-B-STOP10'


def main() -> None:
    verify_freeze()
    if (DATA/'inventory.json').exists() or SECTION in (ROOT/'DATA_DICTIONARY.md').read_text():
        raise FileExistsError('Barrier rescore already registered')
    records = []
    for path in sorted(DATA.iterdir()):
        if not path.is_file():
            continue
        record = {'path': path.name, 'bytes': path.stat().st_size, 'sha256': digest(path)}
        if path.suffix == '.parquet':
            p = pq.ParquetFile(path)
            record.update(rows=p.metadata.num_rows, schema=str(p.schema_arrow))
        elif path.suffix == '.csv':
            frame = pd.read_csv(path)
            record.update(rows=len(frame), columns=list(frame.columns),
                          dtypes={c: str(t) for c, t in frame.dtypes.items()})
        records.append(record)
    inventory = {'namespace': str(DATA), 'parent_namespace': str(OLD), 'status': 'complete',
                 'files': len(records), 'bytes': sum(r['bytes'] for r in records),
                 'scope': 'Payload excludes namespace inventory/dictionary and root registry Markdown',
                 'api_calls': {'thetadata': 0, 'orats': 0},
                 'code_hashes': {str(p): digest(p) for p in OUT.glob('*.py')},
                 'findings_sha256': digest(OUT/'FINDINGS.md'), 'entries': records}
    write_json(DATA/'inventory.json', inventory)
    dictionary = f'''# Branch B +5 before −10 in 60 minutes

Namespace: `{DATA}`.
Parent immutable experiment: `{OLD}`.
Code, protocol and full findings: `{OUT}`.

User-requested change to the adverse scoring barrier only: −15 to −10 SPX points.
Target remains +5, horizon 60 native minute bars starting at entry open, ending
minute +59. Same tolerance 1e-8; first double-touch minute ambiguous. Neither and
ambiguous stay in N. Posttarget reversals never change success. No inferred
intraminute order or new data requests.

Same 421 selected dates from the parent 681-session 2024–2026 audit. Primary
research excludes ten development dates, leaving 411. Half-year research counts
87/85/62/92/67/18; 2026 H2 ends September 18. Same 21,239 raw identities and 20,821
distinct variant/date/minute opportunities. Strict VT gates verified directly
from native observations: every earlier RTH minute low plus entry open strictly
above same-date VT. 16,379 strict opportunities include development; 16,016 exclude
development. No new signal, population, warmup, IV, threshold or eligibility rule.

All original −15 outcomes, touch times, entry prices and endpoint changes reproduced;
both barriers independently checked via sequential native scans. New target-first
outcomes must be a subset of old ones. All 390 summary denominators and original
outcome counts match prior evidence. Twelve targeted scorer tests and Ruff pass.

Pooled research: thrust 61/92 →59/92 (66.3%→64.1%), thrust/staircase 184/317→180/317
(58.0%→56.8%), opening-range immediate 153/260→145/260 (58.8%→55.8%), plain B06
1,241/2,382→1,208/2,382 (52.1%→50.7%). B06 loses 33 winners, all to definite
−10-first, and 209 old neither outcomes become adverse-first. Its new outcome
distribution is 1,208 target /485 adverse /689 neither /0 ambiguous. Opening-range
retest remains sparse at 37/61 (60.7%) and weak in 2024. No option P&L model.

Thrust and thrust/staircase exceed all-entry B06 in all six halves; opening-range
immediate trails B06 in 2024 H2. First-per-day thrust remains 48/68 (70.6%) and
60-minute-spaced thrust remains 55/81 (67.9%) under both barriers. These are fixed
sensitivities, not optimized selection rules. Individual-rate and paired-change
95% intervals resample whole dates 10,000 times, seed 20260919, including zero-event
dates. They do not remove serial dependence or earlier research selection.

## Files and fields

- input_freeze.json: protocol, code, parent ledgers, exact native/history/note hashes,
  score, cohort and bootstrap definitions frozen before new outcomes.
- event_outcomes.parquet: all 21,239 raw records. `outcome`/`first_touch_min` now
  refer to −10; `outcome_15`/`first_touch_min_15` preserve old scoring. Other event
  fields unchanged. Native prices and provenance remain in original source paths.
- distinct_event_outcomes.csv: 20,821 unique variant/date/minute opportunities.
- comparison.csv: 13 variants ×10 cohorts ×3 sensitivities =390 rows, strict VT
  only. Cohorts: six half-years, combined_non_development, new_2024, prior_239,
  development_10. Sensitivities all/first_per_day/spaced60. `target_first`,
  `adverse_first`, `neither`, `ambiguous` refer to −10; *_15 fields to −15.
  N fixed, hit_pct and hit_pct_15 in percent, change_pp=new minus old in percentage
  points. lost_targets=old targets minus new targets. date_ci fields are new-rate
  intervals; paired_change_ci fields resample the same dates for both barriers.
- outcome_transitions.csv: all-entry counts by cohort, variant, old outcome and
  new outcome, including old winners becoming ambiguous versus adverse separately.
- daily_counts.csv: zero-inclusive date/variant/cohort N and new/old target counts
  used for date bootstrap. Primary qualifying dates remain in parent's selected_days.
- score_verification.json: exact original-score reproduction, independent native
  scan, strict VT and identity checks; freezes new raw event ledger hash.
- analysis_verification.json: denominator/outcome reconciliation, strict counts,
  exact summary and CSV hashes.

OHLC/entry/barriers/VT use SPX points, integer minute clocks use ET minutes since
midnight. Rates are 0–100, differences percentage points; no return interpretation.
Every file hash and CSV/Parquet schema is recorded in inventory.json.

Payload: {inventory['files']} files, {inventory['bytes']:,} bytes, excluding this
dictionary, inventory.json and root registry Markdown. Zero API calls. Previous
raw data, source studies, results and dashboard remain unchanged.
'''
    with (DATA/'DATA_DICTIONARY.md').open('x') as file:
        file.write(dictionary)
    section = f'''\n\n## {SECTION} — same entries, +5 before −10 in 60 minutes (2026-09-19)

Namespace: `{DATA}`; parent: `{OLD}`.
Findings/code: `{OUT}`.

Only adverse barrier changes −15→−10. Same 411 research dates (plus ten separately
labeled development dates), thirteen variants, strict above-VT gate and original
signals. 21,239 raw rows;20,821 distinct opportunities;16,016 strict research entries.
All −15 outcomes reproduce; both barriers and prior-only VT flags independently
verified from original native sources. Twelve tests pass;390 paired summary rows
preserve all denominators. New targets are a subset of previous ones.

Thrust 66.3%→64.1% (N92), thrust/staircase 58.0%→56.8% (N317), opening-range
immediate 58.8%→55.8% (N260), B06 52.1%→50.7% (N2,382). B06 loses33 prior
winners and turns209 old timeouts into adverse-first. Thrust and thrust/staircase
still exceed B06 in every half; opening-range immediate fails that comparison in
2024 H2. Full13-row half-year, paired-change, outcome-transition and sensitivity
tables documented, with whole-date intervals. No option profitability claim.

{inventory['files']} payload files /{inventory['bytes']:,} bytes, excluding namespace
inventory/dictionary and root registry Markdown. Zero API calls. Exact schemas
and hashes in namespace inventory. Original experiment remains immutable.
'''
    with (ROOT/'DATA_DICTIONARY.md').open('a') as file:
        file.write(section)
    journal = f'''\n\n## 2026-09-19 — create — paired Branch B −10 adverse-barrier rescore

- **date:** 2026-09-19
- **operator:** Codex / Branch B barrier side conversation
- **repo_session:** delta_bomb
- **op_type:** create
- **paths_touched:** `{DATA}/`; `{ROOT}/DATA_DICTIONARY.md`; `{ROOT}/CHANGELOG.md`
- **size_delta_bytes:** +{inventory['bytes']} (payload; namespace inventory/dictionary and root registry Markdown excluded)
- **file_count_delta:** +{inventory['files']} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** 0
- **reversibility:** reversible (new derived namespace; old data/results untouched)
- **dictionary_section:** {SECTION} and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** {DATA.relative_to(ROOT)}/input_freeze.json, score_verification.json, analysis_verification.json, inventory.json
- **why:** User requested +5 before −10 within60 minutes on the same above-VT research population.
- **verification:** Same21,239 raw identities/20,821 distinct entries, same411 primary dates,16,016 strict research entries. Every old−15 score and touch reproduces; both barriers independently scanned on native data; all VT gates and390 summary rows reconcile; new wins subset old. Twelve tests and Ruff pass. No fetches, tuning or inferred intraminute ordering.
- **findings:** Thrust64.1% (59/92), thrust/staircase56.8% (180/317), opening-range immediate55.8% (145/260), B06 50.7% (1,208/2,382). B06 loses33 wins;209 old timeouts become adverse-first. First-per-day/spaced thrust unchanged. All half-years, uncertainty, transitions and exclusions inherit exact prior population. No posttarget penalty or option P&L inference.
'''
    with (ROOT/'CHANGELOG.md').open('a') as file:
        file.write(journal)
    print(json.dumps({k: inventory[k] for k in ['files', 'bytes', 'api_calls']}))


if __name__ == '__main__':
    main()
