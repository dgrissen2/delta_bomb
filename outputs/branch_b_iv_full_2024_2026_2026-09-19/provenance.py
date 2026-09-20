"""Check immutable source and output manifests before consuming research artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from inputs import DATA, OUT, PRICE, SCORE, digest, write_json


def check_hashes(hashes: dict) -> None:
    for name,expected in hashes.items():
        if digest(Path(name)) != expected:
            raise ValueError(f'Changed frozen input or output: {name}')


def check_manifest(path: Path) -> dict:
    value = json.loads(path.read_text())
    check_hashes(value.get('inputs',{}) | value.get('output_hashes',{}))
    return value


def execution_freeze() -> None:
    """Freeze executable dependencies before outcome-blind event features are assembled."""
    dependencies = [
        'b06_iv_recovery_findings_2026-09-19/evidence.json',
        'b06_iv_expansion_150d_2026-09-19/iv_rules.py',
        'b06_sector_surface_50d_2026-09-13/surface.py',
        'b06_iv_matched_price_2026-09-17/matching.py',
        'xlre_balanced_baseline_2026-09-19/inventory.py',
        'xlre_balanced_baseline_2026-09-19/balanced.py',
        'sector_iv_mad_2025_2026_2026-09-19/pipeline.py',
        'sector_iv_mad_2025_2026_2026-09-19/calibrate_exact.py',
        'branch_b_150d_rerun_2026-09-19/rerun_core.py',
        'branch_b_stop10_2026-09-19/scoring.py',
        'b06_sector_weighted_iv_2026-09-19/weights.py']
    paths = list(OUT.glob('*.py'))+[OUT/p for p in ['PROTOCOL.md','SCOPE_CLARIFICATION.md','IDEA_INVENTORY.md']]
    paths += [OUT.parent/p for p in dependencies]
    paths += [PRICE/'events_before_outcomes.parquet',PRICE/'selected_days.csv',SCORE/'event_outcomes.parquet']
    value = dict(inputs={str(p):digest(p) for p in paths},
                 timing='After native derivation, before event features and new outcome comparisons',
                 note='Native derivation predates this expanded dependency freeze; native and legacy replay validate it.')
    write_json(DATA/'execution_freeze.json',value)


def checked_execution() -> dict:
    return check_manifest(DATA/'execution_freeze.json')


def write_csv(path: Path, frame) -> None:
    content = frame.to_csv(index=False)
    if path.exists():
        if path.read_text() != content:
            raise ValueError(f'Attempt to replace immutable table: {path}')
    else:
        path.write_text(content)
