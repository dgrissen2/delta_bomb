"""Fetch NVDA 1-min greeks for (expiration, session-range) pairs into the Delta Bomb store. Idempotent."""
from __future__ import annotations
import datetime as dt, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from thetadata import ThetaClient
ROOT = os.path.expanduser("~/Dev/central_trade_data/thetadata/nvda_delta_bomb_1m_2026-08-17-v1")
c = ThetaClient(creds_file=os.path.expanduser("~/Dev/ThetaData/creds.txt"))
def sessions(a, b):
    return [d.date() for d in pd.bdate_range(a, b) if d.date() not in {dt.date(2026,5,25), dt.date(2026,6,19), dt.date(2026,7,3)}]
PLAN = [("2026-06-18", sessions("2026-05-04", "2026-06-18")), ("2026-07-17", sessions("2026-05-18", "2026-07-17")),
        ("2026-08-21", sessions("2026-06-22", "2026-07-31")), ("2026-09-18", sessions("2026-07-20", "2026-07-24")),
        ("2026-05-29", sessions("2026-05-11", "2026-05-29")), ("2026-06-05", sessions("2026-05-18", "2026-06-05"))]
def one(exp, day):
    e = dt.date.fromisoformat(exp); out = f"{ROOT}/greeks/NVDA_{e:%Y%m%d}_{day:%Y-%m-%d}.parquet"
    if os.path.exists(out) and os.path.getsize(out) > 0: return exp, day, "cached", 0
    last = ""
    for a in range(4):
        try:
            r = c.option_history_greeks_first_order(symbol="NVDA", expiration=e, interval="1m", date=day, strike="*", right="both", start_time="09:30:00", end_time="16:00:00")
            df = r.to_pandas() if hasattr(r, "to_pandas") else pd.DataFrame(r)
            if df is None or len(df) == 0: return exp, day, "nodata", 0
            df.to_parquet(out, index=False); return exp, day, "ok", len(df)
        except Exception as ex:  # noqa: BLE001
            last = str(ex)
            if "no data" in last.lower(): return exp, day, "nodata", 0
            time.sleep(5 * 2 ** a)
    return exp, day, "error " + last[:120], 0
if __name__ == "__main__":
    tasks = [(e, d) for e, ds in PLAN for d in ds]; print(len(tasks), "tasks", flush=True); log = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in as_completed([ex.submit(one, e, d) for e, d in tasks]):
            e, d, s, n = f.result(); log.append(dict(exp=e, date=str(d), status=s, rows=n))
            if s != "cached": print(e, d, s, n, flush=True)
    m = json.load(open(f"{ROOT}/manifest.json")); m["files"] += [x for x in log if x["status"] != "cached"]
    m["expirations"] = sorted(set(m["expirations"] + [e for e, _ in PLAN])); m["sessions"] = sorted(set(m["sessions"] + [x["date"] for x in log]))
    m["note_2026-08-17c"] = "May-Aug 2026 cycle study: Jun-18/Jul-17/Aug-21 monthlies + May-29/Jun-05 weeklies + Sep-18 Jul 20-24 (%d calls)" % sum(1 for x in log if x["status"] != "cached")
    json.dump(m, open(f"{ROOT}/manifest.json", "w"), indent=1)
    print("done", sum(1 for x in log if x["status"].startswith("ok")), "ok;", sum(1 for x in log if x["status"].startswith("error")), "errors")
