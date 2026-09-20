"""Derive a fixed snapshot of captured dates while the collector is still running."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

import spx_mad as p


def main() -> None:
    p.freeze()
    # Invoke only while collection is well short of completion: the full runner
    # owns final calibration and must not derive the same dates concurrently.
    if (p.DATA / 'SPXW_collection.json').exists():
        raise RuntimeError('Collection finished; let the full runner own derivation')
    records = [json.loads(path.read_text())
               for path in sorted((p.DATA / 'days' / 'SPXW').glob('*.json'))
               if not (p.DATA / 'derived' / 'SPXW' / 'metadata' / path.name).exists()]
    p.emit('captured_snapshot', dates=len(records))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(p.legacy.derive_day, row) for row in records]
        for i, future in enumerate(as_completed(futures), 1):
            future.result()
            if i % 20 == 0 or i == len(futures):
                p.emit('captured_snapshot_measure', complete=i, total=len(futures))
    p.emit('captured_snapshot_complete')


if __name__ == '__main__':
    main()
