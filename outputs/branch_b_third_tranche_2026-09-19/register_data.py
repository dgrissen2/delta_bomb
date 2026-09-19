"""Journal the immutable third-tranche dataset and exact file/schema inventory."""
from __future__ import annotations

import json

import pandas as pd
import pyarrow.parquet as pq

from pipeline import DATA, OUT, digest, write_json

ROOT = DATA.parent.parent
SECTION = 'BRANCH-B-THIRD-TRANCHE'


def main() -> None:
    if (DATA/'inventory.json').exists() or SECTION in (ROOT/'DATA_DICTIONARY.md').read_text():
        raise FileExistsError('Third tranche already registered')
    records = []
    for path in sorted(DATA.rglob('*')):
        if not path.is_file():
            continue
        item = {'path': str(path.relative_to(DATA)), 'bytes': path.stat().st_size, 'sha256': digest(path)}
        if path.suffix == '.csv':
            frame = pd.read_csv(path)
            item.update(rows=len(frame), columns=list(frame.columns),
                        dtypes={c: str(t) for c, t in frame.dtypes.items()})
        elif path.suffix == '.parquet':
            parquet = pq.ParquetFile(path)
            item.update(rows=parquet.metadata.num_rows, schema=str(parquet.schema_arrow))
        records.append(item)
    requests = [json.loads(line) for line in (DATA/'requests.jsonl').read_text().splitlines()]
    calls = sum(r['status'] == 'started' for r in requests)
    reused = sum(r['status'] == 'reused_external' for r in requests)
    verification = json.loads((DATA/'independent_verification.json').read_text())
    inventory = {'namespace': str(DATA), 'status': 'complete', 'files': len(records),
                 'bytes': sum(r['bytes'] for r in records),
                 'scope': 'Namespace payload, excluding inventory.json and DATA_DICTIONARY.md',
                 'api_calls': {'thetadata': calls, 'orats': 0},
                 'exact_external_raw_responses_reused': reused,
                 'verification': verification,
                 'source_code_hashes': {str(p): digest(p) for p in sorted(OUT.glob('*.py'))},
                 'entries': records}
    write_json(DATA/'inventory.json', inventory)
    dictionary = f'''# B01–B10 third tranche: all remaining verifiable dates

Namespace: `{DATA}`.

Audited429 completed NYSE dates,2025-01-01–2026-09-18.249 qualify:
original50 + second100 + third89 + development10. Third tranche is88 dates
from2025 and one from2026;85 recovered from older publication metadata and4
previously eligible undrawn dates. Research cumulative total excludes development
and contains239 dates. The249-date aggregate is explicitly descriptive.

The earlier date audit's `Date`-only metadata parser excluded usable `Published`
notes. New logic requires all publication labels on the same session date and
strictly before09:30, an explicit Eastern heading, valid DST labels and matching
SPX VT. Use the latest label when preopen timestamps differ; retain discrepancies.
No use of scraped-at, future note, inferred VT, after-open label or favorable choice
between conflicting values. Prior studies remain unchanged and their counts reproduce.

**Objective:** native entry open to +5 before−15 within60 bars, including entry bar.
Same-minute first double-touch is ambiguous; neither/ambiguous remain in N. Later
reversal irrelevant. Prices in SPX points; minute clocks are integer ET minutes
since midnight. Percent fields are0–100; differences are percentage points.

**Primary VT gate:** all prior minute lows from09:30 and entry open strictly above
same-date VT. Never uses entry-minute future low or future session status. Other
gates are labeled diagnostics. Full390-minute valid sessions required; partial
warmup contributes only complete5m bins and no inferred observations.

**Dataset:**12,534 raw setup events,12,284 distinct variant/date/entry-minute
opportunities;9,320 strict-VT opportunities,3,554 in tranche3. All7,465 earlier
raw identities and7,313 distinct opportunities reproduce. Ten development days
separately reproduce441 original dashboard identities. All1,053 summary rows and
every native outcome/VT flag independently checked;24 targeted tests pass.

**Files:**{inventory['files']} payload files,{inventory['bytes']:,} bytes. This
dictionary and inventory.json excluded. Every file hash and CSV/Parquet schema
is in inventory.json. Root CHANGELOG/DATA_DICTIONARY are registry metadata.

| File | Rows | Bytes |
| --- | --- | --- |
'''
    dictionary += '\n'.join(f'| {r["path"]} | {r.get("rows", "—")} | {r["bytes"]:,} |' for r in records)
    dictionary += f'''

## File meanings

- population_before_coverage/population: every429 calendar date, VT/source/evidence,
  native completeness, exclusion reasons, old/recovered publication status and cohort.
- selected_days: all249 qualifying dates, frozen before outcomes; cohort labels
  original_50/additional_100/third_tranche/development_10. No new random draw.
- provenance_before_coverage/vt_note_provenance: every saved note's extracts, hash,
  old and new time status, VT table cells, timestamp discrepancies and price attempts.
- coverage_plan/complete and requests.jsonl: essential missing native SPX coverage,
  request/error/reuse audit; one new SDK index-history request for2026-09-17 and one
  existing2025-04-07 raw response reused then rejected for four bad OHLC observations.
- index_history_ohlc: immutable SDK raw response and request metadata. spx_normalized:
  timezone-aware native390-minute2026-09-17 RTH data. That date opens below VT.
- history_ledger:999 sources,999 five-minute-history inclusions and990 complete RSI
  sessions. Feature parquets contain249 evaluated dates with inherited warmup.
- *_freeze: protocol, input, method and event hashes recorded before new outcomes.
- events_before_outcomes/setup_ledger: raw recipe emissions and original episodes.
- event_outcomes/distinct_event_outcomes: scored raw versus unique opportunity ledgers.
- comparison:3 VT gates ×3 sensitivities ×9 cohort groups ×13 variants =1,053 rows.
  Primary all-entry rows use strict VT. first_per_day and spaced60 are sensitivities.
  Date-bootstrap10,000 draws,seed20260919,zero-event dates included. Single-date
  third_2026 intervals are not meaningful population uncertainty estimates.
- daily_counts/context_diagnostics: zero-inclusive date counts and frozen diagnostic
  bins/hour. Original150-date cut points reused; no cutoff search.
- paired_setup_comparison: matched parent/delayed setups and missed parent targets;
  setup-unit counts can exceed distinct entry-minute counts.
- third_admission_comparison: all13 rows on85 recovered versus4 legacy-eligible new dates.
- third_month_counts: exact new-date calendar mix. warmup_gap_events:empty after audit.
- existing_iv_coverage_diagnostic: unchanged earlier IV coverage data only; no new IV
  features/filters attached to this price-only replay.
- independent_verification/development_reproduction: native-event, cohort, summary
  and original-development-identity checks.

Earlier-hour B01 differences are selected-path timing diagnostics, not causal signal
uplift. They condition an earlier control on later setup formation. Rates remain
exploratory and cannot establish option profitability. No new2026-generalization
claim is supported by the single third-tranche2026 date.

Remaining unknowns/exclusions are visible, including missing2026-09-18 VT/prices,
conflicting levels, late/missing note evidence, bad OHLC and three2025 early closes.
Publication labels cannot establish contemporaneous local capture or absent revisions.

Code, methods and all13-row findings: `{OUT}`.
'''
    with (DATA/'DATA_DICTIONARY.md').open('x') as file:
        file.write(dictionary)
    root_section = f'''\n\n## {SECTION} — exhaustive verifiable B01–B10 extension (2026-09-19)

Namespace: `{DATA}`.

429 completed2025–2026 sessions audited through2026-09-18;249 qualify. Original50,
second100,third89 (88from2025/1from2026),development10 separately labeled.239 research
dates exclude development.85 previously excluded dates recovered by handling saved
Published metadata and conservatively checking all explicit preopen time labels;
4 previously eligible undrawn dates complete tranche3. Source labels still do not
prove absence of historical revisions. Earlier date-universe completeness claims
were conditional on the overly restrictive old parser; old numeric rows reproduce.

Frozen13 price-only rows, +5 before−15 in60m, strict above-VT through entry.12,534 raw
setups,12,284 unique opportunities,9,320 strict-VT opportunities,3,554 in tranche3.
1,053 comparison rows, all native scores/gates independently verified;351 prior
summary rows and441 development identities reproduce.24 targeted tests pass.
No IV overlay, cutoff tuning or causal interpretation of earlier-hour controls.

{inventory['files']} payload files / {inventory['bytes']:,} bytes, excluding namespace
inventory/dictionary and root registry metadata. One new ThetaData SDK1m SPX request;
zero options/ORATS calls. Existing raw/source caches preserved. Exact schemas/hashes
and all exclusions in namespace dictionary/inventory. Full findings: `{OUT}/FINDINGS.md`.
'''
    with (ROOT/'DATA_DICTIONARY.md').open('a') as file:
        file.write(root_section)
    journal = f'''\n\n## 2026-09-19 — create — exhaustive Branch B third tranche with publication-format recovery

- **date:** 2026-09-19
- **operator:** Codex / Branch B third-tranche side conversation
- **repo_session:** delta_bomb
- **op_type:** create
- **paths_touched:** `{DATA}/`; `{ROOT}/DATA_DICTIONARY.md`; `{ROOT}/CHANGELOG.md`
- **size_delta_bytes:** +{inventory['bytes']} (namespace payload; inventory/dictionary and root registry metadata excluded)
- **file_count_delta:** +{inventory['files']} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** {calls} (one successful new index_history_ohlc request, native1m; authentication excluded)
- **reversibility:** reversible (new immutable namespace; no previous raw cache, date study or dashboard overwritten)
- **dictionary_section:** {SECTION} and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** {DATA.relative_to(ROOT)}/inventory.json, protocol_freeze.json, coverage_plan.json, coverage_complete.json, input_freeze.json, analysis_freeze.json, event_freeze.json, analysis_complete.json, independent_verification.json, development_reproduction.json
- **why:** User requested every qualifying2025–2026 date and an unchanged third-tranche B01–B10 replay.
- **coverage_correction:** Old Date-only/exact-time parser missed Published-format notes.85 above-VT dates recovered using matching same-date VT and latest explicit preopen label, plus4 eligible undrawn dates. Preserve time discrepancies and prior acceptance status; no future/late/conflicting note admitted. Prior results remain immutable and reproduce. Old eligible-universe completeness claims were conditional on the restrictive parser.
- **reconciliation:**429 calendar sessions audited;249 eligible =50+100+89+10development. Primary pooled239 excludes development.12,284 unique outcomes/VT gates independently checked;1,053 table rows reconcile;351 prior summaries and441 development identities match. Third-tranche B06 is281/540(52.0%); former high-percentage candidates weaken. One missing-native2026-09-17 fetch opens below VT and is excluded. Reused2025-04-07 raw response retains four invalid OHLC bars and remains rejected;2026-09-18 VT/prices unavailable.24 tests and Ruff pass.
'''
    with (ROOT/'CHANGELOG.md').open('a') as file:
        file.write(journal)
    print(json.dumps({k: v for k, v in inventory.items() if k not in ['entries', 'source_code_hashes', 'verification']}, indent=2))


if __name__ == '__main__':
    main()
