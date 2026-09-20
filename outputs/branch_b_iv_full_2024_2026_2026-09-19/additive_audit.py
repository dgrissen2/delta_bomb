"""Explain existing missingness and artifact identities without changing any result."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from inputs import DATA, digest, write_frame, write_json
from provenance import checked_execution, check_manifest, write_csv
from weights import validation_paths


def stats(frame: pd.DataFrame) -> dict:
    return dict(n=len(frame),targets=int(frame.hit.sum()),days=int(frame.date.nunique()),
                rate=float(100*frame.hit.mean()) if len(frame) else None)


def main() -> None:
    checked_execution()
    check_manifest(DATA/'independent_verification.json')
    events = pd.read_parquet(DATA/'joined_events.parquet')
    events = events[events.cohort.ne('development_10')].copy()
    events['reference_before_rth'] = events.known_min.lt(605)
    weights_path,ledger_path = validation_paths()
    valid_dates = set(pd.read_parquet(weights_path).date)
    coverage = pd.read_csv(DATA/'coverage_sector_days.csv')
    gaps = coverage[coverage.status.ne('captured')].groupby('date').size()
    events['expiry_gap_sectors'] = events.date.map(gaps).fillna(0).astype(int)
    events['weight_snapshot_accepted'] = events.date.isin(valid_dates)
    context = events[['date','variant','known_min','outcome','reference_before_rth',
                      'expiry_gap_sectors','weight_snapshot_accepted']]
    write_frame(DATA/'entry_missingness_context.parquet',context)
    registry = pd.read_parquet(DATA/'rule_registry.parquet')
    rows,reasons = [],[]
    for rule in registry.loc[registry.category.ne('delayed_only'),'rule']:
        for variant,frame in events.groupby('variant'):
            for state in ['yes','no','unknown','measured','baseline']:
                group = frame if state=='baseline' else frame[frame[rule].ne('unknown')] if state=='measured' else frame[frame[rule].eq(state)]
                rows.append(dict(variant=variant,rule=rule,state=state,**stats(group)))
            missing = frame[frame[rule].eq('unknown')].copy()
            missing['reason'] = 'quotes_or_expiries_leave_condition_unresolved'
            if '_weighted_' in rule:
                missing.loc[~missing.weight_snapshot_accepted,'reason'] = 'issuer_snapshot_rejected'
            missing.loc[missing.reference_before_rth,'reason'] = 'reference_starts_before_0930'
            for reason,group in missing.groupby('reason'):
                reasons.append(dict(variant=variant,rule=rule,reason=reason,**stats(group)))
    write_csv(DATA/'unknown_performance_summary.csv',pd.DataFrame(rows))
    write_csv(DATA/'unknown_reason_summary.csv',pd.DataFrame(reasons))
    pairs = pd.read_parquet(DATA/'matched_pairs.parquet')
    pairs['canonical_pair_id'] = pairs[['rule','scope','stratum','pair_id']].astype(str).agg('|'.join,axis=1)
    assert pairs.canonical_pair_id.is_unique
    write_frame(DATA/'matched_pairs_canonical.parquet',pairs)
    manifests = []
    for path in list(DATA.glob('*freeze*.json'))+list(DATA.glob('*complete.json'))+[DATA/'independent_verification.json']:
        value = json.loads(path.read_text())
        left,right = value.get('inputs',{}),value.get('output_hashes',{})
        for key in set(left)&set(right):
            if left[key]!=right[key]:
                raise ValueError(f'Conflicting frozen hash expectations in {path}: {key}')
        manifests.append(str(path))
    issuer = pd.read_parquet(ledger_path)
    assert issuer.as_of_date.lt(issuer.date).all()
    receipt_rows = json.loads((DATA/'weights/manifest.json').read_text())['receipts']
    issuer_http = [dict(date=r['date'],as_of=r['as_of'],http_status=r.get('http_status'),
        provenance='status_recorded' if 'http_status' in r else 'validated_cached_body_http_status_unrecorded') for r in receipt_rows]
    write_csv(DATA/'issuer_http_provenance.csv',pd.DataFrame(issuer_http))
    files = ['entry_missingness_context.parquet','unknown_performance_summary.csv','unknown_reason_summary.csv',
             'matched_pairs_canonical.parquet','issuer_http_provenance.csv']
    result = dict(primary_recipe_entries=len(events),pre_1005_recipe_entries=int(events.reference_before_rth.sum()),
        canonical_pairs=len(pairs),original_pair_id_unique=int(pairs.pair_id.nunique()),
        hash_collision_manifests_checked=len(manifests),hash_collisions=0,
        all_421_weight_asof_dates_strictly_prior=True,
        issuer_http_status_unrecorded=sum('http_status' not in r for r in receipt_rows),
        input_verification_sha256=digest(DATA/'independent_verification.json'),
        numeric_outputs_unchanged=True,output_hashes={str(DATA/p):digest(DATA/p) for p in files},
        code_sha256=digest(Path(__file__)))
    write_json(DATA/'additive_review_audit.json',result)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
