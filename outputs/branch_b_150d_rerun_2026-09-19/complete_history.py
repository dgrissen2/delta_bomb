"""Add existing population-ledger SPX sources without changing frozen recipes."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import run
import analyze

DATA = run.CENTRAL/'branch_b_150d_rerun_2026-09-19-v2'
POPULATION = run.EXPANSION/'research/population_ledger.csv'
ORIGINAL_HISTORY = run.history
HISTORY_CALLS = 0


def expanded_history(sources: list[dict[str, Any]]) -> tuple:
    """Preserve first original-inventory replay; complete the expanded inventory."""
    global HISTORY_CALLS
    HISTORY_CALLS += 1
    if HISTORY_CALLS == 1:
        return ORIGINAL_HISTORY(sources)
    cutoff = max(r['date'] for r in sources if r.get('included_in_warmup',True))
    combined = {r['date']:r for r in sources}
    population = pd.read_csv(POPULATION)
    for row in population[population.source_path.notna() & population.date.le(cutoff)].itertuples():
        if row.date not in combined:
            combined[row.date] = {'date':row.date,'path':row.source_path,'sha256':row.source_sha256}
    return ORIGINAL_HISTORY(list(combined.values()))


def verify_adapter() -> None:
    import json
    for path,wanted in json.loads((DATA/'adapter_freeze.json').read_text())['hashes'].items():
        if run.digest(Path(path)) != wanted:
            raise ValueError('Complete-history adapter or source ledger changed')


def main(stage: str) -> None:
    run.DATA = DATA
    analyze.DATA = DATA
    if stage == 'prepare':
        run.history = expanded_history
        run.prepare()
        run.write_json(DATA/'adapter_freeze.json',{
            'at':datetime.now(timezone.utc).isoformat(),'before_outcomes':True,
            'hashes':{str(p):run.digest(p) for p in [Path(__file__),POPULATION,
                run.OUT/'WARMUP_CORRECTION.md']}})
    else:
        verify_adapter()
        {'freeze':analyze.freeze,'generate':run.generate,
         'outcomes':run.outcomes,'analyze':analyze.analyze}[stage]()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['prepare','freeze','generate','outcomes','analyze'])
    main(parser.parse_args().stage)
