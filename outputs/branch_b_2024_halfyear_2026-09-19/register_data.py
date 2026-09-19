"""Register the immutable 2024 extension, its coverage exceptions and exact schemas."""
from __future__ import annotations

from collections import Counter
import json

import pandas as pd
import pyarrow.parquet as pq

from pipeline import DATA, OUT, digest, write_json

ROOT = DATA.parent.parent
SECTION = 'BRANCH-B-2024-HALFYEAR'


def main() -> None:
    if (DATA/'inventory.json').exists() or SECTION in (ROOT/'DATA_DICTIONARY.md').read_text():
        raise FileExistsError('Dataset already registered')
    verification = json.loads((DATA/'independent_verification.json').read_text())
    assert verification['prior_identities_exact']
    assert verification['prior_summary_rows_changed'] == 0
    assert (OUT/'FINDINGS.md').exists()
    records = []
    for path in sorted(DATA.rglob('*')):
        if not path.is_file():
            continue
        record = {'path': str(path.relative_to(DATA)), 'bytes': path.stat().st_size,
                  'sha256': digest(path)}
        if path.suffix == '.parquet':
            file = pq.ParquetFile(path)
            record.update(rows=file.metadata.num_rows, schema=str(file.schema_arrow))
        elif path.suffix == '.csv':
            frame = pd.read_csv(path)
            record.update(rows=len(frame), columns=list(frame.columns),
                          dtypes={c: str(t) for c, t in frame.dtypes.items()})
        records.append(record)
    requests = Counter(json.loads(line)['status'] for line in (DATA/'requests.jsonl').read_text().splitlines())
    inventory = {'namespace': str(DATA), 'status': 'complete_with_documented_source_exclusions',
                 'files': len(records), 'bytes': sum(r['bytes'] for r in records),
                 'scope': 'Namespace payload excluding inventory.json and DATA_DICTIONARY.md',
                 'api_calls': {'thetadata': requests['started'], 'orats': 0},
                 'provider_responses_ok': requests['ok'],
                 'normalization_rejections': {'2024-05-30': '77 invalid OHLC observations'},
                 'verification': verification,
                 'source_code_hashes': {str(p): digest(p) for p in sorted(OUT.glob('*.py'))},
                 'findings_sha256': digest(OUT/'FINDINGS.md'), 'entries': records}
    write_json(DATA/'inventory.json', inventory)
    periods = pd.read_csv(DATA/'halfyear_population.csv')
    dictionary = f'''# Branch B 2024 extension and half-year results

Namespace: `{DATA}`.
Code and extensive findings: `{OUT}`.

All 681 completed NYSE sessions from January 2, 2024 through September 18, 2026
audited, including 252 in 2024. There are 421 verifiable qualifying dates: 172
newly evaluated 2024 dates plus 249 prior dates. All primary half-years and pooled
research exclude the original ten development dates, leaving 411. Existing
50/100/89 research cohorts and all earlier data remain immutable.

| Period | Research dates | Zero-event dates | Development excluded |
| --- | --- | --- | --- |
'''
    dictionary += '\n'.join(f'| {r.half_year} | {r.research_dates} | {r.zero_event_research_dates} | '
                            f'{r.development_dates_excluded} |' for r in periods.itertuples())
    dictionary += f'''

Primary gate requires all prior RTH minute lows and entry open strictly above
same-date VT. Prior touches/breaches block later entries. Future lows and full-day
status never approve entry. Same-date positive VT requires matching saved preopen
note labels under the third-tranche parser; conflicting/late/missing/prior-evening
evidence remains excluded. Complete valid 390-minute native sessions required;
early closes remain excluded. Publication labels are not proof of absent revisions.

Score: +5 points before −15 within 60 native minute bars from entry open. A first
double-touch bar is ambiguous. Neither/ambiguous remain in N; later giveback is
irrelevant. Opportunity unit is unique variant/date/entry-minute. Raw overlapping
setup records are retained separately. Thirteen frozen rows; B03 includes thrust.
No new IV features, option requests or thresholds. One-minute clocks are integer
ET minutes since midnight; OHLC/VT/ATR use SPX points; percentages use 0–100;
percentage differences use percentage points. Raw SDK timestamps are preserved,
normalized new SPX timestamps are timezone-aware America/New_York.

34 SDK index_history_ohlc requests succeeded; 33 normalized to native complete
sessions. May 30, 2024 raw had 77 invalid OHLC bars and was rejected; its old
313-minute source remains incomplete/below VT. It contributes only existing
complete 5m warmup bins under inherited conventions. No fabricated/repaired bars.
2024 November 29 remains missing native prices and is an excluded early close.
33 history dates added and one source replaced by a new complete file (December
30, 2024); old file preserved. 1,032 history sources, 1,024 complete minute-RSI
sessions. New coverage adds no qualifying evaluation dates beyond the initial 172.

{verification['raw_setup_rows']:,} raw setup rows;
{verification['native_opportunities_checked']:,} distinct opportunities;
{verification['strict_distinct_opportunities']:,} strict-VT opportunities including
development. All native scores/gates independently verified; all
{verification['summary_rows_reconciled']:,} summary rows reconciled. All 12,534
prior identities and {verification['prior_summary_rows_compared']} earlier summary
rows reproduce exactly; 441 development identities also match. 34 targeted tests
plus four subtests; Ruff passes. Six period groups partition research dates exactly.

## Files and schemas

Exact file hashes, Parquet schemas and CSV column types are in inventory.json.
{inventory['files']} payload files / {inventory['bytes']:,} bytes, excluding this
dictionary and inventory.json. Root registry Markdown is outside this scope.

- population_before_coverage/population: all 681 calendar sessions, native sources,
  VT evidence, completeness, eligibility, cohort and explicit exclusion reasons.
- selected_days: 421 qualifying dates; new_2024/original_50/additional_100/
  third_tranche/development_10. Primary period membership excludes development.
- provenance_before_coverage/vt_note_provenance: saved note paths, hashes, VT
  extracts, publication timestamps, discrepancies and native price attempts.
- coverage_plan/complete, requests.jsonl, index_history_ohlc, spx_normalized:
  planned dates, all requests, exact raw responses/metadata, normalized native bars
  and explicit normalization rejection. No provider failure or pending queue.
- history_changes/history_ledger: source additions/replacement and per-date 5m/
  RSI warmup inclusion. Previous partial sources are preserved, not overwritten.
- five_features/minute_features: causal indicators for evaluated dates using
  available chronological history; exact eight frozen recipe modules unchanged.
- *_freeze: protocol, source, analysis and event hashes frozen before outcomes.
- events_before_outcomes/setup_ledger: raw entry emissions and parent episodes.
- event_outcomes/distinct_event_outcomes: scored setup versus unique opportunity
  records. Entry open, known_min, outcome, first_touch_min and strict VT flags.
- comparison: 3 VT gates × 3 sensitivities × 15 cohorts × 13 variants = 1,755 rows.
  Primary gate always_above; entry_above/opening_only diagnostic only. Sensitivities
  all/first_per_day/spaced60. Target/adverse/neither/ambiguous counts sum to N.
- halfyear_results: 78 strict all-entry rows; halfyear_population: calendar,
  research/development/zero-event counts. Halfyear_b06_context: median known-at-
  entry 5m ATR and +5/ATR, descriptive only, no fitted target or cutoff.
- daily_counts: zero-inclusive daily counts for cohort/date bootstrap. 10,000
  draws, seed 20260919; date_ci fields are individual-rate percentile intervals.
- context_diagnostics/warmup_gap_events: frozen earlier diagnostic cuts and gaps.
- paired_setup_comparison: parent/retest and price/RSI setup-unit comparisons;
  setup counts may exceed distinct minute-entry counts.
- existing_iv_coverage_diagnostic: unchanged earlier IV coverage audit only;
  no IV filter or feature applied to the new price-only replay.
- prior_event_comparison/prior_summary_changes: exact prior reproduction;
  latter is an empty, header-only changes ledger.
- independent_verification/development_reproduction: all native gate/score,
  period, aggregate and earlier-identity checks.

Earlier-hour B01 matched-control differences condition earlier entries on later
trigger formation; they are selected-path timing diagnostics, never causal uplift.
2026 H2 is partial and has only 18 non-development qualifying dates. Rules overlap,
entries cluster, and prior research selection limits inference. Best pooled rate
is thrust 61/92 (66.3%), followed by sparse retest 38/61 (62.3%) whose 2024 record
is weak. Immediate opening-range 153/260 (58.8%) and thrust/staircase 184/317
(58.0%) beat all-entry B06 in each half but are close to first-per-day B06 (57.9%).
No claim of a validated edge or realized option profitability.
'''
    with (DATA/'DATA_DICTIONARY.md').open('x') as file:
        file.write(dictionary)
    root_section = f'''\n\n## {SECTION} — full 2024 calendar added, six half-years (2026-09-19)

Namespace: `{DATA}`. Findings/code: `{OUT}`.

681 completed NYSE sessions audited through September 18, 2026; 421 verifiable
qualifying dates, including 172 new 2024 dates. Primary research excludes ten
development dates, leaving 411: half-year counts 87/85/62/92/67/18. Every primary
entry requires SPX to remain strictly above same-date VT from open through entry;
no future/full-day gate. Same frozen 13 price-only recipes and +5-before−15-in-60m
score. No posttarget giveback penalty, IV overlay or threshold optimization.

34 ThetaData Python SDK native SPX 1m requests, 34 successful responses, 33 complete
normalized sessions; May 30, 2024 raw rejected for 77 invalid OHLC bars, old partial
source preserved. Missing/conflicting VT notes and early closes explicitly excluded.
33 history dates added, one source replaced without overwriting old data. All 12,534
earlier signals and {verification['prior_summary_rows_compared']} prior summary rows
reproduce. {verification['native_opportunities_checked']:,} distinct opportunities
independently checked; 1,755 table rows reconcile; 34 tests plus four subtests pass.

Thrust 61/92 (66.3%), opening-range immediate 153/260 (58.8%), thrust plus staircase
184/317 (58.0%) exceed all-entry B06 in each half; small samples and first-per-day
B06 at 57.9% qualify that comparison. B10 retest weakens on 2024. Full outcome
counts, date intervals, sensitivity rows and every exclusion are documented.

{inventory['files']} payload files / {inventory['bytes']:,} bytes, excluding namespace
inventory/dictionary and root registry metadata. Zero options/ORATS calls. Exact
schemas/hashes in namespace inventory.json. Earlier data and dashboard untouched.
'''
    with (ROOT/'DATA_DICTIONARY.md').open('a') as file:
        file.write(root_section)
    journal = f'''\n\n## 2026-09-19 — create — Branch B 2024 extension and six-half-year comparison

- **date:** 2026-09-19
- **operator:** Codex / Branch B 2024 side conversation
- **repo_session:** delta_bomb
- **op_type:** create
- **paths_touched:** `{DATA}/`; `{ROOT}/DATA_DICTIONARY.md`; `{ROOT}/CHANGELOG.md`
- **size_delta_bytes:** +{inventory['bytes']} (namespace payload; inventory/dictionary and root registry metadata excluded)
- **file_count_delta:** +{inventory['files']} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** {requests['started']} (native index_history_ohlc, 1 minute; authentication excluded)
- **reversibility:** reversible (new namespace; prior native/derived data and dashboard preserved)
- **dictionary_section:** {SECTION} and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** {DATA.relative_to(ROOT)}/inventory.json, protocol_freeze.json, coverage_plan.json, coverage_complete.json, history_changes.json, input_freeze.json, analysis_freeze.json, event_freeze.json, analysis_complete.json, prior_event_comparison.json, independent_verification.json, development_reproduction.json
- **why:** User requested all qualifying 2024 dates added to the existing study and results by half-year, strictly above VT only.
- **coverage:** 681 dates audited, 421 qualify, 411 research dates excluding ten development dates. 172 new 2024 dates (87 H1 /85 H2). 34 native requests succeeded; 33 normalized complete, May 30 rejected for 77 invalid OHLC bars. Existing partial remains excluded. No artificial fills or favorable VT conflict resolution. Prior-evening/missing/late notes and early closes remain excluded under frozen policy.
- **verification:** {verification['native_opportunities_checked']:,} distinct native scores and VT gates independently checked; 1,755 aggregate rows reconcile; 12,534 prior identities and {verification['prior_summary_rows_compared']} earlier rows unchanged; 441 development identities preserved. 34 tests plus four subtests and Ruff pass. 33 history dates added, one incomplete source superseded read-only by new complete December 30 file.
- **findings:** Thrust 66.3% on 92 entries; opening-range immediate 58.8% on 260; thrust/staircase 58.0% on 317; plain B06 52.1% on 2,382. Those three candidates exceed all-entry B06 in each half, but first-per-day B06 reaches 57.9% and small-sample uncertainty is material. B10 retest does not repeat its recent strength in 2024. Fixed +5 target is larger relative to early-2024 ATR; many nonwins are timeouts. No IV, posttarget penalty, causal-uplift or realized-profitability claim.
'''
    with (ROOT/'CHANGELOG.md').open('a') as file:
        file.write(journal)
    print(json.dumps({k: inventory[k] for k in ['namespace', 'files', 'bytes', 'api_calls']}, indent=2))


if __name__ == '__main__':
    main()
