# September 2 pending-signal HIRO gap-fill notes

The authenticated capture ran on 2026-09-04 through a browser-pool lease on CDP port 9222. MDB and PDD were September 2 buy-first put-tail inventory qualifiers whose follow-through was necessarily pending when the prior capture ended on September 2.

## Scope and integrity

- Input tickers: MDB, PDD
- Capture window: September 3–4
- Tickers completed: 2 of 2
- Request failures: 0
- Available ticker-sessions: 4
- Explicitly unavailable ticker-sessions: 0
- Provider rows: 112,354
- Raw JSON partitions: 4
- Normalized CSV partitions: 4
- Compact summary SHA-256: `889224dcafcdf58eaa1a136f9a56f07060eaec76212ca08fae7d6d86a6337087`

The collector ran one ticker at a time with randomized 6–12 second pauses and never foregrounded Chrome. All, Next Expiry, and Retail remain separate; missing data would be unavailable rather than zero.

## Git policy

The compact `summary.csv`, input window ledger, and these notes are committed. The 29 MB of raw/normalized provider data and local manifest are ignored.

## Reproduction

```bash
python /Users/dgrissen/.config/skillshare/skills/browser-pool/scripts/browser_pool.py \
  --ports 9222 -- \
  python scripts/hiro_single_name_backfill.py \
  --candidate-csv docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/pending_sep2_hiro_windows.csv \
  --out-dir docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/hiro_ticker_followthrough_to_2026-09-04_pending_sep2 \
  --end-date 2026-09-04 \
  --pause-min-sec 6 \
  --pause-max-sec 12 \
  --retries 2 \
  --seed 20260904
```
