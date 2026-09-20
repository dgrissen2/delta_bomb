"""Append reviewed missingness disclosures to the exact verified numeric report."""
from __future__ import annotations

import pandas as pd

from inputs import DATA, OUT
from provenance import check_manifest


def main() -> None:
    check_manifest(DATA/'independent_verification.json')
    check_manifest(DATA/'additive_review_audit.json')
    values = pd.read_csv(DATA/'unknown_performance_summary.csv')
    reasons = pd.read_csv(DATA/'unknown_reason_summary.csv')
    errors = pd.read_csv(DATA/'uncertainty.csv')
    body = ['# Additional review disclosures',
        'These tables are an additive presentation of the unchanged verified results. '
        'Structural missingness, unknown-cohort performance and the eight-sector '
        'candidates remain visible. All counts below are primary recipe entries; '
        'different families can share an execution, so do not sum them as unique trades.',
        '## Signals before a full same-session reference can exist',
        '741 primary recipe entries occur before 10:05 ET. Their T−35 reference '
        'begins before 09:30; no amount of quote recovery fixes this structural gap. '
        'All other unresolved conditions and rejected issuer snapshots are separated '
        'in unknown_reason_summary.csv. Native expiry gaps are additionally recorded '
        'per entry in entry_missingness_context.parquet.',
        reasons[reasons.rule.eq('original_falling_6')&reasons.reason.eq('reference_starts_before_0930')][
            ['variant','n','targets','rate','days']].to_markdown(index=False,floatfmt='.1f')]
    selections = {
        'b06_breakout':['original_falling_6','original_accelerating_6','midpoint_accelerating_6','guarded_100_accelerating_6'],
        'b07':['original_accelerating_6','midpoint_accelerating_6','guarded_50_weighted_accelerating'],
        'b09':['original_accelerating_8','midpoint_accelerating_8','guarded_100_accelerating_8','guarded_50_accelerating_8'],
        'b10_breakout':['original_accelerating_6','midpoint_accelerating_6','guarded_100_accelerating_6']}
    for variant,rules in selections.items():
        selected = values[values.variant.eq(variant)&values.rule.isin(rules)]
        body += [f'## {variant}: yes, no, unknown and comparable coverage',
                 selected[['rule','state','n','targets','rate','days']].to_markdown(index=False,floatfmt='.1f')]
        ci = errors[errors.variant.eq(variant)&errors['mode'].eq('all')&errors.rule.isin(rules)]
        body += ['95% whole-date intervals; differences are percentage points. '
                 'No multiple-comparison adjustment. No interval here proves that an '
                 'N-expanding union has higher accuracy than thrust.',
                 ci[['rule','low','high','delta_no_low','delta_no_high','delta_all_low','delta_all_high']].to_markdown(index=False,floatfmt='.1f')]
    body += ['## Evaluated rules with no qualifying entries',
        'All four quote_resolved falling/acceleration rules (six/eight sectors) had '
        'zero qualifying entries. Their NaN success percentages mean N=0 after an '
        'evaluated condition; this is not a failed data download. The conservative '
        'quote-envelope rule did not resolve a broad sign in these observations. '
        'This is not a proof that it could never qualify on any possible future data.',
        '## Execution and identity notes',
        'The main per-family headline tables use all entries, where retained winners '
        'are a literal subset. For first/spaced modes, the retention columns count '
        'shared winning date/minute identities; filtering can replace the chosen '
        'minute. They do not count a differently timed successful trade as retained.',
        'Use matched_pairs_canonical.parquet and canonical_pair_id for future joins. '
        'Original pair_id restarts within each rule/scope/stratum; the current analysis '
        'already uses those groups and joins outcomes by event identity. All 3,524 '
        'canonical pair identifiers are unique.',
        'Fifty validated reused issuer bodies have no recorded HTTP status. '
        'issuer_http_provenance.csv preserves that distinction; parse validation '
        'still governs all accepted weights. All 421 as-of dates are strictly prior.']
    path = OUT/'RESULT_TABLES.md'
    original = path.read_text().split('# Additional review disclosures')[0].rstrip()
    path.write_text(original+'\n\n'+'\n\n'.join(body)+'\n')


if __name__ == '__main__':
    main()
