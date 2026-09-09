"""Publish the fixed daily-surface experiment and the recent exact-call bridge."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from pandar_eligibility import fmt, table
from pandar_skew_journey_data import OUTPUT

LABELS = {
    'all_eligible': 'All eligible daily surfaces', 'high_rank': 'High front-wing rank ≥85',
    'high_positive_wing': 'High rank + wing above ATM', 'high_age1_2': 'High rank, age 1–2',
    'high_age3_5': 'High rank, age 3–5', 'high_age6plus': 'High rank, age 6+',
    'high_age_unknown': 'High rank, age left-censored', 'high_expanding': 'High rank, expanding wing',
    'high_rollover': 'High rank, rolling-over wing', 'high_mature_rollover': 'Age ≥3 + rollover',
    'high_premia_coverage': 'High rank, both RV/IV windows available',
    'high_both_premia': 'High rank + positive 30/60 variance premia',
    'high_exhaustion': 'High rank + price/IV exhaustion',
    'high_mature_rollover_premia_exhaustion': 'Age ≥3 + rollover + premia + exhaustion',
    'high_exhaustion_accelerating_iv': 'Exhaustion + accelerating IV decline',
    'high_low_modeled_event': 'High rank + modeled front event premium ≤2 pts',
    'episode_first_exit': 'First observation below high-rank threshold',
}


def completion_cells(replays: pd.DataFrame, ticker: str, day: str) -> list[str]:
    """Keep executable closures distinct from zero-bid marks and unavailable horizons."""
    subset = replays[replays.ticker.eq(ticker) & replays.tradeDate.eq(day)].set_index('horizon')
    a, b = subset.loc[4], subset.loc[5]
    if a.status == 'entry_not_admitted':
        entry = pd.Timestamp(a.entry_time).strftime('%m-%d %H:%M')
        return [f'Skipped sale: ${a.observed_entry_bid:.2f} bid at {entry}',
                f'This replay required at least $0.20 per share ($20 per contract); '
                f'the bid offered ${a.observed_entry_bid*100:.0f} per contract. '
                'Only that entry time was checked. Other entry times remain untested here.']
    if a.status == 'deadline_censored':
        return ['Second leg completed; closing outcome unavailable',
                f'Sold ${a.entry_bid:.2f}; bought nearer at ${a.leg2_ask:.2f} '
                f'on {pd.Timestamp(a.leg2_time).strftime("%m-%d %H:%M")}. '
                f'Exit {pd.Timestamp(a.deadline).strftime("%m-%d")} is beyond 09-04 cutoff.']
    if a.status in ('completed_closed', 'completed_zero_bid_long_mark'):
        wording = 'Yes, quoted closes' if a.fully_closed and b.fully_closed else \
            'Completed; short covered, long marked at zero'
        status = f'{wording}: ${a.pnl_net:+.2f} / ${b.pnl_net:+.2f} net (D4/D5)'
        reason = (f'Sold {a.short_strike:g}C ${a.entry_bid:.2f}; bought '
                  f'{a.long_strike:g}C ${a.leg2_ask:.2f} on '
                  f'{pd.Timestamp(a.leg2_time).strftime("%m-%d %H:%M")}. ')
        if not a.fully_closed:
            reason += 'No long-call closing bid; positive conservative mark is not a full close. '
        if a.expiry_shortened or b.expiry_shortened:
            reason += f'Expiry caps exit at {a.expiry[5:]}. '
        return [status, reason.strip()]
    return [f'{a.status} / {b.status}', 'See the exact-quote replay ledger.']


def chart(summary: pd.DataFrame, calls: pd.DataFrame) -> None:
    """Show the coordinate distinction and the temporal sensitivity without ranking winners."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.1), layout='constrained')
    valid = calls.age.notna() & ~calls.left_censored.fillna(True)
    points = axes[0].scatter(calls.loc[valid, 'delta']*100, calls.loc[valid, 'otm_pct'],
        c=calls.loc[valid, 'age'], cmap='viridis', s=48, alpha=.8, edgecolors='white', linewidths=.4)
    axes[0].scatter(calls.loc[~valid, 'delta']*100, calls.loc[~valid, 'otm_pct'],
        c='#aaaaaa', marker='x', label='Age unavailable / left-censored')
    for ticker, day in [('SMCI', '2026-08-13'), ('JNJ', '2026-08-24'), ('MSTR', '2026-08-20')]:
        row = calls[calls.ticker.eq(ticker) & calls.tradeDate.eq(day)].iloc[0]
        axes[0].annotate(ticker, (row.delta*100, row.otm_pct), xytext=(6, 5),
                         textcoords='offset points', fontsize=9)
    fig.colorbar(points, ax=axes[0], label='High-wing episode age (sessions)', shrink=.82)
    axes[0].set(xlabel='Call delta × 100', ylabel='Strike above spot (%)',
                title='73 recent selections: equal delta ≠ equal distance')
    axes[0].grid(alpha=.15)
    rules = ['high_rank', 'high_age6plus', 'high_rollover', 'high_exhaustion']
    positions = np.arange(len(rules))
    for i, (era, color) in enumerate([('2024–2025', '#3977a8'), ('2026', '#d17830')]):
        s = summary[(summary['mode'].eq('nonoverlap')) & summary.era.eq(era)
                    & summary.horizon.eq(2)].set_index('rule').loc[rules]
        values = s.joint_down_pct.to_numpy()
        errors = np.vstack([values-s.joint_ci_low.to_numpy(), s.joint_ci_high.to_numpy()-values])
        axes[1].bar(positions+(i-.5)*.36, values, width=.34, label=era, color=color)
        axes[1].errorbar(positions+(i-.5)*.36, values, yerr=errors, fmt='none',
                         color='#333333', capsize=3, linewidth=.8)
    axes[1].set_xticks(positions, ['High rank', 'Age 6+', 'Rollover', 'Exhaustion'])
    axes[1].set(ylabel='Spot down AND ATM IV10 down (%)', ylim=(0, 100),
                title='Two holding sessions after next-session reference')
    axes[1].legend(frameon=False)
    axes[1].grid(axis='y', alpha=.15)
    fig.suptitle('Call-skew journey research — daily surface outcomes, not option P&L', fontsize=13)
    fig.savefig(OUTPUT / 'delta_distance_and_journey.png', dpi=160)
    plt.close(fig)


def main() -> None:
    summary = pd.read_csv(OUTPUT / 'ablation_results.csv')
    adjusted = pd.read_csv(OUTPUT / 'starting_state_comparisons.csv')
    calls = pd.read_csv(OUTPUT / 'recent_73_calls_with_journey.csv')
    coverage = pd.read_csv(OUTPUT / 'coverage.csv')
    stats = json.loads((OUTPUT / 'run_summary.json').read_text())
    api = json.loads((OUTPUT / 'api_manifest.json').read_text())
    selected = summary.query("mode == 'nonoverlap' and era == 'all' and horizon == 2")
    base = selected.set_index('rule').loc['high_rank']
    rows = []
    for r in selected.itertuples():
        rate = (f'{r.joint_down_pct:.1f}% [{r.joint_ci_low:.1f}, {r.joint_ci_high:.1f}]'
                if r.valid_outcomes else 'Unavailable')
        rows.append([LABELS[r.rule], int(r.valid_outcomes), rate,
                     fmt(r.mean_return_pct, 2), fmt(r.mean_iv10_change_points, 2)])
    main_table = table(['Frozen comparison', 'Valid nonoverlapping observations',
        'Spot down + IV down: rate [month-block 95% interval]',
        'Mean spot return %', 'Mean ATM IV10 change (pts)'], rows)
    temporal_rows = []
    for rule in ['high_rank', 'high_age1_2', 'high_age3_5', 'high_age6plus',
                 'high_expanding', 'high_rollover', 'high_exhaustion',
                 'high_mature_rollover_premia_exhaustion']:
        cells = []
        for era in ['2024–2025', '2026']:
            r = summary.query("mode == 'nonoverlap' and horizon == 2")
            r = r[r.rule.eq(rule) & r.era.eq(era)].iloc[0]
            cells.append(f'{r.joint_down_pct:.1f}% (n={r.valid_outcomes:,})')
        a = adjusted[adjusted.rule.eq(rule) & adjusted.era.eq('all')]
        cells.append('Reference' if a.empty else
            f'{a.iloc[0].descriptive_difference_points:+.1f} points '
            f'(supported n={a.iloc[0].common_support:,})')
        temporal_rows.append([LABELS[rule], *cells])
    temporal = table(['Comparison', '2024–2025 joint rate', '2026 joint rate',
                      'Starting-state comparison: all daily signals'], temporal_rows)
    replays = pd.read_csv(OUTPUT / 'review_45_session_replay.csv')
    recent_rows = []
    for ticker, day in [('COIN', '2026-08-20'), ('COIN', '2026-08-21'),
        ('STX', '2026-08-24'), ('NVDA', '2026-08-26'), ('BE', '2026-08-28'),
        ('MSTR', '2026-08-20'), ('SMCI', '2026-08-13'), ('JNJ', '2026-08-24'),
        ('MRNA', '2026-08-24'), ('TSLA', '2026-09-02')]:
        r = calls[calls.ticker.eq(ticker) & calls.tradeDate.eq(day)].iloc[0]
        stage = 'rolling over' if r.rolling_over else 'expanding' if r['expanding'] else 'mixed'
        age = 'unknown' if pd.isna(r.age) or r.left_censored else f'{r.age:.0f}'
        recent_rows.append([f'{ticker} {day[5:]}',
            f'{r.delta*100:.2f}Δ / {r.otm_pct:.2f}% / {r.log_distance_atm_move_units:.2f} ATM moves',
            f'age {age}; high {r.high_days20:.0f}/20 days; {stage}; '
            f'{r.peak_minus_wing:.2f} pts below episode peak',
            f'{r.iv30d*100:.1f}/{r.rv30*100:.1f}; {r.iv60d*100:.1f}/{r.rv60*100:.1f}',
            f'{r.return_2:+.2f}% / {r.iv10_change_2:+.2f} pts'
            if pd.notna(r.joint_down_2) else 'Unavailable',
            *completion_cells(replays, ticker, day)])
    recent = table(['Signal EOD', 'Call delta / % OTM / log-distance',
                    'Front 5Δ/10D wing journey', 'IV/RV %: 30d; 60d',
                    'Observed post-reference 2-session spot / IV10',
                    'Sell first / buy cheaper, closed within 4–5 sessions?',
                    'Why / why not (ET; per contract)'], recent_rows)
    contract_requirements = (OUTPUT / 'historical_contract_requirements.md').read_text()
    missing_requirements = (OUTPUT / 'missing_data_requirements.md').read_text()
    earnings_exclusion = (OUTPUT / 'earnings_exclusion.md').read_text()
    execution_notes = (OUTPUT / 'review_execution_notes.md').read_text()
    feynman_path = OUTPUT / 'feynman_summary.md'
    feynman = feynman_path.read_text() if feynman_path.exists() else ''
    text = f'''# Delta, distance and the high-call-skew journey

**September 7 review update:** exact quotes now support the ten-example four/five-session
comparison below. Two mature cases have profitable quoted closes of both legs; three
others have positive conservative marks with a zero-bid long. All five made less than
simply covering the original short at the same deadline. The new 30-day earnings rule
is recorded below; the available dated schedules do not clear any of the 73 recent
selections, so these option replays are counterfactual, not admitted trades.

**Charlie and Brent both favor treating strike distance, richness and exhaustion as
separate questions.** A persistent high call wing can keep expanding. The research
question is whether its age and rollover add information beyond its starting level.
These were canonical persona simulations; [their decisions](persona_decisions.md)
and the [protocol frozen before outcomes](research_protocol.md) are recorded separately.

**The most useful research leads are skew age and rollover, mainly for volatility
normalization.** Age 6+ raised the joint decline rate from 23.8% to 28.6%, but spot fell
only 52% of the time and its average change was effectively zero. Two-day wing rollover
gave 27.7%, with similar point estimates in 2024–2025 and 2026; its descriptive advantage
after starting-state matching was about 2.8 percentage points. These are modest associations.

**Positive 30/60-day variance gaps alone did not improve this timing test.** The larger
combined filter also weakened in 2026: 21.4% joint declines from only 28 nonoverlapping
observations, versus 24.5% for that period's high-rank baseline. Both personas advise
against promoting that combination into an entry gate. Their post-result agreement
is to prioritize exact-quote tests of rollover versus continued expansion, retaining
delta, % OTM and normalized distance as separate coordinates.

The retrospective daily-surface study covers **{stats['observed_stocks']} stocks with
observed data**, **{stats['eligible_signal_days']:,} eligible stock-days**, and
**{stats['high_rank_signal_days']:,} high-front-wing stock-days** from January 2024
through September 3, 2026. The universe is the **September 3 HIRO membership set applied
backwards**. It is not historical HIRO membership or a claim that intraday HIRO existed
throughout. Requested stocks without usable history remain in the coverage ledger.
Collection used **{api['used']} requests** under this experiment's separate 80-attempt cap.

The primary reference result is **{base.joint_down_pct:.1f}%** spot-down **and** ATM-IV10-down,
from **{int(base.valid_outcomes):,} nonoverlapping high-rank observations**, over two holding
sessions beginning at the next-session EOD reference. This is a daily stock/surface
outcome study, **not an exact-option profit backtest**.

![Delta, distance and chronological journey comparisons]({OUTPUT / 'delta_distance_and_journey.png'})

## Combining delta and distance

Use **delta + % OTM + expiry + distance in ATM expected-move units**. For the recent
contracts, the extra coordinate is log(K/S) / (ATM IV × sqrt(DTE/365)). IV is decimal;
S is a spot approximation because a matched forward is unavailable. Rich tail IV
must not inflate its own distance denominator. These quantities do not establish
strike-touch probability or bounded loss. SMCI's 9.26Δ / 24.78% OTM and JNJ's
9.43Δ / 3.56% OTM remain economically different cases.

The longer-history surface panel uses a **constant 5Δ/10D proxy**. It cannot prove
which exact 2–10Δ and % OTM combination performs best without historical chains,
quotes and fixed contract execution rules. The [73-contract bridge](recent_73_calls_with_journey.csv)
keeps those exact-contract coordinates alongside the proxy's journey; it does not
substitute the proxy percentile for a strike-history z-score.

{contract_requirements}

## Where the high-call-skew episode stands

| Dimension | Recorded measure | Interpretation |
| --- | --- | --- |
| How extreme now? | Prior-only 252-session percentile and absolute call-wing IV minus ATM | High percentile can still mean a negative wing |
| How long? | Consecutive sessions at rank ≥85; age 1–2, 3–5, 6+ | Age bands are research choices, not Pandar rules |
| How much sustained demand? | Cumulative normalized rank excess above85 | Persistence/intensity, without assuming a reversal |
| How far from its own peak? | Highest wing known so far minus current wing, in vol points | Never uses a later realized peak |
| Still expanding or rolling over? | Two successive rises versus two successive falls in the fixed-tenor wing | Separates continued demand from observed deterioration |
| Is change accelerating? | Daily change in wing/IV slope; change in log-return momentum | Temporal acceleration, distinct from cross-strike curvature and option gamma |

Missing observations interrupt episodes. Unknown starting ages remain in the baseline
and a separate censored-age category, not the known-age comparisons. The 30D/25Δ
ex-earnings call skew and ORATS cross-strike curvature are also retained for context.
Strict episode age resets after even one below-85 observation; it is not the age of an
entire market narrative. The recent-contract bridge additionally shows the number of
high-rank days in the last 20 sessions and distance from that window's peak. Those are
descriptive additions after the primary results, not newly tested admission filters.

{missing_requirements}

## Realized versus implied volatility

Compute trailing **30 and 60 calendar-day** realized variance from split/dividend-adjusted
stock log returns: 252 × mean squared daily returns, requiring all observations in the
window. Compare it with matched IV30² and IV60². Positive spreads mean implied variance
exceeds recently realized variance; they are not guaranteed carry or forward forecasts.
The study retains modeled earnings premium separately and does not mix raw RV with
ex-earnings IV under a claim of pure diffusion premium. Weekly IV and event exposure
remain relevant even if 30/60-day comparisons look attractive.
For example, MRNA's trailing RV is heavily affected by ORATS's reported adjusted-close
move from $62.96 to $174.38 on August 19. That observation remains in raw RV; its catalyst
is not established here. The August 24 IV30/RV30 comparison of 92.5%/370.3% therefore
does not mean its particular far-OTM call was cheaply offered. A past jump can dominate
trailing RV after the options market has already repriced future volatility.
The weak result for the simple positive-gap rule does not test or reject every
realized-volatility forecasting model or earnings-adjusted comparison.

{earnings_exclusion}

ORATS distinguishes 30/60-calendar-day implied vol, daily adjusted stock prices, and
cross-strike curvature in its [field definitions](https://orats.com/docs/definitions).
The summary endpoint's confidence fraction is converted to percent before applying
the confidence gate. Eight timing, missing-data, unit and column-selection tests pass;
no future price or volatility value enters the signal features.

## Frozen two-session comparisons

EOD features on t authorize a next-session EOD reference on t+1. Outcomes below run
from that reference to t+3. Nonoverlap is chosen separately per rule using the maximum
three-session holding horizon, so rules can enter on different dates. The intervals
resample calendar months of the full cross section and do not make observations
independent trades. The complete CSV also reports all daily signals, 1/3-session
horizons, missing outcomes, component hit rates and signal-to-entry drift.

{main_table}

Price/IV exhaustion means preceding three-session strength, slowing daily stock returns,
and falling IV10. Accelerating-IV sensitivity additionally requires IV's daily slope to
become more negative. The combined hypothesis requires known age ≥3, wing rollover,
both positive variance premia and that exhaustion condition. **No weights or thresholds
were optimized on observed winners.**

## Chronological and starting-state checks

{temporal}

The final column compares each group with other high-rank daily observations in the
same fixed calendar-quarter, starting-rank, absolute-wing, ATM-IV and modeled-event
premium cell, requiring at least five controls. It uses common-support observations
and is a descriptive percentage-point difference, not a causal or tradable edge.
These are all-signal comparisons; their sample sizes differ from the nonoverlap columns.
Current-universe selection, residual confounding and multiple comparisons remain.
The later 2026 slice is not a pristine untouched holdout.

## What the recent calls looked like along that journey

These are selected examples fixed before reading their outcome rows, including both
HIRO-covered and uncovered cases. The original stock/IV column uses a next-session EOD
reference. The two added columns use **exact option quotes with a next-session 10:01
clock entry**, not that EOD reference or a HIRO trigger. The journey belongs to the fixed
5Δ/10D surface proxy; delta and distance are signal-date coordinates, not entry Greeks.

**Why four rows say “skipped sale”:** this comparison checked one possible sale time,
10:01 ET on the next trading day, and required at least $0.20 per share ($20 for one
standard contract). At that minute, NVDA and SMCI offered $15 per contract, BE offered
$5, and JNJ offered $4. The replay therefore left those trades unopened. The clock time
and minimum premium are project assumptions used to make this one comparison consistent;
they are not Pandar's requirements. Those rows do not tell us whether selling on the
signal day, waiting until later, or following HIRO could have produced a good trade.

For the added test, sell the preselected far call at the next-session 10:01 bid >=$0.20;
buy the fixed nearer call at the first subsequent valid minute ask that leaves $0.10
gross credit. Close at 15:50 on session 4 or 5, counting entry as session 1, or expiry
if sooner. Dollar results include $2.60 round-trip fees per one-contract spread. Buying
the nearer call completes the spread; it does not close it. This project conversion
and the fixed bid/credit/time rules are not universal Pandar requirements.

{recent}

{execution_notes}

The full CSV includes all 73 selections, both original delta/OTM coordinates and current
surface-stage inputs, plus the previously verified HIRO capture status. It retains
unavailable outcomes. A fading stock price with rising IV is a separate adverse-vol
regime; it must not be mistaken for a call-wing crush or successful nearer-call purchase.
The refreshed histories reproduce 70 of the 73 original front-wing ranks exactly;
the other three differ by 0.397 percentile points, equivalent to one prior observation
out of 252, with no change to the 85 threshold classification. The original ranks remain
visible alongside the new computed ranks in the [reconciliation](recent_rank_reconciliation.csv).

## Artifacts and limits

- [Review protocol](review_followup_protocol.md), [exact four/five-session replay](review_45_session_replay.csv),
  [quote provenance](review_quote_manifest.json), [earnings audit](review_earnings_73.csv),
  [earnings source dates/hashes](review_earnings_sources.json), and [Feynman-style review](feynman_review.md).
- [Protocol](research_protocol.md), [persona decisions](persona_decisions.md),
  [full fixed-comparison results](ablation_results.csv), and
  [starting-state comparisons](starting_state_comparisons.csv).
- [All daily features/outcomes](daily_features_and_outcomes.parquet),
  [high-rank and first-exit ledger](high_rank_signal_ledger.csv),
  [73 exact-call coordinate/journey rows](recent_73_calls_with_journey.csv), and
  [delta versus % OTM counts](delta_otm_counts.csv).
- [Requested-stock coverage](coverage.csv), [source hashes](data_sources.csv),
  [frozen membership](hiro_universe.csv), and [request ledger](api_manifest.json).

This tests some of the user's proposed predictors across historical HIRO ticker names.
It does not establish an optimal delta/OTM band, an intraday HIRO edge or optimal
second-leg timing. Exact-price examples now exist for the ten selected rows, under the
specific clock rule and unresolved earnings admission above; they do not validate the
strategy across the historical universe. The earlier HIRO-based MSTR replay remains
separate. The fixed reference/entry times, selection bias and small sample prevent
interpreting these examples as a portfolio return or a fitted profitable trading rule.

{feynman}
'''
    (OUTPUT / 'pandar_skew_journey_research.md').write_text(text)
    chart(summary, calls)
    print('Published', OUTPUT / 'pandar_skew_journey_research.md')
    print('Coverage status', coverage.status.value_counts().to_dict())


if __name__ == '__main__':
    main()
