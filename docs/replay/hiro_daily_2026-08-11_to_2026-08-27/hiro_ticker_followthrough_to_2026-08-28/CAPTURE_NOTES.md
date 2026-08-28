# HIRO ticker follow-through capture notes

The authenticated capture ran on 2026-08-28 through a browser-pool lease on CDP port 9222.

It processed all 49 qualifying tickers serially. Each ticker used one range request followed by a randomized 8–14 second pause.

## Coverage

- Tickers completed: 49 of 49
- Requested ticker-sessions: 409
- Available ticker-sessions: 203
- Explicitly unavailable ticker-sessions: 206
- Provider rows: 5,689,121
- Zero-row tickers: GAP, LCID, PYPL, QS
- Series preserved: All, Next Expiry, Retail
- Session timezone: America/New_York

The August 28 session was partial at capture time. Older absent sessions are recorded as unavailable, never as zero flow.

## Git policy

The compact `summary.csv` is committed. The 409 raw JSON and normalized CSV partitions are local scraped-provider data and are excluded by `.gitignore`.

The local partition set occupies about 1.4 GB. Its resumable manifest remains local because it contains machine-specific absolute paths.

## Reproduction

Use the browser-pool wrapper and the authenticated SpotGamma browser on port 9222. The collector itself never activates or foregrounds Chrome.

```bash
/Users/dgrissen/Dev/virtualenvs/HIRO_finder/bin/python \
  /Users/dgrissen/.config/skillshare/skills/browser-pool/scripts/browser_pool.py \
  --ports 9222 -- \
  /Users/dgrissen/Dev/virtualenvs/HIRO_finder/bin/python \
  scripts/hiro_single_name_backfill.py \
  --candidate-csv docs/replay/hiro_daily_2026-08-11_to_2026-08-27/single_name_call_screen_candidates.csv \
  --out-dir docs/replay/hiro_daily_2026-08-11_to_2026-08-27/hiro_ticker_followthrough_to_2026-08-28 \
  --end-date 2026-08-28 \
  --port 9222 \
  --pause-min-sec 8 \
  --pause-max-sec 14 \
  --retries 2 \
  --seed 20260828
```
