"""Fetch NVDA 1-min option greeks (bid/ask/delta/IV/underlying) for the Delta Bomb study.

Source: local ThetaData terminal v3 via the python SDK, `option_history_greeks_first_order`
(https://docs.thetadata.us/operations_python/option_history_greeks_first_order.html).
Layout: ~/Dev/central_trade_data/thetadata/nvda_delta_bomb_1m_2026-08-17-v1/greeks/NVDA_<exp>_<date>.parquet
        one file per (expiration, session), all strikes, both rights, 09:30-16:00 ET, interval 1m.
Idempotent: skips existing non-empty files. Writes manifest.json.
"""
from __future__ import annotations
import datetime as dt, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from thetadata import ThetaClient

ROOT = os.path.expanduser("~/Dev/central_trade_data/thetadata/nvda_delta_bomb_1m_2026-08-17-v1")
CREDS = os.path.expanduser("~/Dev/ThetaData/creds.txt")
SYMBOL = "NVDA"
EXPS = [dt.date(2026, 8, 21), dt.date(2026, 9, 18)]
DATES = [dt.date(2026, 8, d) for d in (3, 4, 5, 6, 7, 10, 11, 12, 13, 14)]

def one(exp, day, workers_client):
    out = f"{ROOT}/greeks/{SYMBOL}_{exp:%Y%m%d}_{day:%Y-%m-%d}.parquet"
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return out, "cached", 0
    for attempt in range(4):
        try:
            t0 = time.time()
            r = workers_client.option_history_greeks_first_order(symbol=SYMBOL, expiration=exp, interval="1m", date=day, strike="*", right="both", start_time="09:30:00", end_time="16:00:00")
            df = r.to_pandas() if hasattr(r, "to_pandas") else pd.DataFrame(r)
            if df is None or len(df) == 0:
                return out, "nodata", 0
            df.to_parquet(out, index=False)
            return out, f"ok {len(df)} rows {time.time()-t0:.0f}s", len(df)
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {e}"
            if "no data" in msg.lower() or "nodata" in msg.lower():
                return out, "nodata", 0
            time.sleep(5 * 2 ** attempt)
            last = msg
    return out, f"error {last[:200]}", 0

if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    client = ThetaClient(creds_file=CREDS)
    tasks = [(e, d) for e in EXPS for d in DATES]
    log = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(one, e, d, client): (e, d) for e, d in tasks}
        for f in as_completed(futs):
            e, d = futs[f]; out, status, n = f.result()
            print(f"{e} {d} {status}", flush=True); log.append(dict(exp=str(e), date=str(d), file=os.path.basename(out), status=status, rows=n))
    man = dict(created="2026-08-17", symbol=SYMBOL, source="ThetaData v3 terminal, python SDK option_history_greeks_first_order, interval=1m, strike=*, right=both, 09:30-16:00 ET",
               expirations=[str(e) for e in EXPS], sessions=[str(d) for d in DATES], files=log,
               columns="symbol, expiration, strike, right, timestamp(ET), bid, ask, delta, theta, vega, rho, epsilon, lambda, implied_vol, iv_error, underlying_timestamp, underlying_price",
               purpose="Delta Bomb study (~/Dev/delta_bomb): NVDA intraday leg-in replay, put and call side, front monthly + ~30-45 DTE monthly")
    json.dump(man, open(f"{ROOT}/manifest.json", "w"), indent=1)
