#!/usr/bin/env python3
"""Render the compact audit report for a four-method single-name scan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


METHOD_ORDER = (
    "buy-first call puke",
    "buy-first call standard",
    "sell-first call grab",
    "buy-first put-tail inventory",
)


def number(value: object, digits: int = 1) -> str:
    """Format a numeric cell without leaking pandas NaN strings."""
    parsed = pd.to_numeric(value, errors="coerce")
    return "—" if pd.isna(parsed) else f"{float(parsed):.{digits}f}"


def contract_text(row: pd.Series) -> str:
    """Describe the exact two-leg implementation selected for one finalist."""
    expiry = str(row["expiry"])[5:]
    first = number(row["leg1_strike"], 1).rstrip("0").rstrip(".")
    second = number(row["leg2_strike"], 1).rstrip("0").rstrip(".")
    cash = number(row["entry_cash"], 2)
    scenario = str(row["scenario"])
    if scenario == "sell-first call grab":
        target = number(row["target_leg2_price"], 2)
        return f"STO {expiry} {first}C at ≥${cash}; rest BTO {second}C at ${target}"
    if scenario == "buy-first call standard":
        return f"BTO {expiry} {first}C at ≤${cash}; rest STO {second}C into strength"
    suffix = "P" if str(row.get("option_side")) == "put" else "C"
    return f"BTO {expiry} {first}/{second}{suffix} complete spread at ≤${cash}"


def reason_text(row: pd.Series) -> str:
    """Explain why one row belongs to its canonical method."""
    scenario = str(row["scenario"])
    iv_rank = number(row["ivRank1y"])
    rr_rank = number(row["rr25_pct252"])
    if scenario == "buy-first call puke":
        return (
            f"RR {rr_rank}≥60; call-skew {number(row['callskew_pct252'])}≤40; "
            f"IV {iv_rank}≤65; drawdown {number(row['drawdown_20d_pct'])}%; "
            f"5d {number(row['return_5d_pct'])}%."
        )
    if scenario == "buy-first call standard":
        return (
            f"{str(row['buy_surface_tier']).title()} call-cheap surface: RR {rr_rank}, "
            f"call-skew {number(row['callskew_pct252'])}, IV {iv_rank}; "
            f"63d relative return {number(row['relative_return_63d_pct'])}%."
        )
    if scenario == "sell-first call grab":
        return (
            f"RR {rr_rank}≤10; call-wing {number(row['call_wing_10_pct252'])}≥85; "
            f"kink {number(row['call_kink_pct252'])}≥70; IV {iv_rank}; "
            f"5d {number(row['return_5d_pct'])}%."
        )
    return (
        f"IV {iv_rank}≤35; RR {rr_rank}≤50; put-skew "
        f"{number(row['putskew_pct252'])}≤25; executable far-tail spread."
    )


def markdown_table(frame: pd.DataFrame) -> str:
    """Render a small frame as a GitHub-flavored Markdown table."""
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_report(
    *,
    output_dir: Path,
    universe_csv: Path,
    orats_manifest: Path,
) -> str:
    """Build the complete compact report from derived scan artifacts."""
    candidates = pd.read_csv(output_dir / "single_name_call_screen_candidates.csv")
    checks = pd.read_csv(output_dir / "single_name_call_screen_chain_checks.csv")
    finalists = pd.read_csv(output_dir / "single_name_call_screen_finalists.csv")
    summary = json.loads(
        (output_dir / "single_name_call_screen_summary.json").read_text()
    )
    chain_summary = json.loads(
        (output_dir / "single_name_call_screen_chain_summary.json").read_text()
    )
    inventory = pd.read_csv(output_dir / "hiro_inventory_windows.csv")
    pending = pd.read_csv(output_dir / "hiro_inventory_pending.csv")
    capture_summary = pd.read_csv(
        output_dir / "hiro_ticker_followthrough_to_2026-09-02" / "summary.csv"
    )
    ledger = json.loads(orats_manifest.read_text())

    surface_daily = (
        candidates.groupby(["tradeDate", "scenario"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=METHOD_ORDER, fill_value=0)
    )
    confirmed_daily = (
        checks.loc[checks["chain_confirmed"]]
        .groupby(["tradeDate", "scenario"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=METHOD_ORDER, fill_value=0)
    )
    daily_rows: list[dict[str, object]] = []
    for trade_date in summary["dates"]:
        row: dict[str, object] = {"Date": trade_date}
        for scenario in METHOD_ORDER:
            short = {
                "buy-first call puke": "Call puke",
                "buy-first call standard": "Call standard",
                "sell-first call grab": "Call grab",
                "buy-first put-tail inventory": "Put inventory",
            }[scenario]
            row[short] = (
                f"{int(surface_daily.at[trade_date, scenario])}/"
                f"{int(confirmed_daily.at[trade_date, scenario])}"
            )
        daily_rows.append(row)

    finalist_rows: list[dict[str, str]] = []
    order = {method: index for index, method in enumerate(METHOD_ORDER)}
    finalists = finalists.assign(
        method_order=finalists["scenario"].map(order),
    ).sort_values(["method_order", "tradeDate", "ticker"])
    for _, row in finalists.iterrows():
        finalist_rows.append(
            {
                "Date": str(row["tradeDate"]),
                "Ticker": str(row["ticker"]),
                "Method": str(row["scenario"]),
                "RR rank": number(row["rr25_pct252"]),
                "IV rank": number(row["ivRank1y"]),
                "Why": reason_text(row),
                "Exact strategy": contract_text(row),
            }
        )

    universe_hash = hashlib.sha256(universe_csv.read_bytes()).hexdigest()
    pending_names = ", ".join(pending["ticker"].astype(str)) or "none"
    lines = [
        "# Four-method HIRO single-name scan through 2026-09-02",
        "",
        "## Outcome",
        "",
        (
            f"The authenticated SpotGamma HIRO universe contained **{summary['input_universe_tickers']} "
            f"tickers**. After excluding indices/funds and enforcing the frozen liquidity gates, "
            f"the scan produced **{summary['candidate_rows']} surface-qualified method/date rows "
            f"across {summary['candidate_tickers']} current tickers**. Exact historical chains "
            f"confirmed **{chain_summary['confirmed_rows']} rows**, yielding "
            f"**{sum(chain_summary['unique_finalists_by_scenario'].values())} method/ticker finalists "
            f"across {chain_summary['finalist_tickers']} unique stocks**."
        ),
        "",
        (
            f"The HIRO follow-through inventory is the union of the prior capture and the current "
            f"surface set: **{len(inventory) + len(pending)} tickers total**, with "
            f"**{len(inventory)} eligible for a completed next-session window through September 2**. "
            f"Pending September 2 identifications: **{pending_names}**."
        ),
        "",
        (
            f"The serial authenticated capture completed **{len(capture_summary)}/{len(inventory)} "
            f"eligible tickers**: **{int(capture_summary['available_sessions'].sum())} available "
            f"ticker-sessions**, **{int(capture_summary['unavailable_sessions'].sum())} explicitly "
            f"unavailable ticker-sessions**, and **{int(capture_summary['row_count'].sum()):,} "
            f"provider rows**."
        ),
        "",
        "## Frozen method definitions",
        "",
        "| Canonical name | Path | Surface/regime gate | Exact implementation |",
        "|---|---|---|---|",
        "| buy-first call puke | Buy complete spread first | RR rank ≥60, call-skew rank ≤40, IV Rank ≤65, drawdown ≤-8%, 5d return <0 | Buy complete 20–35%-OTM, 30–90 DTE call spread for $0.05–$0.50; scale out into rebound |",
        "| buy-first call standard | Buy long call first | Good/Better/Best call-cheap surface plus constructive technical/relative-strength overlay | Buy ~15-delta 30–60 DTE call; rest adjacent upper-call sale into strength |",
        "| sell-first call grab | Sell far call first | Call-wing rank ≥85, kink ≥70, RR rank ≤10, positive 5d return, near 20d high, IV Rank 30–70, no near earnings | Sell 2–6-delta 5–19 DTE call; rest nearer-call buy; breakout stop mandatory |",
        "| buy-first put-tail inventory | Buy complete put spread first | IV Rank ≤35, RR rank ≤50, put-skew rank ≤25 | Buy complete current/next-monthly spread 25–45% OTM, roughly $5 wide, for ≤$0.10; hold as inventory and rest scale-out offers |",
        "",
        "## Daily surface rows / exact-chain confirmations",
        "",
        "Each cell is `surface-qualified / exact-chain-confirmed`. Call methods begin August 28; put-tail inventory gets the requested extra week beginning August 24.",
        "",
        markdown_table(pd.DataFrame(daily_rows)),
        "",
        "## Exact-chain finalists",
        "",
        markdown_table(pd.DataFrame(finalist_rows)),
        "",
        "## Audit notes",
        "",
        f"- ORATS ledger: **{ledger['used']} / {ledger['max_calls']}** attempts used. Failed sandbox-only connection attempts remain counted.",
        "- The primary chain query covered call delta 0.005–0.995. A separately cached 0.995–0.99999 gap fill was required to avoid falsely rejecting ultra-far puts.",
        "- Put-tail earnings are annotated, not rejected: this is persistent hedge inventory, not an earnings-timing setup.",
        "- All/Next Expiry/Retail HIRO groups are preserved separately and must not be summed because they overlap.",
        "- Missing provider sessions are unavailable, not zero flow.",
        f"- HIRO universe SHA-256: `{universe_hash}`.",
        "",
        "## Artifacts",
        "",
        "- `single_name_call_screen_candidates.csv`: all surface-qualified method/date rows.",
        "- `single_name_call_screen_chain_checks.csv`: every exact-chain selection and rejection reason.",
        "- `single_name_call_screen_finalists.csv`: one best confirmed date per method/ticker.",
        "- `single_name_call_screen_all.parquet`: complete eligible ticker/day feature table.",
        "- `hiro_inventory_windows.csv`: serial-capture windows for prior-plus-current inventory.",
        "- `hiro_inventory_pending.csv`: identifiers with no completed post-signal session yet.",
        "- `hiro_ticker_followthrough_to_2026-09-02/summary.csv`: compact committed capture coverage.",
        "- `hiro_ticker_followthrough_to_2026-09-02/CAPTURE_NOTES.md`: retention, integrity, and reproduction notes.",
        "- `hiro_tickers_2026-09-03.csv`: refreshed authenticated HIRO membership snapshot.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Render the report and copy the exact HIRO universe snapshot."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--universe-csv", required=True)
    parser.add_argument("--orats-manifest", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    universe_csv = Path(args.universe_csv).expanduser().resolve()
    report = render_report(
        output_dir=output_dir,
        universe_csv=universe_csv,
        orats_manifest=Path(args.orats_manifest).expanduser().resolve(),
    )
    (output_dir / "README.md").write_text(report, encoding="utf-8")
    universe = pd.read_csv(universe_csv)
    universe.to_csv(output_dir / "hiro_tickers_2026-09-03.csv", index=False)


if __name__ == "__main__":
    main()
