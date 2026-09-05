# delta_bomb

Analysis of the Delta Bomb options strategy (SPX hedges + upside calls) from Discord captures and the Delta Bombs white paper.

## Contents

- `docs/strategy_names.md` — canonical names and aliases for the four single-name strategies: **Buy-first call puke**, **Buy-first call standard**, **Sell-first call grab**, and **Buy-first put-tail inventory**.
- `docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/README.md` — the active Pandar-only master: just **Sell-first call grab (Pandar core only)** and **Buy-first put-tail inventory**, with every evaluated session, exact-chain decisions, and deduplicated HIRO follow-through through September 4.
- `docs/replay/hiro_daily_four_methods_2026-08-24_to_2026-09-02/README.md` — refreshed 398-ticker HIRO-universe scan through September 2, including the extra put-tail week, exact historical contracts, rejection evidence, and serial HIRO follow-through inventory.
- `scripts/hiro_engine/` — **the Delta Bomb signal engine** (paper-only): live SPX 1-min + HIRO evaluation of the frozen rules, silent paper executor, console event stream, backtesting (verification / sweep / rehearsal), and the R9 scorecard. Docs: `docs/hiro_engine/` (requirements v2.2, design v1.1, tasks v1.2, build_notes, RUNBOOK). Run: `cd scripts && ~/Dev/virtualenvs/gamma_chaser/bin/python -m hiro_engine {live|backtest|verify|scorecard|sweep}`. Tests: `pytest scripts/hiro_engine/tests`.
- `docs/delta_bombs.html` — the analysis: mechanics, SPX put playbook, the 50/20 → 3 bombs walkthrough, call side, evidence, and a Charlie McElligott positioning read.
- `docs/specs/p1_nvda_tail_sale_backtest.md` — P1 (NVDA tail sale + buyback) backtest spec v0.3 with Charlie/Codex reviews; `docs/specs/spx_1min_delta_bomb_leg_in_strategy.md` — SPX leg-in evidence from spy_chaser 1-min trend work, Codex errata, CIO memo, Feynman explanation (touch stats in `docs/replay/spx_touch_stats_full*.parquet`).
- `docs/sources/` — extracted white-paper text + figures, and a cleaned Discord transcript (`[timestamp] author: text`).
- `manual_extract_20260816_175931/` — raw Discord capture (JSON + media).
- `scripts/replay_50_20.py` — replays the 50/20-anchor Delta Bomb sequence on real ThetaData SPXW 5-min quotes (`~/Dev/central_trade_data/thetadata/lrrf_spxw_1550_5m_2026-08-10-v1/raw/greeks`). Run with `~/Dev/virtualenvs/gamma_chaser/bin/python scripts/replay_50_20.py 2025-09-17 --credit 0.50`.
- `docs/replay/` — replay outputs: three worked days (`examples.txt/json`) and the 102-day scan (`scan_50_20_2024_2025.csv`).
- `scripts/replay_variants.py` — eight planting sequences (serial anchor, anchor-bomb, long-first, ATM ladder, 3 parallel long/short ladders, fade) with day-P&L accounting; `--scan docs/replay/dayscan_2024_2025.csv --out …` for the cross-day table.
- `scripts/fetch_nvda_1m.py`, `scripts/nvda_load.py`, `scripts/nvda_replay.py` — NVDA 1-min ThetaData pull (Aug 3–14 2026, Aug-21 + Sep-18 expiries), loader, and the put/call leg-in replay; outputs in `docs/replay/nvda_*.csv`.
- `scripts/fetch_nvda_1m_range.py`, `scripts/nvda_cycles.py` — May–Aug 2026 NVDA 1-min pull (171 sessions across 6 expiries) and the multi-day buy-first cycle tracker (put and call).
