"""Render evidence charts and compact comparison tables for Pandar leg timing."""

from __future__ import annotations

import os
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/pandar_matplotlib')
os.environ.setdefault('XDG_CACHE_HOME', '/private/tmp/pandar_xdg_cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pandar_quote_history import OUTPUT, SOURCE
from pandar_leg_timing import quotes, at, shift, initial_prices, simulate


def chart(row: pd.Series, hiro: pd.DataFrame) -> None:
    """Show stock, decomposed flow and exact option quotes with causal execution markers."""
    opened, completed, exited = map(pd.Timestamp, (row.entry_time, row.leg2_time, row.exit_time))
    first = quotes(row.ticker, row.expiry, row.leg1_strike, 'call')
    second = quotes(row.ticker, row.expiry, row.leg2_strike, 'call')
    times = first.index[(first.index >= at(opened.strftime('%Y-%m-%d'), '09:30'))
                        & (first.index <= exited)]
    x = pd.Series(np.arange(len(times)), index=times)
    flow = hiro[hiro.ticker.eq(row.ticker)].set_index('timestamp').reindex(times)
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True,
                              gridspec_kw={'height_ratios': [1, 1.1, 1.25]})
    axes[0].plot(x, flow.stock_price, color='#15314b', lw=1.5)
    axes[0].set_ylabel('MSTR stock ($)')
    for side, color in [('call', '#ba6031'), ('put', '#246a9a')]:
        axes[1].plot(x, flow[f'{side}15'] / 1e6, color=color, label=f'{side.title()} HIRO, 15m')
    axes[1].axhline(0, color='#888888', lw=.7)
    axes[1].set_ylabel('All Trades pressure ($mn)')
    axes[1].legend(loc='upper left', frameon=False, ncol=2)
    axes[2].plot(x, first.reindex(times).bid, color='#993553',
                 label=f'{row.leg1_strike:g}C sale bid')
    axes[2].plot(x, second.reindex(times).ask, color='#277c67',
                 label=f'{row.leg2_strike:g}C purchase ask')
    axes[2].axhline(row.leg1_price - .026, color='#555555', linestyle=':',
                   label='Entry proceeds less all four fees')
    axes[2].set_ylabel('Option premium ($/share)')
    axes[2].legend(loc='upper right', frameon=False)
    markers = [(opened, '#993553', f'Sell {row.leg1_strike:g}C\n{opened:%m/%d %H:%M}'),
               (completed, '#277c67', f'Buy {row.leg2_strike:g}C\n{completed:%m/%d %H:%M}'),
               (exited, '#555555', f'Exit\n{exited:%m/%d %H:%M}')]
    for timestamp, color, label in markers:
        for ax in axes:
            ax.axvline(x.loc[timestamp], color=color, linestyle='--', lw=1, alpha=.8)
        axes[0].annotate(label, (x.loc[timestamp], 1), xycoords=('data', 'axes fraction'),
                         xytext=(0, 5), textcoords='offset points', ha='right' if timestamp == exited
                         else 'left', va='bottom', color=color, fontsize=9)
    starts = [i for i, t in enumerate(times) if i == 0 or t.date() != times[i-1].date()]
    axes[2].set_xticks(starts)
    axes[2].set_xticklabels([times[i].strftime('%a %m/%d\n09:30 ET') for i in starts])
    for ax in axes:
        for i in starts[1:]:
            ax.axvline(i, color='#cccccc', lw=.6)
        ax.grid(axis='y', color='#eeeeee')
        ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle(f'MSTR {row.expiry} {row.leg2_strike:g}/{row.leg1_strike:g} calls'
                 f'  |  HIRO completion replay: +${row.pnl_net:.2f} per unit',
                 fontsize=16, fontweight='bold', y=.99)
    fig.text(.5, .01, 'One-contract bid/ask replay, $0.65 per transaction. '
             'HIRO uses prior-minute information. Overnight gaps compressed; fills unverified.',
             ha='center', fontsize=9, color='#555555')
    fig.tight_layout(rect=[0, .03, 1, .96])
    fig.savefig(OUTPUT / f'MSTR_{row.leg2_strike:g}_{row.leg1_strike:g}_timeline.png', dpi=160)
    plt.close(fig)


def main() -> None:
    attempts = pd.read_csv(OUTPUT / 'all_attempts.csv')
    hiro = pd.read_parquet(OUTPUT / 'data/hiro_minutes.parquet')
    call = attempts.query('scenario == "sell-first call grab" and entry_mode == "hiro"')
    comparison = call.query('method in ["simultaneous", "fixed_clock", "price_finance", "hiro_finance"]')
    comparison[['tradeDate', 'leg1_strike', 'leg2_strike', 'entry_time', 'leg1_price', 'method',
                'horizon', 'status', 'leg2_time', 'leg2_price', 'exit_time', 'pnl_net',
                'pnl_extra_1c_slippage', 'first_leg_min_pnl',
                'completion_benefit_vs_close']].to_csv(OUTPUT / 'call_timing_comparison.csv', index=False)
    selected = call.query('method == "hiro_finance" and horizon == 1')
    selected.to_csv(OUTPUT / 'profitable_hiro_cases.csv', index=False)
    for _, row in selected.iterrows():
        chart(row, hiro)
    paired = attempts.query('method == "standalone" and primary_episode').pivot(
        index=['row_id', 'ticker', 'scenario'], columns='entry_mode', values='pnl_net').dropna()
    paired['hiro_minus_clock'] = paired.hiro - paired.clock
    paired.to_csv(OUTPUT / 'paired_entry_comparison.csv')
    labels = ['Immediate', 'Same day\n15:50', 'Next session\n15:50', '+2 sessions\n15:50',
              'Price gate\nwithin +1', 'HIRO + price\nwithin +1']
    selections = [('simultaneous', -1), ('fixed_clock', 0), ('fixed_clock', 1),
                  ('fixed_clock', 2), ('price_finance', 1), ('hiro_finance', 1)]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for index, (day, rows) in enumerate(call.groupby('tradeDate')):
        values = [rows[(rows.method == method) & (rows.horizon == horizon)].pnl_net.iloc[0]
                  for method, horizon in selections]
        bars = ax.bar(np.arange(6) + (index - .5)*.36, values, width=.35,
                      color=['#2b758a', '#b9783b'][index],
                      label=f'{rows.leg2_strike.iloc[0]:g}/{rows.leg1_strike.iloc[0]:g}C')
        ax.bar_label(bars, labels=[f'${v:.2f}' for v in values], padding=3, fontsize=9)
    ax.axhline(0, color='#777777', linewidth=.8)
    ax.set_xticks(np.arange(6), labels)
    ax.set_ylabel('Net modeled P&L per one-contract unit ($)')
    ax.set_ylim(-42, 22)
    ax.set_title('Waiting for the nearer call to cheapen helped these two cases', fontsize=15, pad=16)
    ax.legend(frameon=False, ncol=2, loc='lower right')
    ax.spines[['top', 'right']].set_visible(False)
    fig.text(.5, .01, 'Same first leg and common exit within each case. Includes $2.60 round-trip fees. '
             'Two correlated MSTR examples; no optimal-delay or HIRO-edge claim.', ha='center', fontsize=9)
    fig.tight_layout(rect=[0,.05,1,1])
    fig.savefig(OUTPUT / 'call_timing_comparison.png', dpi=160)
    plt.close(fig)
    eligibility = []
    for _, row in pd.read_csv(SOURCE / 'pandar_approved_exact_confirmations.csv').iterrows():
        day = shift(row.tradeDate, 1)
        is_put = row.scenario.startswith('buy-first')
        right = 'put' if is_put else 'call'
        first = quotes(row.ticker, row.expiry, row.leg1_strike, right)
        second = quotes(row.ticker, row.expiry, row.leg2_strike, right)
        flow = hiro[hiro.ticker.eq(row.ticker) & hiro.session_date.eq(day)].set_index('timestamp')
        gate = 'calm_put' if is_put else 'call_exhaustion'
        clocks = pd.date_range(at(day, '10:00'), at(day, '14:30'), freq='5min')
        flow_times = [t for t in clocks if t in flow.index and flow.loc[t, gate]]
        priced = [t for t in clocks if initial_prices(row, first, second,
                                                      t + pd.Timedelta(minutes=1)) is not None]
        admitted = sorted(set(flow_times) & set(priced))
        status = ('admitted' if admitted else 'hiro_unavailable' if flow.empty else
                  'no_flow_trigger' if not flow_times else 'no_live_quote_gate_at_flow_trigger')
        eligibility.append(dict(ticker=row.ticker, tradeDate=row.tradeDate, scenario=row.scenario,
                                 entry_day=day, flow_triggers=len(flow_times),
                                 live_quote_passes=len(priced), admitted_triggers=len(admitted),
                                 hiro_status=status))
    pd.DataFrame(eligibility).to_csv(OUTPUT / 'entry_eligibility_audit.csv', index=False)
    # Separately labelled source-rule sensitivity; does not replace the frozen primary result.
    history = {(ticker, day): frame.set_index('timestamp') for (ticker, day), frame
               in hiro.groupby(['ticker', 'session_date'])}
    source = pd.read_csv(SOURCE / 'pandar_approved_exact_confirmations.csv')
    source_target = []
    for _, chosen in selected.iterrows():
        row = source[source.ticker.eq(chosen.ticker) & source.tradeDate.eq(chosen.tradeDate)].iloc[0]
        opened = pd.Timestamp(chosen.entry_time)
        first = quotes(row.ticker, row.expiry, row.leg1_strike, 'call')
        second = quotes(row.ticker, row.expiry, row.leg2_strike, 'call')
        entry = (opened, chosen.leg1_price, second.loc[opened, 'ask'], first, second)
        for method in ('price_finance', 'hiro_finance'):
            for horizon in (0, 1, 2):
                result = simulate(row, entry, history, method, horizon, financing_target=.10)
                source_target.append(dict(ticker=row.ticker, tradeDate=row.tradeDate,
                                           leg1_strike=row.leg1_strike, leg2_strike=row.leg2_strike,
                                           target_credit=.10, **result))
    pd.DataFrame(source_target).to_csv(OUTPUT / 'source_dime_target_sensitivity.csv', index=False)


if __name__ == '__main__':
    main()
