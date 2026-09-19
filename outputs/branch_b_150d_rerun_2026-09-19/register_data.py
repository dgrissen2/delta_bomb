"""Archive provenance and register this isolated replay in the central data catalog."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
ROOT = Path('/Users/dgrissen/Dev/central_trade_data')
V1 = ROOT/'thetadata/branch_b_150d_rerun_2026-09-19-v1'
V2 = ROOT/'thetadata/branch_b_150d_rerun_2026-09-19-v2'
SECTION = 'BRANCH-B-150-REPLAY'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create(path: Path, text: str) -> None:
    with path.open('x') as file:
        file.write(text)


def main() -> None:
    if SECTION in (ROOT/'DATA_DICTIONARY.md').read_text():
        raise FileExistsError('Study already registered')
    source_hashes = json.loads((V2/'input_freeze.json').read_text())['hashes']
    archive = V2/'dashboard_reproduction_inputs'
    archive.mkdir()
    for name in ['manifest.json', 'chart_data.json']:
        source = OUT.parent/'branch_b_above_vt_10d_2026-09-12'/name
        assert digest(source) == source_hashes[str(source)]
        with (archive/name).open('xb') as file:
            file.write(source.read_bytes())
    logs = V2/'review_logs'
    logs.mkdir()
    moved = []
    for name in ['charlie_review.log', 'brent_review.log']:
        source = OUT/name
        target = logs/name
        size, wanted = source.stat().st_size, digest(source)
        source.rename(target)
        source.symlink_to(target)
        assert digest(target) == wanted
        moved.append({'source': str(source), 'destination': str(target),
                      'bytes': size, 'sha256': wanted})
    create(V2/'review_log_move.json', json.dumps(moved, indent=2)+'\n')
    summaries = []
    for directory in [V1, V2]:
        records = []
        for path in sorted(directory.rglob('*')):
            if not path.is_file():
                continue
            record = {'path': str(path.relative_to(directory)), 'bytes': path.stat().st_size,
                      'sha256': digest(path)}
            if path.suffix == '.csv':
                frame = pd.read_csv(path)
                record.update(rows=len(frame), columns=list(frame.columns),
                              dtypes={c: str(t) for c, t in frame.dtypes.items()})
            elif path.suffix == '.parquet':
                metadata = pq.ParquetFile(path)
                record.update(rows=metadata.metadata.num_rows,
                              schema=str(metadata.schema_arrow))
            records.append(record)
        inventory = {'namespace': str(directory),
                     'status': 'unscored_superseded' if directory == V1 else 'authoritative',
                     'date_count': 150, 'date_range': ['2025-02-06', '2026-08-11'],
                     'files': len(records), 'bytes': sum(r['bytes'] for r in records),
                     'scope': 'All namespace payload; excludes inventory.json and DATA_DICTIONARY.md',
                     'api_calls': {'thetadata': 0, 'orats': 0}, 'entries': records}
        create(directory/'inventory.json', json.dumps(inventory, indent=2)+'\n')
        lines = [f'# {directory.name}', '', f'Status: **{inventory["status"]}**.', '',
                 f'Absolute namespace: `{directory}`.', '',
                 f'{len(records)} payload files, {inventory["bytes"]:,} bytes; inventory and this dictionary excluded.', '',
                 'Fixed150 evaluation dates,2025-02-06–2026-08-11. Native SPX minute OHLC;',
                 'all clocks are minutes since midnight in America/New_York, prices in SPX points.',
                 'Indicators use inherited continuous warmup; all original sources are immutable.', '',
                 '## File inventory', '', '| File | Rows | Bytes |', '| --- | --- | --- |']
        lines.extend(f'| {r["path"]} | {r.get("rows", "—")} | {r["bytes"]:,} |' for r in records)
        lines += ['', '## Semantics and schema', '',
                  'Exact columns/dtypes or Arrow schemas, bytes and SHA-256 are in inventory.json.',
                  '`selected_days`: frozen dates, original/additional cohort, same-date VT provenance, native paths/hashes.',
                  '`history_ledger`: every included/excluded warmup source, valid5m counts, complete1m inclusion and reason.',
                  '`five_features` and `minute_features`:150 evaluation sessions with causally warmed features.',
                  '`events_before_outcomes`: raw setup emissions; overlapping setup clocks are retained.',
                  '`setup_ledger`: original state-machine episode records; rows are setups, not trades.',
                  '`day_context`: opening35 range, ATR/cushion, calendar gap and explicitly descriptive full-day breach data.',
                  '`diagnostic_bins`: outcome-free day-level tercile cuts fixed before scoring.',
                  '`*_freeze`: exact input/source/method hashes captured before new-family outcomes.',
                  '`reproduction`:441 original dashboard identities and four temporal-prefix checks.', '']
        if directory == V1:
            lines += ['This preparation omitted35 already-existing non-evaluation warmup sessions.',
                      'It is preserved unscored with7,413 raw events. No hit-rate conclusions use this namespace.',
                      f'Use `{V2}` for authoritative outcomes.']
        else:
            lines += ['`event_outcomes`:7,465 setup records. `distinct_event_outcomes`:7,313 variant/date/minute opportunities.',
                      'Outcome target_first means +5 before−15 within60 native bars starting at entry open.',
                      'Same-minute double touch is ambiguous; neither/ambiguous stay in the denominator.',
                      'Posttarget reversal does not change a win. No option P&L is inferred.',
                      '`always_above`: all prior RTH lows strictly above VT and entry open above VT; future lows excluded.',
                      '`entry_above`: entry-open-only diagnostic; opening_only retains the original opening cohort.',
                      '`comparison`:585 rows:3 gates ×3 sensitivities ×5 cohorts ×13 variants.',
                      'Rates/CI fields are percentage units; control differences are percentage points.',
                      'Date-bootstrap intervals:10,000 resamples,seed20260919,zero-event dates included.',
                      'The same-hour B01 control is earlier than most family entries. Selecting its date/hour using a later',
                      'trigger conditions it on future movement from its own clock. Control differences are timing diagnostics,',
                      'not causal signal uplift or a sufficient promotion criterion.',
                      '`daily_counts`: zero-inclusive date counts; `context_diagnostics`: frozen bins/hour diagnostics.',
                      '`paired_setup_comparison`: delayed-entry selection and missed successful parent setups; setup-unit denominators.',
                      '`existing_iv_coverage_diagnostic`: original IV policy coverage counts only; no IV overlay on these13 rows.',
                      '`warmup_*`:35 added native sources, before/after event identity changes and remaining calendar-gap flags.',
                      '`independent_verification`: every native score/VT flag and all585 comparison rows rechecked independently.',
                      '`dashboard_reproduction_inputs`: byte-identical original manifest/payload for later mutable-dashboard changes.',
                      '`review_logs`: moved reviewer-process logs with SHA-preserving project links; review_log_move.json records provenance.',
                      'Strict-VT primary:5,403 distinct opportunities, including762 B06 immediate entries;27 dates have no entry.',
                      'v2 raw identities reproduce all original441 dashboard events; no threshold was retuned.']
        lines += ['', f'Code, frozen methods, persona dispositions and findings: `{OUT}`.',
                  'No API calls or original-source overwrites. Metadata is committed with root CHANGELOG and DATA_DICTIONARY.', '']
        create(directory/'DATA_DICTIONARY.md', '\n'.join(lines))
        summaries.append(inventory)
    section = f'''\n\n## {SECTION} — frozen B01–B10 on150 dates (2026-09-19)

- Authoritative namespace: `{V2}`.
- Preserved unscored preparation: `{V1}`; omitted35 existing warmup sources, corrected before outcomes.
- Fixed150 dates (original50, added66from2025+34from2026),2025-02-06–2026-08-11; zero new API calls.
- Primary gate: strictly above same-date VT from09:30 through entry, using prior minute lows and entry open only.
- Objective: +5 before−15 within60 native minute bars. Posttarget reversals irrelevant. Neither/ambiguous stay in N.
- Frozen10 families produce13 rows;7,465 raw setup records,7,313 distinct opportunities,5,403 strict-VT opportunities.
-585 comparison rows preserve3 VT scopes,3 sensitivities and5 cohorts. No IV overlay or new thresholds.
- Matched earlier-hour B01 differences are selected-path timing diagnostics, not causal signal effects.
- v1: {summaries[0]['files']} payload files / {summaries[0]['bytes']:,} bytes; v2: {summaries[1]['files']} / {summaries[1]['bytes']:,} bytes.
  Counts exclude each namespace's inventory.json/DATA_DICTIONARY.md and root registry markdown.
- Every source/output hash and schema is in namespace inventory; original dashboard inputs are archived in v2.
- All441 original dashboard identities,1,040 B06 parents/outcomes and762 strict-VT B06 entries reproduce.
  Independent native reconciliation covers all7,313 opportunities and585 summary rows;122 tests passed.
- Detailed file meanings, raw/unique denominator distinctions and exploratory limitations in namespace dictionaries;
  methods and findings at `{OUT}`.
'''
    with (ROOT/'DATA_DICTIONARY.md').open('a') as file:
        file.write(section)
    entries = []
    for inventory in summaries:
        is_final = inventory['status'] == 'authoritative'
        moved_size = sum(r['bytes'] for r in moved) if is_final else 0
        count = inventory['files']-(len(moved) if is_final else 0)
        size = inventory['bytes']-moved_size
        title = 'authoritative B01–B10 replay with complete cached warmup' if is_final else 'preserved unscored B01–B10 preparation'
        reason = ('Rerun all frozen entry recipes on the expanded150-date sample with strict causal VT eligibility.'
                  if is_final else 'Preserve the first preparation after a source inventory audit found35 missing cached warmup sessions before scoring.')
        entries.append(f'''\n\n## 2026-09-19 — create — {title}

- **date:** 2026-09-19
- **operator:** Codex / Charlie and Brent Branch B replay side conversation
- **repo_session:** delta_bomb
- **op_type:** create
- **paths_touched:** `{inventory['namespace']}/`; `{ROOT}/DATA_DICTIONARY.md`
- **size_delta_bytes:** +{size} (payload; inventory/dictionary metadata excluded; reviewer-log moves accounted separately)
- **file_count_delta:** +{count} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** 0
- **reversibility:** reversible (new derived namespace; native inputs and earlier studies unchanged)
- **dictionary_section:** {SECTION} and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** {Path(inventory['namespace']).relative_to(ROOT)}/inventory.json, input_freeze.json, event_freeze.json, analysis_freeze.json, reproduction.json{' ; adapter_freeze.json, analysis_complete.json, independent_verification.json, review_log_move.json' if is_final else ''}
- **why:** {reason}
- **verification:** {'All441 dashboard identities,1,040 B06 parents/outcomes and762 strict-VT B06 records reproduce. Every7,313 unique outcome/VT flag independently checked from native sources; all585 summary rows reconcile.122 tests passed. Methods frozen before outcomes; selected earlier-hour controls explicitly limited to timing diagnostics.' if is_final else 'No new-family outcomes scored in this namespace.7,413 raw candidate events preserved; authoritative v2 adds35 native cached warmup sessions without changing recipes or evaluation dates.'}
''')
    entries.append(f'''\n\n## 2026-09-19 — move — Charlie and Brent replay review logs into central storage

- **date:** 2026-09-19
- **operator:** Codex / Charlie and Brent Branch B replay side conversation
- **repo_session:** delta_bomb
- **op_type:** move
- **paths_touched:** `{V2}/review_logs/`; `{ROOT}/DATA_DICTIONARY.md`
- **size_delta_bytes:** +{sum(r['bytes'] for r in moved)} (central payload; same bytes removed from project-local regular files)
- **file_count_delta:** +{len(moved)} (central log payload; byte-identical project symlinks remain)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** 0
- **reversibility:** reversible
- **dictionary_section:** {SECTION} and v2 DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** {V2.relative_to(ROOT)}/review_log_move.json, inventory.json
- **why:** Keep reviewer execution logs in the central data root alongside experiment evidence.
- **verification:** Both log SHA-256 values unchanged after move; source/destination/bytes in review_log_move.json.
''')
    with (ROOT/'CHANGELOG.md').open('a') as file:
        file.write(''.join(entries))
    print(json.dumps([{k:v for k,v in s.items() if k != 'entries'} for s in summaries], indent=2))


if __name__ == '__main__':
    main()
