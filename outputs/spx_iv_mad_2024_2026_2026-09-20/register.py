"""Register the isolated SPX native and derived dataset after verification."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import spx_mad as p


def main() -> None:
    manifest = json.loads((p.DATA / 'manifest.json').read_text())
    assert manifest['status'] == 'complete' and not manifest['unresolved_requests']
    paths = sorted(path for path in p.DATA.rglob('*') if path.is_file()
                   and path.name not in ['inventory.json', 'DATA_DICTIONARY.md'])
    if any(path.suffix == '.tmp' for path in paths):
        raise ValueError('Incomplete data writes remain')
    entries = [{'path': str(path), 'bytes': path.stat().st_size, 'sha256': p.digest(path)}
               for path in paths]
    size = sum(row['bytes'] for row in entries)
    counts = {}
    for method in ['option_list_contracts', *p.legacy.METHODS]:
        metadata = [json.loads(path.read_text()) for path in (p.DATA / method).glob('*.json')]
        counts[method] = {'responses': len(metadata), 'rows': sum(row['rows'] for row in metadata)}
    exact = p.DATA / 'calibration_exact' / 'SPXW'
    schema = pd.read_parquet(exact / 'scored_windows.parquet').dtypes.astype(str).to_dict()
    summary = manifest['summary']
    section = 'SPX-IV-MAD-2024-2026 — index IV acceleration history (2026-09-20)'
    body = f'''## {section}

Namespace: `{p.DATA}`. Project producer/report: `{p.OUT}`.
Underlying **SPX**, option root **SPXW** (PM-settled index options only).
681 target sessions January 2, 2024–September 18, 2026; 60 strictly prior warmup
sessions October 5–December 29, 2023; 741 calendar dates total. All regimes.
Native 09:30–14:29 ET; derived early-close cutoff 12:59. Thirty-minute endpoints
begin 09:59. No claims about uncollected later-session hours or future 2026 dates.

Native ThetaData SDK IV and matching first-order histories, one-minute interval,
both rights, strike_range=30, SOFR/latest/default model. Listed expiries bracket
30 calendar DTE within 8–65 DTE; exact 30 DTE uses one expiry. Same frozen ATM spot-strike
interpolation, call/put variance average and quote guards as the sector baseline.
Strict exact→strict±2min neighbor→guarded original-minute recovery, 100% spread
ceiling for fallback. Positive dollar bid/ask required; no zero-bid substitution.
Sources stay inside actual window/hour; unique actual timestamps. Actual-time
OLS fifteen-minute halves; acceleration=(b2−b1)/15.

Sixty strictly prior sessions per endpoint-hour, both signs, equal total date
weights; exact lower weighted median and MAD. Scale=1.4826×MAD; minimum 10
contributing dates and scale>1e−12. Signed score=−a/scale; absolute=abs(a)/scale;
downward-only requires actual falling IV and negative acceleration. Unknowns
retain expected slots and reasons. No thresholds or B0x outcomes fitted.

**Coverage:** {summary['target_scored']:,}/{summary['target_windows']:,} target windows
scored; {summary['baseline_blocks']:,} daily/hourly baseline rows;
baseline statuses `{json.dumps(summary['baseline_status'])}`.
Target dates missing selected expiry brackets: {len(manifest['missing_target_dates'])}.
Raw response counts/rows: `{json.dumps(counts, sort_keys=True)}`.

**Files:** native endpoint Parquet plus request metadata; immutable requests.jsonl;
dated listed expirations and selected brackets; day input manifests; per-date
native-derived IV sources, source choices/support and acceleration windows;
all_windows/daily_coverage; calibration_exact/SPXW/block_baselines.parquet and
scored_windows.parquet; CSV baselines/coverage/half-year bins; independent
verification, boundary probes, protocol and input/output hashes. Project links
reference central outputs without duplicating market data.

Score schema: `{json.dumps(schema, sort_keys=True)}`.

**Verification:** 13 boundary tests, inherited quote-guard checks, all
baseline medians/MADs independently checked using rational-CDF inequalities;
all prior-date/count ledgers and scores checked; independent OLS and causal prefix
replay, including 2023/2024 boundaries. Frozen sector scientific code unchanged.

One recorded endpoint alignment exception: June 9, 2026 has 79,200 native IV rows
versus 36,000 native Greek rows, with every Greek key present in IV. A separate
paired IV view keeps every Greek key and unchanged IV values; original native
responses remain immutable. The additive protocol freeze, receipt and independent
verification record the 43,200 IV-only rows excluded, with no Greek inference,
quote-guard change or extra request. All 271 windows on that date are available.

**Calls:** {manifest['sdk_attempts']} explicit SDK data attempts,
{manifest['sdk_successes']} successful responses,{manifest['sdk_errors']} error
attempts, 0 unresolved. Authentication excluded. Existing exact parameter-matched
caches are reused by SHA-256. Four SDK/two calculation workers, 12,000-attempt cap,
two normal attempts plus one exclusive cooled INTERNAL-only third; gateway
outages pause requests. Zero ORATS/other paid-provider calls.

**Payload:** {len(entries):,} files, {size:,} bytes, excluding this namespace's
inventory/dictionary and root registry markdown. Per-file hashes in inventory.json.
Operation is reversible additive backfill; no prior source or sector data changed.
'''
    dictionary = p.DATA / 'DATA_DICTIONARY.md'
    if dictionary.exists() and dictionary.read_text() != body:
        raise ValueError('Existing SPX dictionary differs')
    dictionary.write_text(body)
    p.write_json(p.DATA / 'inventory.json', {
        'files': len(entries), 'bytes': size, 'entries': entries,
        'excluded': ['inventory.json', 'DATA_DICTIONARY.md', 'root registry markdown'],
        'native_response_counts': counts, 'operation': 'backfill',
        'manifest_sha256': p.digest(p.DATA / 'manifest.json'),
        'registry_producer_sha256': p.digest(Path(__file__))})
    entry = f'''\n\n## 2026-09-20 — backfill — SPX IV acceleration MAD history from 2024

- **date:** 2026-09-20
- **operator:** Codex / delta_bomb SPX MAD continuation
- **repo_session:** delta_bomb
- **op_type:** backfill
- **paths_touched:** `{p.DATA}/`; `/Users/dgrissen/Dev/central_trade_data/DATA_DICTIONARY.md`
- **size_delta_bytes:** +{size} (payload excluding namespace inventory/dictionary and root registry markdown)
- **file_count_delta:** +{len(entries)} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** {manifest['sdk_attempts']} (explicit data attempts including retries; authentication excluded)
- **reversibility:** reversible (new namespace; prior data unchanged)
- **dictionary_section:** {section}
- **dictionary_reconciled:** true
- **manifests_updated:** protocol_freeze.json, boundary_probe.json, first_target_check.json, endpoint_pairing_freeze/receipt/verification.json, gap_diagnostics.json, selections.json, SPXW_collection.json, request ledger and endpoint metadata, per-date derived metadata, calibration_exact/SPXW summary/verification_final, manifest.json, inventory.json
- **why:** User requested the same IV-acceleration MAD calculation on SPX itself from 2024 onward; SPXW native PM-settled contracts isolate one settlement convention.
- **coverage:** 741 dates including 60 warmup; 681 target dates; {summary['baseline_blocks']} baselines;{summary['target_scored']}/{summary['target_windows']} scored windows; baseline statuses {json.dumps(summary['baseline_status'])}.
- **verification:** 13 boundary tests, frozen quote guards, exact independent rational-CDF median/MAD checks, every historical date/count ledger and score, independent OLS and prefix-causality checks; one documented lossless endpoint-pairing repair. No new threshold or B0x backtest.
- **reconciliation:** {manifest['sdk_successes']} successful native responses; {manifest['sdk_errors']} error attempts; 0 unresolved. Bytes and hashes reconcile with inventory; old sector data remains unchanged.
'''
    for name, addition in [('CHANGELOG.md', entry), ('DATA_DICTIONARY.md', '\n\n' + body)]:
        root = p.DATA.parents[1] / name
        existing = root.read_text()
        marker = addition.strip().splitlines()[0]
        if marker in existing:
            if addition not in existing:
                raise ValueError(f'Registry entry differs: {root}')
        else:
            with root.open('a') as stream:
                stream.write(addition)
        (p.OUT / f'REGISTRY_{name}').write_text(addition)
    (p.OUT / 'DATA_REGISTRY_ENTRY.md').write_text(entry)
    print(json.dumps({'files': len(entries), 'bytes': size, 'sdk_attempts': manifest['sdk_attempts']}))


if __name__ == '__main__':
    main()
