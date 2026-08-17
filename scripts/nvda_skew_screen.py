"""NVDA daily vol-surface screen for buy-first / sell-first call bombs, from local ORATS history.

Conventions (equity/ORATS, NOT FX):
  ORATS dltXX = IV at XX CALL delta -> dlt5 = 5d call, dlt25 = 25d call, dlt75 = 25d put, dlt95 = 5d put.
  RR25       = 25d put IV - 25d call IV = dlt75Iv30d - dlt25Iv30d   (>0 normal; HIGH rank = calls cheap vs puts = buy-first zone)
  callskew   = 25d call IV - ATM IV      = dlt25Iv30d - iv30d
  c5_30      = 5d call IV - ATM (30d)    = dlt5Iv30d - iv30d
  c5_10      = 5d call IV - ATM (10d)    = dlt5Iv10d - iv10d          (front-weekly far wing: the SELL-first tell)
  c5_kink    = dlt5Iv10d - dlt5Iv30d                                    (front vs 30d far-call wing kink)
  ivRank1y / ivPct1y straight from ORATS ivrank history.
Ranks: rolling 252-trading-day percentile (share of prior 252 days below today) on ex-earnings series where available; z-score also stored.
"""
from __future__ import annotations
import pandas as pd
BASE = '/Users/dgrissen/Dev/central_trade_data/oos_validation_v4_b3/'
OUT = '/Users/dgrissen/Dev/delta_bomb/docs/replay/nvda_skew_daily.parquet'

def pct252(s): return s.rolling(252, min_periods=126).apply(lambda w: (w[:-1] < w[-1]).mean() * 100, raw=True)
def z252(s): return (s - s.rolling(252, min_periods=126).mean()) / s.rolling(252, min_periods=126).std()

def build(ticker='NVDA'):
    c = pd.read_parquet(f'{BASE}cores_full_history/{ticker}.parquet'); r = pd.read_parquet(f'{BASE}ivrank_full_history/{ticker}.parquet')
    c['tradeDate'] = pd.to_datetime(c.tradeDate); r['tradeDate'] = pd.to_datetime(r.tradeDate)
    d = c.merge(r[['tradeDate', 'ivRank1y', 'ivPct1y', 'ivRank1m', 'ivPct1m']], on='tradeDate', how='left').sort_values('tradeDate').set_index('tradeDate')
    d = d[d.iv30d < 200]  # drop corrupt ticks (e.g. 2025-04-04 = 381%)
    d['rr25'] = d.exErnDlt75Iv30d - d.exErnDlt25Iv30d
    d['callskew'] = d.exErnDlt25Iv30d - d.exErnIv30d
    d['putskew'] = d.exErnDlt75Iv30d - d.exErnIv30d
    d['c5_30'] = d.dlt5Iv30d - d.iv30d
    d['c5_10'] = d.dlt5Iv10d - d.iv10d
    d['p5_10'] = d.dlt95Iv10d - d.iv10d
    d['c5_kink'] = d.dlt5Iv10d - d.dlt5Iv30d
    for col in ['rr25', 'callskew', 'putskew', 'c5_30', 'c5_10', 'p5_10', 'c5_kink', 'iv30d', 'iv10d', 'exErnIv30d']:
        d[col + '_pct'] = pct252(d[col]); d[col + '_z'] = z252(d[col])
    # tiers for BUY-FIRST call bomb (vol-surface part only; technicals joined elsewhere)
    def tier(row):
        if row.ivRank1y <= 25 and row.rr25_pct >= 90 and row.callskew_pct <= 10 and row.c5_30 <= 1: return 'best'
        if row.ivRank1y <= 35 and row.rr25_pct >= 80 and row.callskew_pct <= 25 and row.c5_30 <= 2: return 'better'
        if row.ivRank1y <= 50 and row.rr25_pct >= 60 and row.callskew_pct <= 40 and row.c5_30 <= 3: return 'good'
        return ''
    d['buyfirst_tier'] = d.apply(tier, axis=1)
    d['sellfirst_wing'] = ((d.c5_10_pct >= 85) & (d.c5_kink_pct >= 70)).map({True: 'sell-first tell', False: ''})
    return d

if __name__ == '__main__':
    d = build(); d.to_parquet(OUT)
    cols = ['iv30d', 'ivRank1y', 'ivPct1y', 'rr25', 'rr25_pct', 'callskew', 'callskew_pct', 'c5_30', 'c5_10', 'c5_10_pct', 'c5_kink_pct', 'buyfirst_tier', 'sellfirst_wing']
    print(d[cols].tail(3).round(2).to_string())
    print(d.loc['2024-06':, 'buyfirst_tier'].value_counts())
    print(d.loc[['2025-01-31', '2025-02-24', '2025-03-20', '2025-08-04'], cols].round(1).to_string())
