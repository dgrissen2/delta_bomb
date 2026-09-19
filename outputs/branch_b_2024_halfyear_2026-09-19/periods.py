"""Outcome-independent period membership and native-history coverage decisions."""
from datetime import date

import pandas as pd

PERIODS = [f'{year}_H{half}' for year in (2024, 2025, 2026) for half in (1, 2)]


def half_year(day: str) -> str:
    parsed = date.fromisoformat(day)
    return f'{parsed.year}_H{1 if parsed.month <= 6 else 2}'


def cohort(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == 'all_qualifying':
        return frame
    if name == 'combined_non_development':
        return frame[frame.cohort.ne('development_10')]
    if name in PERIODS:
        return frame[frame.cohort.ne('development_10') & frame.date.map(half_year).eq(name)]
    if name == 'combined_150':
        return frame[frame.cohort.isin(['original_50', 'additional_100'])]
    if name == 'prior_239':
        return frame[frame.cohort.isin(['original_50', 'additional_100', 'third_tranche'])]
    if name.startswith('third_20'):
        return frame[frame.cohort.eq('third_tranche') & frame.date.str[:4].eq(name[-4:])]
    if name.startswith('added_20'):
        return frame[frame.cohort.eq('additional_100') & frame.date.str[:4].eq(name[-4:])]
    return frame[frame.cohort.eq(name)]


def coverage_dates(ledger: pd.DataFrame) -> list[str]:
    # Even ineligible sessions supply chronological indicator history.
    return ledger[ledger.date.str.startswith('2024') & ~ledger.complete_spx &
                  ~ledger.early_close].date.tolist()


def history_sources(old: pd.DataFrame, population: pd.DataFrame) -> list[dict]:
    sources = {r.date: {'date': r.date, 'path': r.path, 'sha256': r.sha256,
                       'included_in_warmup': bool(r.included_5m),
                       'included_in_rsi_warmup': bool(r.included_1m)} for r in old.itertuples()}
    for r in population[population.source_path.notna() & population.source_path.ne('')].itertuples():
        if r.date not in sources or (r.complete_spx and sources[r.date]['path'] != r.source_path):
            sources[r.date] = {'date': r.date, 'path': r.source_path, 'sha256': r.source_sha256}
    return sorted(sources.values(), key=lambda r: r['date'])
