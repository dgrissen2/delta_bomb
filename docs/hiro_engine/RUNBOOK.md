# hiro_engine RUNBOOK — for the trader

*One page. What to type, what the console means, what to do on each banner.
PAPER ONLY — the engine never places orders; you hand-execute in the broker.*

## Morning (before 09:30 ET)

```bash
cd ~/Dev/delta_bomb
~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/ops/morning_check.py
```
Fix every **RED** before starting (ThetaData SDK creds at `~/Dev/ThetaData/creds.txt`
— no terminal needed — and Chrome with `--remote-debugging-port=9222` logged in
to dashboard.spotgamma.com). WARNs are
informational: missing levels row = engine trades long-first only today; empty
CPI/FOMC month = add the release dates to `docs/hiro_engine/event_calendar.csv`
(a wrong computed NFP Friday can be cleared with a row `date,none`).

Start the engine (add `--shakedown` for the first two sessions):
```bash
cd scripts && ~/Dev/virtualenvs/gamma_chaser/bin/python -m hiro_engine live
```

## Console lines — what they mean, what you do

| Line | Meaning | Your action |
|---|---|---|
| `BANNER … LEVELS MISSING → LONG-FIRST ONLY` | No valid SG levels row today (R4.2) | Only take Branch-A signals |
| `BANNER … EVENT DAY — STAND DOWN` | CPI/FOMC/NFP/opex/rebalance (R4.4) | No trades today, engine only logs |
| `SIGNAL A LONG-FIRST … nearest -0.20Δ put` | Buy the ~20Δ put NOW at market open of next bar; rest the SELL of K−5 at (cost+0.10) | Execute both tickets |
| `SIGNAL B SELL-FIRST …` | Sell the ~20Δ put at next open; rest the BUY of K+5 at (sale−0.10) | Execute both tickets |
| `ENTRY … S0=…` | The engine's simulated entry price (that bar's open) | Compare with your fill |
| `HEARTBEAT … clock Xm left` | Trade open; 60-min clock counting (R7.5) | Nothing |
| `EXIT fill` | Second leg deemed filled (±3.0 touch) | Confirm your resting order filled |
| `EXIT scratch` | Flow shut off / bounce-high broken — get out (R7.2) | Close the lone leg at market |
| `EXIT cap` | Leg moved 3.5 pts (option) / 15 SPX pts against (R7.3) | Close the lone leg NOW |
| `EXIT veto_exit` / `state_flip` | Flow veto fired / 13:00 read flipped against you (R7.4) | Close the lone leg |
| `EXIT timeout` | 60 minutes, no fill (R7.5) | Close the lone leg |
| `EXIT resolution_close` / `resolution_debit` | 15:30 hard resolution (R7.6) | Close, or complete the pair if debit ≤ 0.50 |
| `LATE — NO ENTRY` | Move too steep/late (R6.3) | Do NOT chase |
| `SKIP …` | Signal fired but blocked (one leg / 3-day cap / veto) | Nothing |
| `HIRO DOWN` | Feed lost: no new entries; cap/clock/resolution still guard the open trade (R10.1) | Watch your open leg manually |
| `scratch_unavailable` | Flow-based scratch can't be evaluated | Watch flow on the dashboard yourself |
| `RESUME WARNING` | Restarted state disagrees with the log | Stop; inspect `paper_log.csv` before trusting signals |
| loud `CONFIG_HASH CHANGED` block | Someone edited config.yaml | The 10-session test RESETS — only proceed deliberately |

Hard limits the engine enforces (R6.4): one unpaired leg at a time, ≤ 3
entries/day, one entry per episode, nothing new after 14:30, nothing survives
15:30.

## Crash mid-session

Just restart `python -m hiro_engine live`. It warm-replays today's bars,
rebuilds the open trade from the log, and continues. If you see
`RESUME WARNING`, stop and inspect.

## Evening (after 16:00 ET)

```bash
~/Dev/virtualenvs/gamma_chaser/bin/python scripts/hiro_engine/ops/evening_check.py
```
RED HIRO partition = run the backfill IMMEDIATELY (the vendor only retains ~5
sessions; a missed day is gone forever):
```bash
/Users/dgrissen/Dev/virtualenvs/HIRO_finder/bin/python -m hiro_tickers.historical_backfill --port 9222
```

## Grading

```bash
cd scripts && ~/Dev/virtualenvs/gamma_chaser/bin/python -m hiro_engine scorecard
```
Prints the full R9 table (PASS/FAIL/INCONCLUSIVE per criterion + overall).
Shakedown and PARTIAL sessions never count. Ten countable sessions of one
CONFIG_HASH complete the test. `--rehearsal` grades backtest sessions the same
way, labeled REHEARSAL.
