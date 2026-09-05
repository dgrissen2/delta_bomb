# Pandar-approved single-name master through 2026-09-04

## Outcome

The master contains **917 surface-qualified ticker/date rows across 164 tickers**, and only the two narrowly approved Pandar lanes. Exact historical chains confirmed **81 rows across 24 tickers**. September 4 is present in the coverage ledger as **provider unavailable** because ORATS had not published that completed session; it is not counted as a zero-signal day.

| Pandar-approved lane | Surface rows | Exact-chain rows | What is actually Pandar-direct |
|---|---:|---:|---|
| buy-first put-tail inventory | 893 | 75 | Cheap far-OTM 1:1 put-vertical inventory, usually about $5 wide and under $0.10; recycle and roll. The rank gates, fixed OTM band, complete-at-entry rule, and universal exits are mechanized. |
| sell-first call grab | 24 | 6 | The call-tail sale/crush core only: sell unusually overpriced far-OTM front-weekly calls and size for a strike touch. The systematic conversion and numeric screen are derived. |

Buy-first call puke and buy-first call standard are intentionally absent from every master artifact.

## Session coverage

Each evaluated cell is `surface-qualified / exact-chain-confirmed`.

| Date | Call grab | Put inventory | Status |
|---|---|---|---|
| 2026-08-11 | 1/0 | not in scope | evaluated |
| 2026-08-12 | 2/0 | not in scope | evaluated |
| 2026-08-13 | 2/0 | not in scope | evaluated |
| 2026-08-14 | 0/0 | not in scope | evaluated |
| 2026-08-17 | 2/0 | not in scope | evaluated |
| 2026-08-18 | 0/0 | not in scope | evaluated |
| 2026-08-19 | 2/1 | not in scope | evaluated |
| 2026-08-20 | 3/1 | not in scope | evaluated |
| 2026-08-21 | 3/1 | not in scope | evaluated |
| 2026-08-24 | 3/1 | 89/7 | evaluated |
| 2026-08-25 | 2/0 | 92/8 | evaluated |
| 2026-08-26 | 0/0 | 102/7 | evaluated |
| 2026-08-27 | 1/0 | 92/7 | evaluated |
| 2026-08-28 | 1/0 | 107/7 | evaluated |
| 2026-08-31 | 1/1 | 110/12 | evaluated |
| 2026-09-01 | 0/0 | 96/6 | evaluated |
| 2026-09-02 | 0/0 | 99/11 | evaluated |
| 2026-09-03 | 1/1 | 106/10 | evaluated |
| 2026-09-04 | unavailable | unavailable | ORATS unavailable |

## Newly filled September 3 exact confirmations

| Ticker | Method | RR | IV | Exact contract | 09-04 All HIRO |
|---|---|---|---|---|---|
| AMZN | buy-first put-tail inventory | 14.7 | 32.2 | BTO 09-18 190/185P ≤$0.02 | $+0.46bn |
| BE | buy-first put-tail inventory | 15.9 | 7.3 | BTO 09-18 135/130P ≤$0.04 | $+0.00bn |
| BMNR | buy-first put-tail inventory | 24.2 | 14.8 | BTO 09-18 19/14P ≤$0.05 | $+0.00bn |
| CRWV | buy-first put-tail inventory | 7.9 | 2.8 | BTO 09-18 47.5/42.5P ≤$0.02 | $+0.07bn |
| GOOG | buy-first put-tail inventory | 7.9 | 18.2 | BTO 09-18 240/235P ≤$0.04 | $-0.14bn |
| MRVL | buy-first put-tail inventory | 15.5 | 23.1 | BTO 09-18 125/120P ≤$0.05 | $+0.14bn |
| MSFT | buy-first put-tail inventory | 23.0 | 31.2 | BTO 09-18 350/345P ≤$0.03 | $-0.43bn |
| NBIS | buy-first put-tail inventory | 20.6 | 16.2 | BTO 09-18 125/120P ≤$0.06 | $+0.08bn |
| NVDA | buy-first put-tail inventory | 13.9 | 8.8 | BTO 09-18 155/150P ≤$0.02 | $+0.26bn |
| RTX | buy-first put-tail inventory | 6.0 | 23.9 | BTO 09-18 120/115P ≤$0.03 | $-0.00bn |
| MSTR | sell-first call grab | 0.0 | 50.4 | STO 09-11 190C ≥$0.25; rest BTO 185C $0.15 | $+0.02bn |

## HIRO coverage and interpretation

The compact HIRO ledger contains **896 available ticker-sessions across 164 approved tickers** after deduplication. The new capture added September 4 for all 107 September 3 surface qualifiers; a separate gap fill added September 3-4 for the previously pending MDB and PDD signals; a final 18-ticker pass filled every remaining recent post-signal coverage hole.

`pandar_approved_hiro_daily_metrics.csv` reports regular-session 09:30-16:00 America/New_York signed estimated delta-notional flow. `all`, `nextExp`, and `retail` overlap and remain separate; never sum them. Call and put components are retained, and unavailable provider sessions stay unavailable rather than becoming zero.

## Audit trail

- ORATS calls: **337 / 500**; 163 remained. Attempts include the two successful calendar checks that established September 4 was not yet published.
- Surface rows are screen candidates; only rows with `chain_confirmed=true` had a qualifying historical spread in the captured chain.
- The August 11-27 call-tail rows use the frozen original scan. The August 24-September 2 put rows and August 28-September 2 call-tail rows use the refreshed four-method scan. September 3 uses the Pandar-only gap run.
- HIRO-universe snapshot: 398 tickers; SHA-256 `09fd8d6740d2ae8fdc45189f9d9484cdeb688f551cd2fcef554ef73534ba14df`.

## Master artifacts

- `pandar_approved_master.csv`: every surface-qualified Pandar-only ticker/date row, its attribution boundary, exact-chain result, contract fields, and post-signal HIRO coverage.
- `pandar_approved_exact_confirmations.csv`: executable historical-chain subset; repeated qualifying dates are preserved.
- `pandar_approved_daily_tickers.csv`: every in-scope session/method, including zero rows, not-in-scope dates, and September 4 provider-unavailable status.
- `pandar_approved_hiro_daily_metrics.csv`: deduplicated RTH HIRO totals by ticker/session/scope with call and put components.
- `gap_2026-09-03/`: frozen Pandar-only surface, chain checks, exact finalists, and summaries for the newly filled signal date.
- `hiro_ticker_followthrough_to_2026-09-04/`: local raw/normalized September 4 HIRO capture plus committed compact summary and notes.
- `hiro_ticker_followthrough_to_2026-09-04_pending_sep2/`: local MDB/PDD September 3-4 gap fill plus committed compact summary and notes.
- `hiro_ticker_followthrough_to_2026-09-04_missing_followups/`: local 18-ticker recent completeness pass plus committed compact summary and notes.
