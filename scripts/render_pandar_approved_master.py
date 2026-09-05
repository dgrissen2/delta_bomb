#!/usr/bin/env python3
"""Build the Pandar-only master ledger from the frozen point-in-time scans."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable

import pandas as pd


SELL_FIRST_CALL_GRAB = "sell-first call grab"
BUY_FIRST_PUT_TAIL_INVENTORY = "buy-first put-tail inventory"
PANDAR_METHODS = (SELL_FIRST_CALL_GRAB, BUY_FIRST_PUT_TAIL_INVENTORY)
METHOD_START = {
    SELL_FIRST_CALL_GRAB: "2026-08-11",
    BUY_FIRST_PUT_TAIL_INVENTORY: "2026-08-24",
}
ORATS_UNAVAILABLE_DATE = "2026-09-04"
MASTER_COLUMNS = (
    "tradeDate",
    "ticker",
    "scenario",
    "pandar_approval_scope",
    "pandar_direct_portion",
    "project_derived_portion",
    "first_action",
    "source_dataset",
    "ranking_score",
    "stockPrice",
    "return_5d_pct",
    "drawdown_20d_pct",
    "ivRank1y",
    "rr25_pct252",
    "callskew_pct252",
    "putskew_pct252",
    "call_wing_10_pct252",
    "call_kink_pct252",
    "avgOptVolu20d",
    "oi",
    "dollar_stock_volume",
    "chain_confirmed",
    "failure_reason",
    "option_side",
    "expiry",
    "dte",
    "leg1_action",
    "leg1_strike",
    "leg1_delta",
    "leg1_bid",
    "leg1_ask",
    "leg1_oi",
    "leg1_volume",
    "leg2_action",
    "leg2_strike",
    "leg2_bid",
    "leg2_ask",
    "leg2_oi",
    "leg2_volume",
    "spread_width",
    "entry_cash",
    "target_leg2_price",
    "long_otm_pct",
    "lower_otm_pct",
)


def number(value: object, digits: int = 1) -> str:
    """Format numeric output without emitting pandas NaN strings."""
    parsed = pd.to_numeric(value, errors="coerce")
    return "—" if pd.isna(parsed) else f"{float(parsed):.{digits}f}"


def markdown_table(frame: pd.DataFrame) -> str:
    """Render a dataframe as a compact GitHub-flavored Markdown table."""
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def filter_approved_rows(
    frame: pd.DataFrame,
    *,
    source_dataset: str,
    legacy: bool = False,
    later_period: bool = False,
) -> pd.DataFrame:
    """Keep only the two approved lanes and enforce source-period boundaries."""
    rows = frame.copy()
    if legacy:
        rows = rows.loc[rows["scenario"].eq("sell-first")].copy()
        rows["scenario"] = SELL_FIRST_CALL_GRAB
    else:
        rows = rows.loc[rows["scenario"].isin(PANDAR_METHODS)].copy()
    if later_period:
        rows = rows.loc[
            rows["scenario"].eq(BUY_FIRST_PUT_TAIL_INVENTORY)
            | rows["tradeDate"].ge("2026-08-28")
        ].copy()
    rows["source_dataset"] = source_dataset
    return rows


def add_pandar_attribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Attach the direct-versus-derived guardrail to every master row."""
    rows = frame.copy()
    is_put = rows["scenario"].eq(BUY_FIRST_PUT_TAIL_INVENTORY)
    rows["pandar_approval_scope"] = is_put.map(
        {
            True: "Pandar-direct inventory program; exact scanner geometry is partly mechanized",
            False: "Pandar-direct call-tail sale/crush core only; conversion is derived",
        }
    )
    rows["pandar_direct_portion"] = is_put.map(
        {
            True: "accumulate cheap far-OTM 1:1 put vertical inventory; usually about $5 wide and under $0.10; recycle and roll",
            False: "sell unusually overpriced far-OTM front-weekly call tails; expect local wing crush; size for strike touch",
        }
    )
    rows["project_derived_portion"] = is_put.map(
        {
            True: "IV/RR/put-skew gates; fixed 25-45% OTM band; complete-at-entry rule; universal 3x/5x exits",
            False: "RR/wing/kink gates; 2-6 delta and 5-19 DTE selection; nearer-call conversion; order and stop rules",
        }
    )
    rows["first_action"] = is_put.map(
        {
            True: "buy complete put spread in this implementation",
            False: "sell far-OTM call",
        }
    )
    return rows


def build_master(old_dir: Path, later_dir: Path, gap_dir: Path) -> pd.DataFrame:
    """Merge non-overlapping source windows into one Pandar-only ledger."""
    old = filter_approved_rows(
        pd.read_csv(old_dir / "single_name_call_screen_chain_checks.csv"),
        source_dataset="2026-08-11_to_2026-08-27_call_scan",
        legacy=True,
    )
    later = filter_approved_rows(
        pd.read_csv(later_dir / "single_name_call_screen_chain_checks.csv"),
        source_dataset="2026-08-24_to_2026-09-02_four_method_scan",
        later_period=True,
    )
    gap = filter_approved_rows(
        pd.read_csv(gap_dir / "single_name_call_screen_chain_checks.csv"),
        source_dataset="2026-09-03_pandar_only_gap_scan",
    )
    master = add_pandar_attribution(pd.concat([old, later, gap], ignore_index=True))
    keys = ["tradeDate", "ticker", "scenario"]
    duplicates = master.duplicated(keys, keep=False)
    if duplicates.any():
        collisions = master.loc[duplicates, keys].to_dict("records")
        raise ValueError(f"duplicate master keys: {collisions[:10]}")
    for column in MASTER_COLUMNS:
        if column not in master.columns:
            master[column] = pd.NA
    method_order = {method: index for index, method in enumerate(PANDAR_METHODS)}
    master["_method_order"] = master["scenario"].map(method_order)
    master = master.sort_values(
        ["tradeDate", "_method_order", "ticker"]
    ).drop(columns="_method_order")
    return master.loc[:, MASTER_COLUMNS].reset_index(drop=True)


def build_daily_coverage(master: pd.DataFrame) -> pd.DataFrame:
    """Create one auditable row for every session/method, including unavailable data."""
    rows: list[dict[str, object]] = []
    sessions = pd.bdate_range("2026-08-11", ORATS_UNAVAILABLE_DATE)
    for timestamp in sessions:
        trade_date = timestamp.date().isoformat()
        for method in PANDAR_METHODS:
            if trade_date < METHOD_START[method]:
                status = "not_in_scope"
            elif trade_date == ORATS_UNAVAILABLE_DATE:
                status = "provider_unavailable"
            else:
                status = "evaluated"
            day = master.loc[
                master["tradeDate"].eq(trade_date) & master["scenario"].eq(method)
            ]
            confirmed = day.loc[day["chain_confirmed"].fillna(False).astype(bool)]
            rows.append(
                {
                    "tradeDate": trade_date,
                    "scenario": method,
                    "signal_data_status": status,
                    "surface_count": int(len(day)),
                    "exact_chain_count": int(len(confirmed)),
                    "surface_tickers": ",".join(day["ticker"].astype(str)),
                    "exact_chain_tickers": ",".join(confirmed["ticker"].astype(str)),
                }
            )
    return pd.DataFrame(rows)


def _empty_hiro_rows(
    *, ticker: str, session_date: str, source_capture: str, priority: int
) -> list[dict[str, object]]:
    return [
        {
            "ticker": ticker,
            "session_date": session_date,
            "series_group": group,
            "status": "unavailable",
            "market_hours": "09:30-16:00 America/New_York",
            "hiro_total_usd": pd.NA,
            "hiro_call_usd": pd.NA,
            "hiro_put_usd": pd.NA,
            "stock_open": pd.NA,
            "stock_close": pd.NA,
            "stock_return_pct": pd.NA,
            "points": 0,
            "source_capture": source_capture,
            "_priority": priority,
        }
        for group in ("all", "nextExp", "retail")
    ]


def summarize_hiro_file(
    path: Path,
    *,
    ticker: str,
    session_date: str,
    source_capture: str,
    priority: int,
) -> list[dict[str, object]]:
    """Reduce one normalized HIRO partition to separate regular-session scopes."""
    frame = pd.read_csv(path)
    if frame.empty:
        return _empty_hiro_rows(
            ticker=ticker,
            session_date=session_date,
            source_capture=source_capture,
            priority=priority,
        )
    timestamps = pd.to_datetime(frame["utc_iso"], utc=True).dt.tz_convert(
        "America/New_York"
    )
    minute = timestamps.dt.hour * 60 + timestamps.dt.minute
    frame = frame.loc[minute.between(570, 960)].copy()
    rows: list[dict[str, object]] = []
    for group in ("all", "nextExp", "retail"):
        scoped = frame.loc[frame["series_group"].eq(group)]
        if scoped.empty:
            rows.extend(
                _empty_hiro_rows(
                    ticker=ticker,
                    session_date=session_date,
                    source_capture=source_capture,
                    priority=priority,
                )[:1]
            )
            rows[-1]["series_group"] = group
            continue
        stock = pd.to_numeric(scoped["stock_price"], errors="coerce").dropna()
        stock_open = stock.iloc[0] if not stock.empty else pd.NA
        stock_close = stock.iloc[-1] if not stock.empty else pd.NA
        stock_return = (
            (float(stock_close) / float(stock_open) - 1) * 100
            if pd.notna(stock_open) and float(stock_open) != 0 and pd.notna(stock_close)
            else pd.NA
        )
        rows.append(
            {
                "ticker": ticker,
                "session_date": session_date,
                "series_group": group,
                "status": "available",
                "market_hours": "09:30-16:00 America/New_York",
                "hiro_total_usd": pd.to_numeric(
                    scoped["delta_total"], errors="coerce"
                ).sum(min_count=1),
                "hiro_call_usd": pd.to_numeric(
                    scoped["delta_call"], errors="coerce"
                ).sum(min_count=1),
                "hiro_put_usd": pd.to_numeric(
                    scoped["delta_put"], errors="coerce"
                ).sum(min_count=1),
                "stock_open": stock_open,
                "stock_close": stock_close,
                "stock_return_pct": stock_return,
                "points": int(len(scoped)),
                "source_capture": source_capture,
                "_priority": priority,
            }
        )
    return rows


def build_hiro_metrics(
    capture_roots: Iterable[tuple[str, Path]], approved_tickers: set[str]
) -> pd.DataFrame:
    """Build a compact deduplicated metric ledger from local captured partitions."""
    rows: list[dict[str, object]] = []
    for priority, (source_capture, root) in enumerate(capture_roots, start=1):
        for path in sorted(root.glob("ticker=*/date=*/normalized/hiro_series.csv")):
            ticker = path.parents[2].name.removeprefix("ticker=")
            if ticker not in approved_tickers:
                continue
            session_date = path.parents[1].name.removeprefix("date=")
            rows.extend(
                summarize_hiro_file(
                    path,
                    ticker=ticker,
                    session_date=session_date,
                    source_capture=source_capture,
                    priority=priority,
                )
            )
    metrics = pd.DataFrame(rows)
    metrics["_available"] = metrics["status"].eq("available").astype(int)
    metrics = metrics.sort_values(
        ["ticker", "session_date", "series_group", "_available", "_priority"]
    ).drop_duplicates(["ticker", "session_date", "series_group"], keep="last")
    return metrics.drop(columns=["_available", "_priority"]).reset_index(drop=True)


def add_hiro_followup_coverage(
    master: pd.DataFrame, hiro_metrics: pd.DataFrame
) -> pd.DataFrame:
    """Annotate each signal with available post-identification HIRO sessions."""
    available = hiro_metrics.loc[
        hiro_metrics["status"].eq("available")
        & hiro_metrics["series_group"].eq("all")
    ]
    dates_by_ticker = {
        ticker: sorted(set(rows["session_date"].astype(str)))
        for ticker, rows in available.groupby("ticker")
    }
    rows = master.copy()
    counts: list[int] = []
    first_dates: list[object] = []
    last_dates: list[object] = []
    for signal in rows.itertuples(index=False):
        dates = [
            value
            for value in dates_by_ticker.get(str(signal.ticker), [])
            if value > str(signal.tradeDate)
        ]
        counts.append(len(dates))
        first_dates.append(dates[0] if dates else pd.NA)
        last_dates.append(dates[-1] if dates else pd.NA)
    rows["hiro_followup_available_sessions"] = counts
    rows["hiro_followup_first_session"] = first_dates
    rows["hiro_followup_last_session"] = last_dates
    return rows


def contract_text(row: pd.Series) -> str:
    """Render the selected two-leg implementation for an exact confirmation."""
    expiry = str(row["expiry"])[5:]
    first = number(row["leg1_strike"], 1).rstrip("0").rstrip(".")
    second = number(row["leg2_strike"], 1).rstrip("0").rstrip(".")
    cash = number(row["entry_cash"], 2)
    if row["scenario"] == SELL_FIRST_CALL_GRAB:
        target = number(row["target_leg2_price"], 2)
        return f"STO {expiry} {first}C ≥${cash}; rest BTO {second}C ${target}"
    return f"BTO {expiry} {first}/{second}P ≤${cash}"


def _daily_report_table(coverage: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for trade_date in sorted(coverage["tradeDate"].unique()):
        day = coverage.loc[coverage["tradeDate"].eq(trade_date)].set_index("scenario")
        call = day.loc[SELL_FIRST_CALL_GRAB]
        put = day.loc[BUY_FIRST_PUT_TAIL_INVENTORY]
        status = (
            "ORATS unavailable"
            if call["signal_data_status"] == "provider_unavailable"
            else "evaluated"
        )
        if put["signal_data_status"] == "not_in_scope":
            put_text = "not in scope"
        elif put["signal_data_status"] == "provider_unavailable":
            put_text = "unavailable"
        else:
            put_text = f"{put['surface_count']}/{put['exact_chain_count']}"
        call_text = (
            "unavailable"
            if call["signal_data_status"] == "provider_unavailable"
            else f"{call['surface_count']}/{call['exact_chain_count']}"
        )
        rows.append(
            {
                "Date": trade_date,
                "Call grab": call_text,
                "Put inventory": put_text,
                "Status": status,
            }
        )
    return pd.DataFrame(rows)


def render_readme(
    master: pd.DataFrame,
    coverage: pd.DataFrame,
    hiro_metrics: pd.DataFrame,
    *,
    orats_manifest: Path,
    universe_csv: Path,
) -> str:
    """Render the Pandar-only master report."""
    exact = master.loc[master["chain_confirmed"].fillna(False).astype(bool)].copy()
    surface_counts = master["scenario"].value_counts()
    exact_counts = exact["scenario"].value_counts()
    ledger = json.loads(orats_manifest.read_text())
    hiro_available = hiro_metrics.loc[
        hiro_metrics["status"].eq("available")
        & hiro_metrics["series_group"].eq("all")
    ]
    sep3_exact = exact.loc[exact["tradeDate"].eq("2026-09-03")].copy()
    sep4_all = hiro_available.loc[
        hiro_available["session_date"].eq("2026-09-04")
    ].set_index("ticker")
    gap_rows: list[dict[str, str]] = []
    for _, row in sep3_exact.sort_values(["scenario", "ticker"]).iterrows():
        hiro = sep4_all.loc[row["ticker"]] if row["ticker"] in sep4_all.index else None
        gap_rows.append(
            {
                "Ticker": str(row["ticker"]),
                "Method": str(row["scenario"]),
                "RR": number(row["rr25_pct252"]),
                "IV": number(row["ivRank1y"]),
                "Exact contract": contract_text(row),
                "09-04 All HIRO": (
                    f"${float(hiro['hiro_total_usd']) / 1e9:+.2f}bn"
                    if hiro is not None
                    else "—"
                ),
            }
        )
    universe_hash = hashlib.sha256(universe_csv.read_bytes()).hexdigest()
    lines = [
        "# Pandar-approved single-name master through 2026-09-04",
        "",
        "## Outcome",
        "",
        (
            f"The master contains **{len(master)} surface-qualified ticker/date rows across "
            f"{master['ticker'].nunique()} tickers**, and only the two narrowly approved Pandar "
            f"lanes. Exact historical chains confirmed **{len(exact)} rows across "
            f"{exact['ticker'].nunique()} tickers**. September 4 is present in the coverage ledger "
            "as **provider unavailable** because ORATS had not published that completed session; "
            "it is not counted as a zero-signal day."
        ),
        "",
        "| Pandar-approved lane | Surface rows | Exact-chain rows | What is actually Pandar-direct |",
        "|---|---:|---:|---|",
        (
            f"| buy-first put-tail inventory | {int(surface_counts.get(BUY_FIRST_PUT_TAIL_INVENTORY, 0))} "
            f"| {int(exact_counts.get(BUY_FIRST_PUT_TAIL_INVENTORY, 0))} | Cheap far-OTM 1:1 put-vertical inventory, usually about $5 wide and under $0.10; recycle and roll. The rank gates, fixed OTM band, complete-at-entry rule, and universal exits are mechanized. |"
        ),
        (
            f"| sell-first call grab | {int(surface_counts.get(SELL_FIRST_CALL_GRAB, 0))} "
            f"| {int(exact_counts.get(SELL_FIRST_CALL_GRAB, 0))} | The call-tail sale/crush core only: sell unusually overpriced far-OTM front-weekly calls and size for a strike touch. The systematic conversion and numeric screen are derived. |"
        ),
        "",
        "Buy-first call puke and buy-first call standard are intentionally absent from every master artifact.",
        "",
        "## Session coverage",
        "",
        "Each evaluated cell is `surface-qualified / exact-chain-confirmed`.",
        "",
        markdown_table(_daily_report_table(coverage)),
        "",
        "## Newly filled September 3 exact confirmations",
        "",
        markdown_table(pd.DataFrame(gap_rows)),
        "",
        "## HIRO coverage and interpretation",
        "",
        (
            f"The compact HIRO ledger contains **{len(hiro_available)} available ticker-sessions "
            f"across {hiro_available['ticker'].nunique()} approved tickers** after deduplication. "
            "The new capture added September 4 for all 107 September 3 surface qualifiers; a "
            "separate gap fill added September 3-4 for the previously pending MDB and PDD signals; "
            "a final 18-ticker pass filled every remaining recent post-signal coverage hole."
        ),
        "",
        "`pandar_approved_hiro_daily_metrics.csv` reports regular-session 09:30-16:00 America/New_York signed estimated delta-notional flow. `all`, `nextExp`, and `retail` overlap and remain separate; never sum them. Call and put components are retained, and unavailable provider sessions stay unavailable rather than becoming zero.",
        "",
        "## Audit trail",
        "",
        f"- ORATS calls: **{ledger['used']} / {ledger['max_calls']}**; {ledger['max_calls'] - ledger['used']} remained. Attempts include the two successful calendar checks that established September 4 was not yet published.",
        "- Surface rows are screen candidates; only rows with `chain_confirmed=true` had a qualifying historical spread in the captured chain.",
        "- The August 11-27 call-tail rows use the frozen original scan. The August 24-September 2 put rows and August 28-September 2 call-tail rows use the refreshed four-method scan. September 3 uses the Pandar-only gap run.",
        f"- HIRO-universe snapshot: 398 tickers; SHA-256 `{universe_hash}`.",
        "",
        "## Master artifacts",
        "",
        "- `pandar_approved_master.csv`: every surface-qualified Pandar-only ticker/date row, its attribution boundary, exact-chain result, contract fields, and post-signal HIRO coverage.",
        "- `pandar_approved_exact_confirmations.csv`: executable historical-chain subset; repeated qualifying dates are preserved.",
        "- `pandar_approved_daily_tickers.csv`: every in-scope session/method, including zero rows, not-in-scope dates, and September 4 provider-unavailable status.",
        "- `pandar_approved_hiro_daily_metrics.csv`: deduplicated RTH HIRO totals by ticker/session/scope with call and put components.",
        "- `gap_2026-09-03/`: frozen Pandar-only surface, chain checks, exact finalists, and summaries for the newly filled signal date.",
        "- `hiro_ticker_followthrough_to_2026-09-04/`: local raw/normalized September 4 HIRO capture plus committed compact summary and notes.",
        "- `hiro_ticker_followthrough_to_2026-09-04_pending_sep2/`: local MDB/PDD September 3-4 gap fill plus committed compact summary and notes.",
        "- `hiro_ticker_followthrough_to_2026-09-04_missing_followups/`: local 18-ticker recent completeness pass plus committed compact summary and notes.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Build all compact master artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-dir", required=True)
    parser.add_argument("--later-dir", required=True)
    parser.add_argument("--gap-dir", required=True)
    parser.add_argument("--old-hiro", required=True)
    parser.add_argument("--later-hiro", required=True)
    parser.add_argument("--gap-hiro", required=True)
    parser.add_argument("--pending-hiro", required=True)
    parser.add_argument("--missing-followups-hiro", required=True)
    parser.add_argument("--orats-manifest", required=True)
    parser.add_argument("--universe-csv", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    old_dir = Path(args.old_dir).expanduser().resolve()
    later_dir = Path(args.later_dir).expanduser().resolve()
    gap_dir = Path(args.gap_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    master = build_master(old_dir, later_dir, gap_dir)
    coverage = build_daily_coverage(master)
    captures = (
        ("legacy_through_2026-08-28", Path(args.old_hiro).expanduser().resolve()),
        ("refreshed_through_2026-09-02", Path(args.later_hiro).expanduser().resolve()),
        ("pending_sep2_through_2026-09-04", Path(args.pending_hiro).expanduser().resolve()),
        ("sep3_signals_through_2026-09-04", Path(args.gap_hiro).expanduser().resolve()),
        (
            "recent_missing_followups_through_2026-09-04",
            Path(args.missing_followups_hiro).expanduser().resolve(),
        ),
    )
    hiro_metrics = build_hiro_metrics(captures, set(master["ticker"].astype(str)))
    master = add_hiro_followup_coverage(master, hiro_metrics)
    exact = master.loc[master["chain_confirmed"].fillna(False).astype(bool)].copy()

    master.to_csv(output_dir / "pandar_approved_master.csv", index=False)
    exact.to_csv(output_dir / "pandar_approved_exact_confirmations.csv", index=False)
    coverage.to_csv(output_dir / "pandar_approved_daily_tickers.csv", index=False)
    hiro_metrics.to_csv(output_dir / "pandar_approved_hiro_daily_metrics.csv", index=False)
    readme = render_readme(
        master,
        coverage,
        hiro_metrics,
        orats_manifest=Path(args.orats_manifest).expanduser().resolve(),
        universe_csv=Path(args.universe_csv).expanduser().resolve(),
    )
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


if __name__ == "__main__":
    main()
