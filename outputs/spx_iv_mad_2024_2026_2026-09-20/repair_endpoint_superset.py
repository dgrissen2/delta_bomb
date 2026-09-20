"""Resolve one native IV-only contract superset without changing quote checks."""
from copy import deepcopy
import json
from pathlib import Path

import pandas as pd

import spx_mad as p


def align_iv_superset(iv: pd.DataFrame, greek: pd.DataFrame) -> pd.DataFrame:
    """Keep every Greek key and its unchanged native IV counterpart, or fail.

    This only handles a strict IV superset. Duplicate keys, missing counterparts,
    and other endpoint asymmetries are not silently intersected away.
    """
    surface = p.legacy.surface
    left = surface._endpoint(iv, surface.KEY, 'iv')
    right = surface._endpoint(greek, surface.KEY, 'greeks')
    left_keys = pd.MultiIndex.from_frame(left[surface.KEY])
    right_keys = pd.MultiIndex.from_frame(right[surface.KEY])
    if len(right_keys.difference(left_keys)):
        raise ValueError('Greek key lacks an IV counterpart; not a superset repair')
    if len(left_keys) <= len(right_keys):
        raise ValueError('A strict IV superset is required')
    keep = left_keys.isin(right_keys)
    result = iv.loc[keep].reset_index(drop=True)
    if len(result) != len(greek):
        raise ValueError('Pairing did not preserve every Greek key exactly once')
    return result


def main() -> None:
    p.freeze()
    day = '2026-06-09'
    records = json.loads((p.DATA / 'SPXW_collection.json').read_text())
    original = next(row for row in records if row['date'] == day)
    iv_inputs = [r for r in original['raw_files']
                 if r['method'] == 'option_history_greeks_implied_volatility']
    greek_inputs = [r for r in original['raw_files']
                    if r['method'] == 'option_history_greeks_first_order']
    if len(iv_inputs) != 1 or len(greek_inputs) != 1:
        raise ValueError('Repair scoped to the observed single-expiry response pair')
    iv = p.legacy.checked_read(iv_inputs[0]['path'], iv_inputs[0]['sha256'])
    greek = p.legacy.checked_read(greek_inputs[0]['path'], greek_inputs[0]['sha256'])
    if (len(iv), len(greek)) != (79200, 36000):
        raise ValueError('Observed anomaly changed; inspect rather than generalize')
    p.write_json(p.DATA / 'endpoint_pairing_freeze.json', {
        'date': day, 'scope': 'IV strict-superset alignment only; retain every Greek key',
        'original_protocol_sha256': p.digest(p.DATA / 'protocol_freeze.json'),
        'inputs': {r['path']: r['sha256'] for r in original['raw_files']},
        'producer_sha256': p.digest(Path(__file__)),
        'test_sha256': p.digest(p.OUT / 'test_endpoint_pairing.py'),
        'addendum_sha256': p.digest(p.OUT / 'PROTOCOL_ADDENDUM.md')})
    aligned = align_iv_superset(iv, greek)
    prepared = p.legacy.surface._prepare(aligned, greek)
    assert len(prepared) == len(greek)
    destination = p.DATA / 'paired_inputs' / 'SPXW' / f'{day}_iv.parquet'
    p.write_frame(destination, aligned)
    paired = deepcopy(original)
    for row in paired['raw_files']:
        if row['method'] == 'option_history_greeks_implied_volatility':
            row.update(path=str(destination), sha256=p.digest(destination), rows=len(aligned))
    receipt = {'date': day, 'original_record': original, 'paired_record': paired,
               'native_iv_rows': len(iv), 'native_greek_rows': len(greek),
               'paired_rows': len(aligned), 'iv_only_rows_excluded': len(iv) - len(aligned),
               'greek_keys_dropped': 0, 'native_values_changed': 0,
               'matching_quote_rows': int(prepared.endpoint_match.sum()),
               'quality_checks': 'Unmodified surface._prepare and frozen recovery functions',
               'freeze_sha256': p.digest(p.DATA / 'endpoint_pairing_freeze.json')}
    p.write_json(p.DATA / 'endpoint_pairing_receipt.json', receipt)
    metadata = p.legacy.derive_day(paired)
    print(json.dumps({'paired_rows': len(aligned), 'measured_windows': metadata['measured_windows'],
                      'expected_windows': metadata['window_slots']}))


if __name__ == '__main__':
    main()
