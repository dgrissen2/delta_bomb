"""Loader for the NVDA 1-min greeks store (Delta Bomb study)."""
from __future__ import annotations
import glob, os
import pandas as pd
ROOT = os.path.expanduser("~/Dev/central_trade_data/thetadata/nvda_delta_bomb_1m_2026-08-17-v1/greeks")
COLS = ["symbol","expiration","strike","right","timestamp","bid","ask","delta","theta","vega","rho","epsilon","lambda","implied_vol","iv_error","underlying_timestamp","underlying_price"]

def load(exp: str, date: str) -> pd.DataFrame:
    f = f"{ROOT}/NVDA_{exp.replace('-','')}_{date}.parquet"
    g = pd.read_parquet(f)
    g.columns = COLS[:len(g.columns)]
    g["timestamp"] = pd.to_datetime(g["timestamp"], utc=True).dt.tz_convert("America/New_York")
    g["t"] = g.timestamp.dt.strftime("%H:%M")
    g = g[(g.bid > 0) & (g.ask > 0)].copy()
    return g

def q(g, t, k, right):
    r = g[(g.t == t) & (g.strike == k) & (g.right == right)]
    return None if r.empty else r.iloc[0]
