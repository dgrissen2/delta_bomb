# HIRO four-method inventory capture notes

The authenticated capture ran on 2026-09-03 through a browser-pool lease on CDP port 9222. The collector processed one ticker at a time, paused a randomized 8–14 seconds between names, and never activated or foregrounded Chrome.

## Scope

- Current four-method surface qualifiers: 167 unique single stocks
- Prior HIRO inventory: 49 tickers through 2026-08-28
- Union: 183 tickers
- Eligible for a completed post-signal session through 2026-09-02: 179 tickers
- Pending because first identified on 2026-09-02: MDB, PDD, PFE, QBTS
- Capture rule: prior inventory restarted after 2026-08-28; new inventory started on the calendar day after its first signal

## Coverage and integrity

- Tickers completed: 179 of 179
- Request failures: 0
- Requested ticker-sessions: 932
- Available ticker-sessions: 650
- Explicitly unavailable ticker-sessions: 282
- Provider rows: 18,230,251
- Raw JSON partitions: 932
- Normalized CSV partitions: 932
- Zero-row tickers: BYND, LCID, QS
- Series preserved separately: All, Next Expiry, Retail
- Session timezone: America/New_York
- Compact summary SHA-256: `ac3cfc521349c85f2853e85391dc0caef3818899cecc18074b07a4df391ef59b`
- Inventory-window SHA-256: `d4fb8afd96bb25480ea80c8a8c05c526c2388252c0cdcaad6a044a64b2614c02`

Older absent sessions are recorded as unavailable, never as zero flow. All, Next Expiry, and Retail overlap and must not be summed.

## Git policy

The compact `summary.csv` and these notes are committed. The 4.6 GB of raw JSON and normalized CSV partitions remain local scraped-provider data and are excluded by `.gitignore`. The resumable `manifest.json` also remains local because it contains machine-specific absolute paths.

## Reproduction

```bash
/Users/dgrissen/Dev/virtualenvs/HIRO_finder/bin/python \
  /Users/dgrissen/.config/skillshare/skills/browser-pool/scripts/browser_pool.py \
  --ports 9222 -- \
  /Users/dgrissen/Dev/virtualenvs/HIRO_finder/bin/python \
  scripts/hiro_single_name_backfill.py \
  --candidate-csv docs/replay/hiro_daily_four_methods_2026-08-24_to_2026-09-02/single_name_call_screen_candidates.csv \
  --prior-summary docs/replay/hiro_daily_2026-08-11_to_2026-08-27/hiro_ticker_followthrough_to_2026-08-28/summary.csv \
  --prior-end-date 2026-08-28 \
  --out-dir docs/replay/hiro_daily_four_methods_2026-08-24_to_2026-09-02/hiro_ticker_followthrough_to_2026-09-02 \
  --end-date 2026-09-02 \
  --port 9222 \
  --pause-min-sec 8 \
  --pause-max-sec 14 \
  --retries 2 \
  --seed 20260903
```
