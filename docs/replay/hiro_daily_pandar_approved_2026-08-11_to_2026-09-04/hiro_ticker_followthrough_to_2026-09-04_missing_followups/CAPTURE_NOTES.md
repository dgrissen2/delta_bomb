# Recent missing-follow-up HIRO capture notes

The first merged Pandar-only audit found 18 recent approved tickers with no available session after their latest signal row. This capture filled those exact windows through September 4 using the authenticated port-9222 browser lease.

## Scope and integrity

- Input tickers: 18
- Requested windows: September 2–4 or September 3–4, depending on first uncovered signal
- Tickers completed: 18 of 18
- Request failures: 0
- Available ticker-sessions: 47
- Explicitly unavailable ticker-sessions: 0
- Provider rows: 1,319,879
- Raw JSON partitions: 47
- Normalized CSV partitions: 47
- Compact summary SHA-256: `3ef575c0367e5e4c3bce0cf99018775e40bb5f361328abe9daeefbe8949f1f98`

The collector ran one ticker at a time with randomized 6–12 second pauses, did not activate the page, and did not foreground Chrome. After merging this capture, every one of the 917 master signal rows has at least one available post-identification HIRO session.

## Git policy

The compact `summary.csv`, input window ledger, and these notes are committed. The 337 MB of raw/normalized provider data and local manifest are ignored.

## Reproduction

```bash
python /Users/dgrissen/.config/skillshare/skills/browser-pool/scripts/browser_pool.py \
  --ports 9222 -- \
  python scripts/hiro_single_name_backfill.py \
  --candidate-csv docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/missing_followups_hiro_windows.csv \
  --out-dir docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/hiro_ticker_followthrough_to_2026-09-04_missing_followups \
  --end-date 2026-09-04 \
  --pause-min-sec 6 \
  --pause-max-sec 12 \
  --retries 2 \
  --seed 20260904
```
