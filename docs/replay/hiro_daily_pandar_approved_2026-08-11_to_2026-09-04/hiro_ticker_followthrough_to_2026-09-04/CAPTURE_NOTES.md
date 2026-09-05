# September 3 Pandar-only HIRO capture notes

The authenticated capture ran on 2026-09-04 through a browser-pool lease on CDP port 9222. The collector processed one ticker at a time, paused a randomized 6–12 seconds between names, used `navigate=False`, and never activated or foregrounded Chrome.

## Scope and integrity

- Input: all 107 September 3 surface qualifiers from the two-method Pandar-only scan
- Capture window: September 4, the first session after identification
- Tickers completed: 107 of 107
- Request failures: 0
- Available ticker-sessions: 107
- Explicitly unavailable ticker-sessions: 0
- Provider rows: 3,003,578
- Raw JSON partitions: 107
- Normalized CSV partitions: 107
- Compact summary SHA-256: `14a748b3d4dcbc619bb8629e27f9f42872d4cba4669047f171a0f7f0446befdc`

All, Next Expiry, and Retail are preserved separately because they overlap and must not be summed. Call and put components are retained. Session assignment uses America/New_York.

## Git policy

The compact `summary.csv` and these notes are committed. The 771 MB of local raw JSON and normalized CSV partitions are excluded by `.gitignore`. The resumable `manifest.json` is also ignored because it contains machine-specific absolute paths.

## Reproduction

```bash
python /Users/dgrissen/.config/skillshare/skills/browser-pool/scripts/browser_pool.py \
  --ports 9222 -- \
  python scripts/hiro_single_name_backfill.py \
  --candidate-csv docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/gap_2026-09-03/single_name_call_screen_candidates.csv \
  --out-dir docs/replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/hiro_ticker_followthrough_to_2026-09-04 \
  --end-date 2026-09-04 \
  --pause-min-sec 6 \
  --pause-max-sec 12 \
  --retries 2 \
  --seed 20260904
```
