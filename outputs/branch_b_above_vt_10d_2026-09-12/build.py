"""Build one entry-only, offline carousel from existing SPX data; no trading engine."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs

from signals import add_features, evaluate_day

OUT = Path(__file__).resolve().parent
AS_OF = "2026-09-11"
SPX = Path("/Users/dgrissen/Dev/central_trade_data/thetadata/spx_index_1m_ohlc")
LEVELS = Path("/Users/dgrissen/Dev/core_spotgamma_spx_vix_data/offset_historical_spotgamma_data.csv")
REFERENCE = Path("/Users/dgrissen/Dev/spy_chaser/.claude/worktrees/below_vol_trigger/outputs/bvt_5m_ride_carousel.html")
RULE_SOURCE = REFERENCE.parents[1] / "eda/bvt_5m_expand_probe.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aggregate_day(date: str, raw: pd.DataFrame, require_full: bool = True) -> pd.DataFrame:
    """Aggregate complete, unique five-minute intervals; never fill missing prices."""
    g = raw.loc[raw["min"].between(570, 959)].sort_values("min").copy()
    if g["min"].duplicated().any():
        raise ValueError(f"{date}: duplicate RTH minute")
    if not np.isfinite(g[["min", "open", "high", "low", "close"]]).all().all():
        raise ValueError(f"{date}: nonfinite OHLC or minute")
    if ((g["low"] <= 0) | (g["high"] < g[["open", "close"]].max(axis=1))
            | (g["low"] > g[["open", "close"]].min(axis=1))
            | (g["min"] != g["min"].astype(int))).any():
        raise ValueError(f"{date}: invalid OHLC or minute")
    if require_full and g["min"].tolist() != list(range(570, 960)):
        raise ValueError(f"{date}: incomplete RTH session ({len(g)}/390 minutes)")
    g["min5"] = g["min"] // 5 * 5
    bars = g.groupby("min5", as_index=False).agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), minute_count=("min", "count"))
    bars = bars.loc[bars["minute_count"] == 5].drop(columns="minute_count")
    bars.insert(0, "date", date)
    return bars


def select_days(ledger: pd.DataFrame, count: int = 10) -> pd.DataFrame:
    """Choose latest complete sessions opening strictly above same-date recorded VT."""
    eligible = ledger.loc[ledger["complete"] & ledger["vt"].gt(0)
                          & ledger["open"].gt(ledger["vt"])].sort_values("date")
    if len(eligible) < count:
        raise ValueError(f"Only {len(eligible)} eligible sessions; need {count}")
    return eligible.tail(count).reset_index(drop=True)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Read dated levels and all cached history through the frozen as-of date."""
    levels = pd.read_csv(LEVELS)
    levels["csv_row"] = np.arange(len(levels)) + 2
    levels = levels.drop_duplicates("Date", keep="last").set_index("Date")
    history, records, hashes = [], [], []
    for path in sorted(SPX.glob("*.parquet")):
        date = path.stem
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or date > AS_OF:
            continue
        raw = pd.read_parquet(path)
        first = raw.loc[raw["min"] == 570, "open"]
        row = levels.loc[date] if date in levels.index else {}
        record = {"date": date, "open": float(first.iloc[0]) if len(first) == 1 else None,
                  "vt": row.get("Vol Trigger"), "sg_index": row.get("sg_index"),
                  "levels_csv_row": row.get("csv_row"), "complete": False,
                  "data_issue": "", "source_path": str(path), "source_sha256": sha256(path)}
        try:
            bars = aggregate_day(date, raw, require_full=False)
            record["complete"] = len(bars) == 78
            if not record["complete"]:
                record["data_issue"] = f"{len(bars)}/78 complete five-minute intervals"
            history.append(bars)
        except ValueError as exc:
            record["data_issue"] = str(exc)
        records.append(record)
        hashes.append({"date": date, "path": str(path), "sha256": record["source_sha256"],
                       "included_in_warmup": not record["data_issue"] or record["data_issue"].endswith("intervals")})
    return pd.concat(history, ignore_index=True), pd.DataFrame(records), hashes


def reference_layout() -> dict:
    """Reuse the actual saved chart layout, not its changed Python generator."""
    text = REFERENCE.read_text()
    start = text.index("[{", text.index("Plotly.newPlot("))
    _, consumed = json.JSONDecoder().raw_decode(text[start:])
    start = text.index("{", start + consumed)
    layout, _ = json.JSONDecoder().raw_decode(text[start:])
    layout["yaxis"]["title"]["text"] = "SPX"
    layout.pop("width", None)
    layout["autosize"] = True
    layout["height"] = 860
    return layout


def clean_records(frame: pd.DataFrame) -> list[dict]:
    """JSON output uses null, never JavaScript NaN."""
    return json.loads(frame.to_json(orient="records", double_precision=12))


def main() -> None:
    bars, ledger, hashes = load_inputs()
    selected = select_days(ledger)
    dates = selected["date"].tolist()
    for source in hashes:
        source["included_in_warmup"] &= source["date"] <= dates[-1]
    # Freeze the dates before calculating any signal or outcome.
    selected.to_csv(OUT / "selected_days.csv", index=False)
    ledger["selected"] = ledger["date"].isin(dates)
    ledger.to_csv(OUT / "selection_ledger.csv", index=False)
    features = add_features(bars.loc[bars["date"] <= dates[-1]].reset_index(drop=True))
    days, all_events, diagnostics = [], [], []
    for _, selection in selected.iterrows():
        date = selection["date"]
        g, events = evaluate_day(features.loc[features["date"] == date].reset_index(drop=True))
        raw = pd.read_parquet(SPX / f"{date}.parquet").set_index("min")
        for event in events:
            known = int(event["known_min"])
            event["entry_reference_min"] = known
            event["entry_reference_px"] = float(raw.loc[known, "open"])
            event["entry_above_vt"] = event["entry_reference_px"] > selection["vt"]
            event["setup_id"] = f"{date}_{event['variant']}_{known}"
        all_events.extend(events)
        diagnostics.append(g)
        days.append({"date": date, "open": selection["open"], "vt": selection["vt"],
                     "sg_index": selection["sg_index"], "bars": clean_records(g),
                     "events": clean_records(pd.DataFrame(events)) if events else []})
    event_frame = pd.DataFrame(all_events)
    event_frame.to_csv(OUT / "entries.csv", index=False)
    pd.concat(diagnostics).to_csv(OUT / "bar_diagnostics.csv", index=False)
    totals = {v: sum(e["variant"] == v for e in all_events) for v in ("thrust", "staircase")}
    payload = {"days": days, "layout": reference_layout(), "totals": totals}
    (OUT / "chart_data.json").write_text(json.dumps(payload, allow_nan=False, indent=2))
    # One integrated dashboard; old delivered links forward into its matching mode.
    (OUT / "plotly.min.js").write_text(get_plotlyjs())
    template = (OUT / "carousel_template.html").read_text()
    page = template.replace("__PAYLOAD__", json.dumps(payload, allow_nan=False).replace("</", "<\\/"))
    (OUT / "branch_b_carousel.html").write_text(page)
    for variant in ("thrust", "staircase"):
        redirect = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Branch B — integrated dashboard</title>
<p><a href="branch_b_carousel.html#mode={variant}">Open the integrated Branch B dashboard</a></p>
<script>
const date=location.hash.slice(1);
location.replace('branch_b_carousel.html#mode={variant}'+
  (/^\\d{{4}}-\\d{{2}}-\\d{{2}}$/.test(date)?'&date='+date:''));
</script></html>'''
        (OUT / f"{variant}_carousel.html").write_text(redirect)
    manifest = {
        "as_of": AS_OF, "date_selection": "Latest 10 complete cached SPX RTH sessions with 09:30 open > same-date VT",
        "selected_dates": dates, "levels_path": str(LEVELS), "levels_sha256": sha256(LEVELS),
        "dashboard": {"file": "branch_b_carousel.html", "mode_switch": "In-page thrust-only or thrust-plus-staircase",
                      "date_filter": "Only dates with entry events matching the mode and checked entry types; full ten-date research data retained"},
        "levels_duplicate_policy": "Last matching CSV row, as in existing LevelsLoader; no forward-fill",
        "levels_provenance": {"path": str(OUT / "vt_provenance.json"), "sha256": sha256(OUT / "vt_provenance.json")},
        "levels_asof_limit": "All 10 values match notes headed 07:00 AM ET (see vt_provenance.json). This supports pre-open publication, not contemporaneous local ingestion; the CSV has no capture/revision history.",
        "clock": "Cached minute treated as interval start. 5m bar [t,t+5) known at t+5; entry reference is next stored 1m open at t+5. No option fill claimed.",
        "entry_window": "10:00 through 14:30 ET inclusive, measured at decision availability",
        "vt_scope": "Opening cohort only. No intraday VT or SG-index entry filter.",
        "warmup": "All valid complete 5m intervals in cached chronological RTH history through last selected date; no overnight bars; overnight gaps enter ATR. Incomplete 5m intervals omitted, never filled.",
        "adaptations": ["SPX OHLC-only; original SPY VWAP condition omitted identically in both variants",
                        "Completed five-minute intervals only; explicit availability clock and B entry window",
                        "Independent first-of-contiguous-qualifying-run entry extraction; no exit-dependent rearming"],
        "disabled": ["fixed-time baseline", "HIRO", "VWAP", "volume gates", "ADX gate", "overrides", "clean-leg", "strength bypass", "exits", "option simulation", "parameter search"],
        "chart_reference": str(REFERENCE), "chart_reference_sha256": sha256(REFERENCE),
        "rule_reference": str(RULE_SOURCE), "rule_reference_sha256": sha256(RULE_SOURCE),
        "thrust_threshold_bps": 10.0, "fan_min_atr": 0.10, "extension_max_atr": 1.5,
        "staircase_two_bar_ema5_min_atr": 0.60, "entry_totals": totals,
        "sources": hashes, "code_sha256": {p: sha256(OUT / p) for p in ("build.py", "signals.py", "carousel_template.html")}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, allow_nan=False, indent=2))
    print(json.dumps({"dates": dates, "counts": totals, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
