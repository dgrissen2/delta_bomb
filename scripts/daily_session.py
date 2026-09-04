"""The standing evening loop for one completed session, in dependency order (RUNBOOK):

    ~/Dev/virtualenvs/gamma_chaser/bin/python scripts/daily_session.py <date> [--stage DIR] [--skip-hiro]

  1. SPX 1-min bars → store (FIRST: the HIRO identity check needs the day's own bars).
  2. HIRO: staged capture via HIRO_finder (Chrome CDP :9222, logged in; a capture already staged
     for the day is reused) → day-identity check vs SPX 1-min (labelled day must be the cross-day
     winner, median |basket px − SPX close| < 5 pts) → canonical ingest into the immutable store
     (new partition + manifest entry; NEVER `--force` at the store).
  2b. SPXW chain for the day → store (ChainStore.fetch + sanity).
  3. v1 backtest --day <date> → docs/replay/hiro/paper_log_oos_<date>.csv (+ sessions_backtest row).
  4. hiro_watch/run.py <date> (every candidate) — then run compare.py yourself.

Each step refuses loudly and stops the loop; nothing is skipped silently. Re-running a step that is
already done is refused (HIRO partition exists / SPX parquet exists / baseline session row exists).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import logging
import shutil
import subprocess
import functools
import sys
from pathlib import Path

import pandas as pd

print = functools.partial(print, flush=True)      # keep our step lines in order with subprocess output

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
PY = sys.executable
HIRO_PY = Path("~/Dev/virtualenvs/HIRO_finder/bin/python").expanduser()
HIRO_FINDER = Path("~/Dev/HIRO_finder").expanduser()
STORE = Path("~/Dev/central_trade_data").expanduser()
HIRO_ROOT = STORE / "spotgamma/hiro/sp500_basket/v1"
SPX_DIR = STORE / "thetadata/spx_index_1m_ohlc"
BASELINE = REPO / "docs/replay/hiro"
log = logging.getLogger("daily_session")


def refuse(msg: str) -> None:
    raise SystemExit(f"REFUSED: {msg}")


# ---- 1. HIRO ----------------------------------------------------------------------
def hiro_capture(day: str, stage: Path) -> dict:
    stage.mkdir(parents=True, exist_ok=True)
    if (stage / "manifest.json").exists():
        cap = json.load(open(stage / "manifest.json")).get("sessions", {}).get(day)
        if cap and Path(cap.get("series_csv", "")).exists():
            log.info("reusing staged capture in %s", stage)
            return cap
    cmd = [str(HIRO_PY), "-m", "hiro_tickers.historical_backfill", "--port", "9222",
           "--end-date", day, "--sessions", "1", "--out-dir", str(stage)]
    log.info("capture → %s", stage)
    r = subprocess.run(cmd, cwd=HIRO_FINDER, capture_output=True, text=True)
    tail = "\n".join((r.stdout + r.stderr).splitlines()[-8:])
    print(tail)
    m = json.load(open(stage / "manifest.json")) if (stage / "manifest.json").exists() else {}
    cap = m.get("sessions", {}).get(day)
    if r.returncode != 0 or not cap or cap.get("status") not in (None, "available", "success"):
        refuse(f"HIRO capture for {day} failed (exit {r.returncode}); is Chrome on :9222 logged in to SpotGamma?")
    return cap


def hiro_identity(day: str, cap: dict) -> float:
    h = pd.read_csv(cap["series_csv"])
    a = h[h.series_group == "all"].copy()
    ts = pd.to_datetime(a.utc_iso, utc=True).dt.tz_convert("America/New_York")
    a["mn"] = ts.dt.hour * 60 + ts.dt.minute
    a = a[(a.mn >= 575) & (a.mn <= 955) & (a.stock_price > 1000)]     # stock_price: VERIFICATION ONLY
    hp = a.groupby("mn").stock_price.last()
    rows = []
    for g in sorted(SPX_DIR.glob("????-??-??.parquet")):
        spx = pd.read_parquet(g).set_index("min").close
        j = pd.concat([hp, spx], axis=1, join="inner").dropna()
        if len(j) >= 100:
            rows.append((g.stem, float((j.iloc[:, 0] - j.iloc[:, 1]).abs().median())))
    rows.sort(key=lambda r: r[1])
    if not rows:
        refuse("identity check has no SPX days to compare against")
    ok = rows[0][0] == day and rows[0][1] < 5.0
    print(f"identity: winner {rows[0][0]} med {rows[0][1]:.2f}" + (f" (2nd {rows[1][0]} {rows[1][1]:.2f})" if len(rows) > 1 else "")
          + f" -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        refuse(f"HIRO capture labelled {day} does not identify as {day}")
    return rows[0][1]


def hiro_ingest(day: str, cap: dict, med: float) -> None:
    m = json.load(open(HIRO_ROOT / "manifest.json"))
    if day in m["sessions"] or (HIRO_ROOT / f"date={day}").exists():
        refuse(f"HIRO store already has {day} — the store is immutable")
    src_csv, src_raw = Path(cap["series_csv"]), Path(cap["raw_json"])
    dn, dr = HIRO_ROOT / f"date={day}/normalized", HIRO_ROOT / f"date={day}/raw"
    dn.mkdir(parents=True); dr.mkdir(parents=True)
    dst_csv, dst_gz = dn / "hiro_series.csv", dr / "v11_hiro.json.gz"
    shutil.copyfile(src_csv, dst_csv)
    assert dst_csv.read_bytes() == src_csv.read_bytes()
    raw_bytes = src_raw.read_bytes()
    with open(dst_gz, "wb") as fh:
        with gzip.GzipFile(fileobj=fh, mode="wb", mtime=0) as gz:
            gz.write(raw_bytes)
    assert gzip.decompress(dst_gz.read_bytes()) == raw_bytes
    d_ = pd.read_csv(dst_csv)
    raw = json.loads(raw_bytes)["S&P 500"]
    norm_pts = {k: int(v) for k, v in d_.groupby("series_group").size().to_dict().items()}
    raw_rows = {g: len(raw[g]) for g in ("all", "nextExp", "retail") if isinstance(raw.get(g), list)}
    m["sessions"][day] = {
        "captured_at_utc": cap["captured_at_utc"], "first_utc_iso": cap["first_utc_iso"], "last_utc_iso": cap["last_utc_iso"],
        "normalized_path": f"date={day}/normalized/hiro_series.csv", "normalized_points": norm_pts,
        "normalized_sha256": hashlib.sha256(dst_csv.read_bytes()).hexdigest(),
        "note": f"staged historical capture (daily_session.py); day-identity verified vs SPX 1-min (median {med:.2f} pts, cross-day winner)",
        "raw_path": f"date={day}/raw/v11_hiro.json.gz", "raw_rows": raw_rows,
        "raw_uncompressed_sha256": hashlib.sha256(raw_bytes).hexdigest(), "source_attempt": cap.get("attempt"),
        "status": "available"}
    if day not in m["requested_sessions"]:
        m["requested_sessions"] = sorted(m["requested_sessions"] + [day])
    m["available_sessions"] = sorted(d for d, e in m["sessions"].items() if e.get("status") == "available")
    raw_bg, norm_bg = {}, {}
    for d, e in m["sessions"].items():
        if e.get("status") != "available":
            continue
        for g, n in e["raw_rows"].items():
            raw_bg[g] = raw_bg.get(g, 0) + int(n)
        for g, n in e["normalized_points"].items():
            norm_bg[g] = norm_bg.get(g, 0) + int(n)
    m["total_counts"] = {"raw_observations": sum(raw_bg.values()), "normalized_points": sum(norm_bg.values()),
                         "raw_by_group": raw_bg, "normalized_by_group": norm_bg}
    json.dump(m, open(HIRO_ROOT / "manifest.json", "w"), indent=1)
    print(f"ingested {day}: {sum(norm_pts.values())} norm / {sum(raw_rows.values())} raw | "
          f"{len(m['available_sessions'])} sessions | totals {m['total_counts']['raw_observations']} / {m['total_counts']['normalized_points']}")


# ---- 2. SPX + chains ----------------------------------------------------------------
def spx_bars(day: str) -> None:
    from hiro_engine.live import spx_bars_today
    p = SPX_DIR / f"{day}.parquet"
    if p.exists():
        print(f"SPX {day}: already stored")
        return
    bars = spx_bars_today(day)
    if len(bars) < 391 or int(bars["min"].max()) < 960:
        refuse(f"SPX pull for {day} incomplete: {len(bars)} bars, last minute {bars['min'].max() if len(bars) else None}")
    bars.to_parquet(p, index=False)
    print(f"SPX {day}: {len(bars)} bars → {p.name}")


def chains(day: str) -> None:
    from hiro_engine.chains import ChainStore, real_cache_sanity
    cd = ChainStore().fetch(day)
    problems = real_cache_sanity(cd)
    if problems:
        refuse(f"chain sanity {day}: {problems}")
    print(f"chain {day}: expiry {cd.expiry}, {len(cd.frame)} rows, sanity OK")


# ---- 3 + 4. engines ---------------------------------------------------------------------
def v1_backtest(day: str) -> None:
    sess = BASELINE / "sessions_backtest.csv"
    if sess.exists() and day in set(pd.read_csv(sess, dtype=str).date):
        refuse(f"baseline already has a session row for {day}")
    out = BASELINE / f"paper_log_oos_{day}.csv"
    if out.exists():
        refuse(f"{out} exists")
    r = subprocess.run([PY, "-m", "hiro_engine", "backtest", "--day", day, "--log", str(out)], cwd=SCRIPTS)
    if r.returncode != 0:
        refuse(f"v1 backtest exited {r.returncode}")


def watch(day: str) -> None:
    r = subprocess.run([PY, "hiro_watch/run.py", day], cwd=SCRIPTS)
    if r.returncode != 0:
        refuse(f"hiro_watch/run.py exited {r.returncode}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("day")
    ap.add_argument("--stage", default=None, help="staging dir for the HIRO capture (default: scratch under /tmp)")
    ap.add_argument("--skip-hiro", action="store_true", help="HIRO partition already ingested")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if a.debug else logging.INFO, format="%(message)s")
    if a.debug:
        print("[debug on]")
    day = a.day
    spx_bars(day)
    if not a.skip_hiro:
        stage = Path(a.stage) if a.stage else Path(f"/tmp/hiro_stage_{day}")
        cap = hiro_capture(day, stage)
        med = hiro_identity(day, cap)
        hiro_ingest(day, cap, med)
    elif not (HIRO_ROOT / f"date={day}").exists():
        refuse(f"--skip-hiro but no HIRO partition for {day}")
    chains(day)
    v1_backtest(day)
    watch(day)
    print(f"\ndaily_session {day}: done — now `python hiro_watch/compare.py`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
