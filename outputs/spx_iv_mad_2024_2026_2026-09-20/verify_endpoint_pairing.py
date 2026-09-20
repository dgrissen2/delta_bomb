"""Independently replay the one recorded native endpoint alignment using a merge."""
import json
from pathlib import Path

import pandas as pd

import spx_mad as p


def main() -> None:
    receipt = json.loads((p.DATA / 'endpoint_pairing_receipt.json').read_text())
    original, paired = receipt['original_record'], receipt['paired_record']
    day = receipt['date']
    assert original == json.loads((p.DATA / 'days' / 'SPXW' / f'{day}.json').read_text())
    collection = json.loads((p.DATA / 'SPXW_collection.json').read_text())
    assert original == next(r for r in collection if r['date'] == day)
    frames = {r['method']: p.legacy.checked_read(r['path'], r['sha256'])
              for r in original['raw_files']}
    iv = frames['option_history_greeks_implied_volatility']
    greek = frames['option_history_greeks_first_order']
    pair_input = next(r for r in paired['raw_files']
                      if r['method'] == 'option_history_greeks_implied_volatility')
    actual = p.legacy.checked_read(pair_input['path'], pair_input['sha256'])
    key = ['symbol', 'expiration', 'strike', 'right', 'timestamp']
    assert not iv.duplicated(key).any() and not greek.duplicated(key).any()
    replay = greek[key].merge(iv, on=key, how='left', validate='one_to_one', indicator=True)
    assert replay._merge.eq('both').all() and len(replay) == len(greek) == 36000
    pd.testing.assert_frame_equal(
        replay[iv.columns].sort_values(key).reset_index(drop=True),
        actual.sort_values(key).reset_index(drop=True))
    metadata = json.loads((p.DATA / 'derived' / 'SPXW' / 'metadata' / f'{day}.json').read_text())
    assert metadata['input_hashes'] == {r['path']: r['sha256'] for r in paired['raw_files']}
    assert metadata['measured_windows'] == metadata['window_slots'] == 271
    result = {'date': day, 'all_greek_keys_preserved': True, 'native_values_unchanged': True,
              'original_manifests_unchanged': True, 'paired_rows': len(actual),
              'iv_only_rows_excluded': len(iv) - len(actual),
              'receipt_sha256': p.digest(p.DATA / 'endpoint_pairing_receipt.json'),
              'verifier_sha256': p.digest(Path(__file__))}
    p.write_json(p.DATA / 'endpoint_pairing_verification.json', result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
