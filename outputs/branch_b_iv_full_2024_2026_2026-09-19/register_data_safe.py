"""Register the completed namespace with a durable roll-forward transaction.

The original audited writer is preserved; this metadata-only replacement writes
its inventory completion sentinel last and supports interrupted-registration resume.
"""
from __future__ import annotations

from collections import Counter
import json

import pandas as pd
import pyarrow.parquet as pq

from inputs import DATA, OUT, PRICE, ROOT, SCORE, digest
from registry_transaction import commit_files, resume

CENTRAL = ROOT.parent
SECTION = 'BRANCH-B-IV-FULL-2024-2026'


def main() -> None:
    plan_path = DATA/"registration_transaction.json"
    if plan_path.exists() and not (DATA/"inventory.json").exists():
        resume(plan_path)
        return
    if (DATA/'inventory.json').exists() or SECTION in (CENTRAL/'DATA_DICTIONARY.md').read_text():
        raise FileExistsError('Research namespace already registered')
    verification = json.loads((DATA/'independent_verification.json').read_text())
    analysis = json.loads((DATA/'analysis_complete.json').read_text())
    review = json.loads((DATA/'review_status.json').read_text())
    if review['status'] not in ['PASS','CONDITIONAL PASS']:
        raise ValueError('Completed independent review required')
    records = []
    for path in sorted(DATA.rglob('*')):
        if not path.is_file():
            continue
        if path.name.endswith(('.index','.lock','.tmp')):
            raise ValueError(f'Unfinished temporary artifact: {path}')
        row = dict(path=str(path.relative_to(DATA)),bytes=path.stat().st_size,sha256=digest(path))
        if path.suffix == '.parquet':
            parquet = pq.ParquetFile(path)
            row.update(rows=parquet.metadata.num_rows,schema=str(parquet.schema_arrow))
        elif path.suffix == '.csv':
            frame = pd.read_csv(path)
            row.update(rows=len(frame),columns=list(frame.columns))
        records.append(row)
    requests = [json.loads(line) for line in (DATA/'requests.jsonl').read_text().splitlines()]
    counts = Counter(r['status'] for r in requests)
    weights = json.loads((DATA/'weights/manifest.json').read_text())['receipts']
    calls = dict(thetadata=counts['started'],orats=0,public_issuer=sum(not r['reused'] for r in weights))
    inventory = dict(namespace=str(DATA),status='complete',files=len(records),
        bytes=sum(r['bytes'] for r in records),api_calls=calls,request_status_counts=dict(counts),
        scope='Payload excludes inventory.json, registration_transaction.json, namespace DATA_DICTIONARY.md and root registry Markdown',
        code_hashes={str(p):digest(p) for p in sorted(OUT.glob('*.py'))},
        findings_sha256=digest(OUT/'FINDINGS.md'),entries=records)
    text = f'''# Full 2024–2026 prior-rule IV comparison

Namespace: `{DATA}`. Code and findings: `{OUT}`.
Frozen price population: `{PRICE}`. Frozen +5/−10 outcomes: `{SCORE}`.

411 research dates, ten separate development dates, thirteen unchanged entry families.
Strict VT gate uses every earlier native RTH low and entry open; no future day-low gate.
Target +5 before −10 in sixty native minutes; same-minute double touch ambiguous;
neither and ambiguous remain in N. Later givebacks do not change a target-first result.

Eleven sector ETFs; native ThetaData Python SDK one-minute IV and first-order Greeks;
SOFR/default provider dividend model; both rights; strike_range30;09:30–14:29ET.
Dated nearest expiry bracket around30 calendar DTE within8–65, never extrapolated.
ATM-spot and ±25delta wings use the original variance/total-variance interpolation.
Rates are IV percentage points/minute; acceleration is points/minute². Window at
entryT is T−35…T−6. Unknowns retain the fixed eleven-sector denominator.

Prior rules: falling, acceleration, surface-shape directions/phases, quote-resolved
signs, four original quote policies, same-sector positive price/negative IV pairing,
prior-session IVV sector weighting, comparable-price matching and recruitment context.
Balanced nearby recovery and other price families are labeled transfers. No MAD
history or magnitude cutoff test in this run. Sparse-surface coordinates are not a
full continuous surface, term-structure or individual-constituent test.

Primary score table has {analysis['table_rows']:,} rows; unions have {analysis['union_rows']:,}.
Rules: {analysis['registry_rules']}. Primary raw family entries: {analysis['primary_events']:,}.
All/first-qualifying-per-day/sixty-minute spacing, six half-years, unknown groups,
matched-price cohorts, policy transitions and prespecified opportunity unions retained.
Each union deduplicates date/minute; extra entries are measured outside thrust.
Whole-date bootstrap uses5000 shared draws, seed20260919; multiple-testing adjustment
is not claimed. Sparse all-win/all-loss rate intervals are withheld.

## Files

* option_history_greeks_*/ and option_list_contracts/: immutable native Parquet and
  exact request metadata. Existing external caches are referenced with hashes.
* days/SYMBOL/DATE.json: dated manifests, allowed bracket status, native paths/hashes.
  Inherited selection schemas are preserved; normalized_expiry_selections.json is
  the canonical selected-versus-listed interpretation.
* derived/SYMBOL/minutes/: strict ATM, recovered policies, surface coordinates, spot,
  bid/ask-derived coordinate envelopes, integer ET minute/date/symbol keys.
* derived/SYMBOL/windows/: balanced within-window nearby recovery using unique actual
  timestamps; no historical MAD normalization. receipts/ links every output to native
  hashes and the dated manifest.
* sector_features.parquet: one row per date/entry minute/ETF; strictly prior reference,
  separate breakout update and separately labeled post15 observations.
* basket_features.parquet and rule_registry.parquet: fixed yes/no/unknown signals and
  full taxonomy; measured counts and price-context controls.
* weights/raw/: unvalidated HTTP response bodies and immutable retrieval receipts.
  Never consume these by a blind raw-file glob. validation_runs/ separates retrieved
  bodies from accepted/rejected weights, and supports revalidation without refetch.
  404 dates accepted;17 retrieved bodies rejected under the unchanged parser. They
  remain unknown for weighting. IVV is a historical equity-weight proxy; precise
  publication/vintage timing is uncertified.
* matched_pairs.parquet / matched_ledger.parquet / match_freeze.json: feature-only
  global and within-half matching frozen before outcome attachment, exact rising
  count and ten-basis-point median-return caliper, no reuse.
* joined_events.parquet: original score/identity plus IV features, with development
  clearly labeled. No change to native price outcomes.
* comparison.csv, measured_baselines.csv, uncertainty.csv, unions.csv,
  matched_summary.csv, contextual_comparisons.csv, policy_transitions.csv and
  cohort_comparisons.csv: complete numeric evidence. Rates are percentages; retention
  is a fraction of identical winning date/minute baseline entries, not retimed trades.
* checkpoint_*: genuinely new entryT+15, validated VT prefix and fresh60-minute score;
  never used as information at originalT. Original pilot's45-minute remainder differs.
* independent_verification.json / legacy_measurement_replay.json: full count/native
  provenance audit and exact reproduction of45,760 old sector/policy measurements.
* logs/, source_snapshots/, protocol/feature/basket freezes: auditable execution history.

Native sector-days: {verification['native']['sector_days']:,}; statuses:
{json.dumps(verification['native']['statuses'],sort_keys=True)}.
All {verification['counts']['summary_rows_reconciled']:,} summary rows and
{verification['unions']['union_rows_reconciled']:,} union rows independently reconciled;
312 original unfiltered score rows reproduced. Review status: {review['status']}.

Payload: {inventory['files']:,} files /{inventory['bytes']:,} bytes, excluding this
dictionary, inventory.json, registration_transaction.json and root registry Markdown. API attempts: {calls}.
Previous datasets and the interactive dashboard remain untouched.
'''
    section = f'''\n\n## {SECTION} — prior ETF IV rules, +5/−10, above VT (2026-09-19)

Namespace: `{DATA}`. Findings: `{OUT}/FINDINGS.md`.

Same411 primary dates plus10 development, thirteen price families, strict causal VT,
+5 before−10 in60 native minutes. Eleven-ETF30DTE ATM/wings and original quote rules,
weighted and equal breadth, price pairing/matching, confirmation, and fixed N-expansion
unions. No MAD-history collection. Every original150-day sector/policy measurement
reproduces exactly (45,760). All {analysis['table_rows']:,} comparison rows and
{analysis['union_rows']:,} union rows reconcile. 404 issuer dates validated;17 retrieved
but rejected by unchanged rules, preserved for later revalidation. Missingness is explicit.

{inventory['files']:,} payload files /{inventory['bytes']:,} bytes, with exact schemas,
hashes and exclusions in inventory.json and the namespace dictionary. Calls: {calls}.
Claude review: {review['status']}; limitations and dispositions in findings/review notes.
'''
    journal = f'''\n\n## 2026-09-19 — create — full-population prior-rule IV comparison

- **date:** 2026-09-19
- **operator:** Codex / Branch B IV side conversation
- **repo_session:** delta_bomb
- **op_type:** create
- **paths_touched:** `{DATA}/`; `{CENTRAL}/DATA_DICTIONARY.md`; `{CENTRAL}/CHANGELOG.md`
- **size_delta_bytes:** +{inventory['bytes']} (namespace payload; inventory/registration transaction/dictionaries/root registry excluded)
- **file_count_delta:** +{inventory['files']} (same scope)
- **orats_calls_consumed:** 0
- **thetadata_calls_consumed:** {calls['thetadata']} (data attempts; authentication excluded)
- **public_issuer_calls_consumed:** {calls['public_issuer']}
- **reversibility:** reversible (new namespace; older native/derived data preserved)
- **dictionary_section:** {SECTION} and namespace DATA_DICTIONARY.md
- **dictionary_reconciled:** true
- **manifests_updated:** protocol/feature/basket/matching freezes, normalized_expiry_selections.json, native_input_hashes.json, independent_verification.json, analysis_complete.json, review_status.json, inventory.json
- **why:** User requested all previously executable IV ideas tested across the full2024–2026 above-VT study with +5 before−10 in60 minutes, balancing N and accuracy, followed by independent Claude review.
- **coverage:** {verification['native']['sector_days']} sector-days accounted for; {json.dumps(verification['native']['statuses'],sort_keys=True)}. Unknowns never become nonqualifiers. No new MAD history. All market data and derived evidence stored centrally.
- **verification:** 45,760 legacy measurements reproduce exactly;312 original baseline rows and all {analysis['table_rows']} new comparison/{analysis['union_rows']} union rows reconcile. Unchanged native score hashes. Review {review['status']}; repairs documented before final conclusions.
- **findings:** See `{OUT}/FINDINGS.md` for the complete N/accuracy tradeoffs, six-half-year evidence, quote-policy transitions, matching and review limitations; no isolated percentage is promoted without its sample count and coverage.
'''
    updates = [(DATA/'DATA_DICTIONARY.md',text),
        (CENTRAL/'DATA_DICTIONARY.md',(CENTRAL/'DATA_DICTIONARY.md').read_text()+section),
        (CENTRAL/'CHANGELOG.md',(CENTRAL/'CHANGELOG.md').read_text()+journal),
        (DATA/'inventory.json',json.dumps(inventory,indent=2,sort_keys=True)+'\n')]
    commit_files(plan_path,updates)
    print(json.dumps(dict(files=inventory['files'],bytes=inventory['bytes'],calls=calls)))


if __name__ == '__main__':
    main()
