"""Replay the completed warmup early, while later native dates download."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
import pandas as pd

import spx_mad as p


def main() -> None:
    p.freeze()
    sessions, targets = p.date_plan()
    dates = sessions[:60] + targets[:1]
    records = [json.loads((p.DATA / 'days' / 'SPXW' / f'{day}.json').read_text())
               for day in dates]
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(p.legacy.derive_day, records))
    history = pd.concat([pd.read_parquet(p.DATA / 'derived' / 'SPXW' / 'windows' / f'{day}.parquet')
                         for day in sessions[:60]], ignore_index=True)
    verify = p.load_module('spx_first_target_verifier', p.OUT / 'verify.py')
    checks = []
    for block in range(5):
        stats = p.historical_baseline(history, sessions, targets[0], block)
        sample = history[history.block.eq(block) & history.available]
        assert stats['status'] == 'ok'
        assert max(stats['source_dates']) < targets[0]
        verify.assert_lower_median(sample.acceleration.to_numpy(), sample.date, stats['median'])
        verify.assert_lower_median(abs(sample.acceleration.to_numpy() - stats['median']),
                                   sample.date, stats['mad'])
        assert np.isfinite(stats['scale']) and stats['scale'] > 1e-12
        checks.append({'block': block, 'history_days': stats['history_days'],
                       'windows': stats['history_windows'], 'scale': stats['scale']})
    p.write_json(p.DATA / 'first_target_check.json', {
        'target': targets[0], 'prior_sessions': sessions[:60], 'checks': checks,
        'producer_sha256': p.digest(Path(__file__))})
    print(json.dumps(checks, indent=2))


if __name__ == '__main__':
    main()
