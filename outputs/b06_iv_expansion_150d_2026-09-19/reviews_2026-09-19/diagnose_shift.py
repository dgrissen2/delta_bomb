"""Descriptive attribution of the observed shift; no thresholds optimized."""
from pathlib import Path
import json

import numpy as np
import pandas as pd

SOURCE = Path(__file__).resolve().parent.parent
DEST = Path('/Users/dgrissen/Dev/central_trade_data/thetadata/'
            'b06_iv_expansion_150d_audit_2026-09-19-v1')
POLICIES = ['original', 'midpoint', 'guarded_100', 'guarded_50']


def bootstrap(base: pd.DataFrame, selected: pd.DataFrame,
              dates: list[str], block: str = 'date') -> tuple[float, float]:
    def counts(frame: pd.DataFrame) -> pd.DataFrame:
        x = frame.assign(hit=frame.outcome.eq('target_first').astype(int))
        g = x.groupby('date').agg(n=('hit','size'), wins=('hit','sum')).reindex(dates, fill_value=0)
        if block == 'month':
            g = g.groupby(g.index.str[:7]).sum()
        return g
    a, b = counts(base), counts(selected)
    assert a.index.equals(b.index)
    rng = np.random.default_rng(20260919)
    idx = rng.integers(0, len(a), size=(10000,len(a)))
    at = a.to_numpy()[idx].sum(axis=1); bt = b.to_numpy()[idx].sum(axis=1)
    valid = (at[:,0] > 0) & (bt[:,0] > 0)
    dif = 100*(bt[valid,1]/bt[valid,0] - at[valid,1]/at[valid,0])
    return tuple(np.quantile(dif,[.025,.975]).tolist())


def main() -> None:
    events = pd.read_csv(DEST/'event_vt_audit.csv')
    daily = pd.read_csv(DEST/'day_vt_audit.csv')
    ledger = pd.read_csv(SOURCE/'event_ledger.csv')
    events['hit'] = events.outcome.eq('target_first')
    records, contrasts, regimes = [], [], []
    for gate in ['all_open_above','entry_above','always_above_through_entry']:
        subset = events if gate == 'all_open_above' else events[events[gate]]
        for cohort in ['original_50','additional_100','combined_150']:
            base = subset if cohort == 'combined_150' else subset[subset.cohort.eq(cohort)]
            dates = daily.date.tolist() if cohort == 'combined_150' else daily[daily.cohort.eq(cohort)].date.tolist()
            for policy in POLICIES:
                ids = ledger.loc[ledger.variant.eq(policy) & ledger.accelerating_state.eq('yes'),'episode_id']
                y = base[base.episode_id.isin(ids)]
                a, b = bootstrap(base,y,dates)
                records.append({'vt_gate':gate,'cohort':cohort,'policy':policy,
                    'uplift_pp':100*(y.hit.mean()-base.hit.mean()),'date_ci_low_pp':a,'date_ci_high_pp':b,
                    'month_ci_pp':json.dumps(bootstrap(base,y,dates,'month'))})
                perday = base.groupby('date').hit.mean()
                expected = float(y.date.map(perday).mean())
                # Exact decomposition: weighting days like the filter + residual within those days.
                composition = expected - base.hit.mean()
                within = y.hit.mean() - expected
                assert abs(composition + within - (y.hit.mean()-base.hit.mean())) < 1e-12
                no = base[~base.episode_id.isin(ids)]
                yd = y.groupby('date').hit.agg(['size','mean'])
                nd = no.groupby('date').hit.agg(['size','mean'])
                common = yd.join(nd,lsuffix='_y',rsuffix='_n',how='inner')
                weights = common.size_y * common.size_n / (common.size_y+common.size_n)
                matched = float(np.average(common.mean_y-common.mean_n,weights=weights))
                contrasts.append({'vt_gate':gate,'cohort':cohort,'policy':policy,
                    'base_pct':base.hit.mean()*100,'selected_pct':y.hit.mean()*100,
                    'date_weighted_base_pct':expected*100,'date_mix_component_pp':composition*100,
                    'within_date_component_pp':within*100,'same_day_yes_vs_other_pp':matched*100,
                    'comparable_dates':len(common),'selected_n':len(y)})
        for label, mask in [('original_50',subset.cohort.eq('original_50')),
                            ('new_2025',subset.cohort.eq('additional_100') & subset.date.str.startswith('2025')),
                            ('new_2026',subset.cohort.eq('additional_100') & subset.date.str.startswith('2026'))]:
            b = subset[mask]
            days = daily[daily.date.isin(b.date)]
            for policy in ['baseline',*POLICIES]:
                q = b
                if policy != 'baseline':
                    ids = ledger.loc[ledger.variant.eq(policy) & ledger.accelerating_state.eq('yes'),'episode_id']
                    q = b[b.episode_id.isin(ids)]
                regimes.append({'vt_gate':gate,'cohort_year':label,'policy':policy,'n':len(q),
                    'target_pct':q.hit.mean()*100,'adverse_pct':q.outcome.eq('adverse_first').mean()*100,
                    'neither_pct':q.outcome.eq('neither').mean()*100,
                    'baseline_active_day_opening_range_median':float(days.opening_35m_range.median())})
    for name, rows in [('diagnostic_intervals',records),('date_mix_decomposition',contrasts),
                       ('cohort_year_outcomes',regimes)]:
        path = DEST/(name+'.csv')
        if path.exists():
            raise FileExistsError(path)
        pd.DataFrame(rows).to_csv(path,index=False)
    print(pd.DataFrame(contrasts).query("policy == 'original'").to_string(index=False))
    print(pd.DataFrame(records).query("vt_gate == 'always_above_through_entry'").to_string(index=False))
    print(pd.DataFrame(regimes).query("vt_gate == 'all_open_above' and policy in ['baseline','original']").to_string(index=False))

    # Unknowns are explicitly excluded from this separate contrast.
    state_rows = []
    for cohort in ['original_50','additional_100']:
        for policy in POLICIES:
            z = ledger[ledger.cohort.eq(cohort) & ledger.variant.eq(policy)].copy()
            z['hit'] = z.outcome.eq('target_first')
            yes = z[z.accelerating_state.eq('yes')]
            no = z[z.accelerating_state.eq('no')]
            a = yes.groupby('date').hit.agg(['size','mean'])
            b = no.groupby('date').hit.agg(['size','mean'])
            c = a.join(b,lsuffix='_y',rsuffix='_n',how='inner')
            weights = c.size_y*c.size_n/(c.size_y+c.size_n)
            state_rows.append({'cohort':cohort,'policy':policy,'yes_n':len(yes),'no_n':len(no),
                'comparable_dates':len(c),
                'same_day_yes_vs_definite_no_pp':float(np.average(c.mean_y-c.mean_n,weights=weights)*100),
                'yes_neither_pct':float(yes.outcome.eq('neither').mean()*100),
                'no_neither_pct':float(no.outcome.eq('neither').mean()*100),
                'yes_adverse_pct':float(yes.outcome.eq('adverse_first').mean()*100),
                'no_adverse_pct':float(no.outcome.eq('adverse_first').mean()*100)})
    path = DEST/'definite_state_contrasts.csv'
    if path.exists():
        raise FileExistsError(path)
    pd.DataFrame(state_rows).to_csv(path,index=False)


if __name__ == '__main__':
    main()
