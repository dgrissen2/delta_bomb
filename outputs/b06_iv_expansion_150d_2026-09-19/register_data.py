"""Register a completed central dataset with measured inventory and append-only log."""
from __future__ import annotations

import json
from pathlib import Path

from collect import DATA

ROOT = Path('/Users/dgrissen/Dev/central_trade_data')
HEADING = '## B06-IV-150 — sector IV expansion to 150 above-VT dates (2026-09-19)'


def main() -> None:
    inventory = json.loads((DATA / 'inventory.json').read_text())
    feature = json.loads((DATA / 'research/feature_freeze_before_outcomes.json').read_text())
    archive = json.loads((DATA / 'archive_manifest.json').read_text())
    moved = json.loads((DATA / 'derived_storage_move.json').read_text())
    if inventory['collection_status'] != 'complete':
        raise ValueError('Cannot register unfinished collection as complete')
    dictionary = ROOT / 'DATA_DICTIONARY.md'
    changelog = ROOT / 'CHANGELOG.md'
    if HEADING in dictionary.read_text() or 'B06-IV-150' in changelog.read_text():
        raise ValueError('Already registered; add an explicit correction instead of rewriting history')
    totals = inventory['totals']
    calls = inventory['api_requests_started']
    dirs = inventory['directories']
    raw_rows = sum(dirs[n]['parquet_rows'] for n in
                   ['option_history_greeks_implied_volatility', 'option_history_greeks_first_order'])
    rows = '\n'.join(f"| `{name}` | {item['files']:,} | {item.get('parquet_rows', 0):,} | {item['bytes']:,} |"
                     for name, item in dirs.items())
    snapshot = f"""
## Completed inventory snapshot

Collection complete; 1,941 expiry pairs, no final failed pair. The original fifty
and additional 100 contain 150 unique sampled dates and 1,040 B06 parents.
Prepared coverage: {feature['successful_panels']:,} sector-days;
{feature['missing_panels']:,} missing/invalid sector-days, all reasons retained.

| Directory | Files including sidecars | Parquet rows | Bytes |
| --- | ---: | ---: | ---: |
{rows}

Total: **{totals['files']:,} files, {totals['bytes']:,} bytes**, excluding README,
data dictionary and inventory bookkeeping itself. Counts include data, logs and
provenance, with project aliases excluded. New option-history rows: {raw_rows:,}
across both endpoints; corresponding observations repeat across endpoints and
are not independent measurements.

SDK data attempts: **{calls:,}**, including {inventory['historical_errors']} logged
historical errors ({inventory['authentication_errors']} UNAUTHENTICATED).
Maximum attempts per key: {inventory['maximum_attempts_per_key']}. Final collection
recovered those failures; authentication requests themselves are not counted as
market-data calls. Read `requests.jsonl` for original attempts and `manifest.json`
for completed inputs. Previously central raw inputs referenced from other studies
are excluded from this namespace's new-file inventory.

Request reconciliation: {inventory['request_status_counts']['ok']:,} successful new
responses, {inventory['historical_errors']} logged errors, and
{calls-inventory['request_status_counts']['ok']-inventory['historical_errors']} started
attempts without a terminal log record in the interrupted run. Another
{inventory['request_status_counts'].get('reused_external',0)} exact-matching endpoint
responses were reused from existing central caches. The final input set is complete.

Final verification used the recorded numeric-container compatibility adapter at
research/validation_compatibility.json. It preserves values and tolerance; no
calculation or classification rule was changed.
"""
    for filename in ['README.md', 'DATA_DICTIONARY.md']:
        with (DATA / filename).open('a') as stream:
            stream.write(snapshot)
    with dictionary.open('a') as stream:
        stream.write(f"""

{HEADING}

- **Canonical root:** `{DATA}/`.
- **Detailed dictionary:** [{DATA}/DATA_DICTIONARY.md]({DATA}/DATA_DICTIONARY.md).
- **Source:** ThetaData Python SDK1.0.9; native one-minute SPX OHLC and sector-option
  implied-volatility/first-order endpoints, both rights, strike_range30, 09:30–14:29
  Eastern, SOFR. All raw and derived data are central; project data paths are links.
- **Scope:** original50 plus random100 additional documented above-VT-at-open dates;
  66 dates in2025 and84 in2026, 1,040 B06 parents on149 active dates. New sample is
  66 dates in2025 plus34 in2026. No replacement for unavailable IV or outcomes.
- **Capture:** 100 dated listings,1,941 successful selected expiry pairs;
  {raw_rows:,} newly stored option-history rows across two endpoints;
  {calls:,} data-request attempts including logged retries. Successful existing
  central inputs reused without refetching. Exact per-directory rows/files/bytes
  are in inventory.json. Namespace totals: **{totals['files']:,} files /
  {totals['bytes']:,} bytes**, excluding its README, dictionary and inventory.
- **SPX coverage:** 64 new raw responses,60 normalized complete; four raw responses
  fail OHLC validation. Full recorded VT-date inventory420/424complete before draw.
- **Derived:** {feature['successful_panels']} prepared sector-day panels;
  {feature['missing_panels']} missing/invalid panels across150×11.
  Event grid45,760rows; basket grid4,160rows. Four midpoint-IV measurement policies
  use constant30-calendar-DTE spotATM, log-strike variance and expiry total-variance
  interpolation; raw decimal IV becomes volatility percentage points. No time fill.
- **Policy codes:** original,midpoint,guarded_100,guarded_50. Midpoint recovery drops
  bid-IV validity only; zero dollar bids remain rejected. Guards require prior
  same-contract minute quotes, no specified one-sided collapse, and100%/50% spread
  ceilings. Full boundaries and units in the detailed dictionary.
- **Signal clock:** T−35…T−6, thirty actual samples, two fifteen-sample OLS slopes;
  acceleration=(b2−b1)/15. At least six of fixed eleven sectors must show falling
  and accelerating IV. Unknown stays separate; no altered denominator.
- **Objective:** +5SPX before−15 within60native minute bars; same-minute both is
  ambiguous; later reversal irrelevant. Separate old50,new100,full150 and year
  tables; paired date bootstrap10,000draws,seed20260919,zero-entry dates retained.
- **Known limitations:** 22new sector-days lack8–65DTE expiry brackets (20XLRE,2XLB).
  Most2025datesAugust–December,8inFebruary,noMarch–July; documented eligibility is
  not balanced full-year coverage. Transport failures are distinct from expiry
  gaps; all original errors remain audited despite successful recovery.
- **Provenance:** requests.jsonl,manifest.json,selections.json,inventory.json,
  archive_manifest.json,derived_storage_move.json and research/*.json. Frozen
  functions and all original five result rows reproduced; features frozen before
  new outcomes. Code/findings in delta_bomb/outputs/b06_iv_expansion_150d_2026-09-19/.
""")
    # The initial movement and final flat-file archival are separate operations;
    # exclude their payloads from the newly generated-data entry to avoid double counting.
    move_records = moved if isinstance(moved, list) else moved['moves']
    moved_bytes = sum(r['bytes'] for r in move_records)
    moved_files = sum(r['files'] for r in move_records)
    created_bytes = totals['bytes'] - moved_bytes - archive['bytes']
    created_files = totals['files'] - moved_files - archive['file_count']
    operations = [
        ('create', 'native minute capture and derived B06 IV expansion data',
         str(DATA) + '/', created_bytes, created_files, calls,
         'Preserve native data and unchanged four-policy evidence for the requested 50-to-150-date expansion.'),
        ('move', 'B06 minute series and sector features moved centrally',
         str(DATA / 'derived') + '/', moved_bytes, moved_files, 0,
         'Honor the user instruction to keep all study data under central_trade_data; project directory aliases preserve frozen hashes.'),
        ('move', 'B06 sampling evidence and final comparison data moved centrally',
         str(DATA / 'research') + '/', archive['bytes'], archive['file_count'], 0,
         'Store every study CSV, Parquet, JSON and log centrally with byte-preserving project links.')]
    with changelog.open('a') as stream:
        for kind, title, path, size, count, consumed, why in operations:
            stream.write(f"""

## 2026-09-19 — {kind} — {title} (B06-IV-150)

- **date:** 2026-09-19
- **operator:** Codex / B06 IV expansion side conversation
- **repo_session:** delta_bomb
- **op_type:** {kind}
- **paths_touched:** `{path}`; `/Users/dgrissen/Dev/central_trade_data/DATA_DICTIONARY.md`
- **size_delta_bytes:** +{size} (data/log/provenance scope; dictionary and README bytes excluded)
- **file_count_delta:** +{count}
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** {consumed} (data attempts, including errors/retries; auth handshakes excluded)
- **reversibility:** reversible (immutable native inputs preserved; moves retain byte-identical project links)
- **dictionary_section:** §B06-IV-150 and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** thetadata/b06_iv_expansion_150d_2026-09-19-v1/manifest.json, selections.json, sampling_freeze.json, protocol_freeze.json, derived_storage_move.json, archive_manifest.json, inventory.json, research/verification.json
- **why:** {why}
- **reconciliation:** The three entries jointly add {totals['files']} files and {totals['bytes']} bytes to this namespace; moved payloads are subtracted from the create entry. No original fifty-day raw cache was overwritten. All1,941 selected expiry pairs completed;22new sector-days remain missing for the fixed expiry-bracket rule. Historical authentication errors remain in requests.jsonl. See inventory.json for exact counts and scope.
""")
    print(json.dumps({'dictionary_reconciled': True, 'root': str(DATA),
                      'data_files': totals['files'], 'data_bytes': totals['bytes'],
                      'journal_entries': len(operations)}))


if __name__ == '__main__':
    main()
