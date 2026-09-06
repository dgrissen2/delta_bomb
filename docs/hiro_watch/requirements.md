# Requirements — hiro_watch v2 (the clone route)

*v2.1, 2026-09-04. v2.0 + the $150 per-trade line removed from every bar (see W5.3 note). Replaces the
shadow-harness spec (retired; see `decision_clone_2026-09-04.md`). Written to be read in five minutes.*

## What this is

The frozen engine (`scripts/hiro_engine/`, CONFIG_HASH `80c3a41026c8…`) is the **baseline**. The
watch answers one question every evening: *would a small, pre-registered change to the rules have
done better on today's session?* — without touching the engine, without a second rule
implementation, and without letting the answer be edited after the data arrives.

A **candidate** is a config file. It is run through the engine (or a knob-added clone of the
engine) exactly as the baseline is run, producing its own event log stamped with its own
CONFIG_HASH. A **compare** script lays the candidate logs beside the baseline log and prints the
accounting; verdict lines appear only at checkpoints.

## W0. The one rule (everything else follows from it)

> A candidate is a yaml under `docs/hiro_watch/configs/`, committed to git **before its first
> confirmation session**. Its `watch.registered` date is the LAST session whose data was inspected
> when the candidate was defined (≤ the commit date; sessions after it are confirmation); its
> CONFIG_HASH on every log row is its identity; it is **never edited** once a confirmation session
> has been logged — any change after that is a new file with a new name and a new registration date.

Corollaries:
- **W0.1** `scripts/hiro_engine/` is never edited. The clone `scripts/hiro_engine_v2/` is edited
  once (knobs added, live code removed) and then frozen the same way.
- **W0.2** At v1-equivalent knob values the clone must reproduce the baseline log **byte-for-byte
  except `config_hash`** over every stored session. This is checked before any candidate exists and
  re-checked by a test.
- **W0.3** No silent skips: a session either runs fully for every candidate or the evening command
  fails with the reason. Duplicate session rows in a candidate log are an error, not a dedup.

## W1. The candidates (committed 2026-09-04; `registered` = 2026-09-02, the last session inspected)

| name | engine | change vs baseline | kind |
|---|---|---|---|
| `baseline_v2` | v2 | none (knobs at v1 values) — the W0.2 check | control |
| `credit030` | v1 | `r1v3_limits.credit: 0.30` | promotable |
| `a_depth_m4` | v2 | `r6_entries.a_r30_lt: -4.0` (Branch A signal only when r30 < −4 $B) | promotable |
| `diag_vt_off` | v2 | `r4_vetoes.vt_broken_enabled: false` | diagnostic — never promoted |
| `diag_levels_off` | v2 | `r4_vetoes.levels_invalid_enabled: false` | diagnostic — never promoted |
| `diag_late_off` | v2 | `r6_entries.late_enabled: false` | diagnostic — never promoted |

One change per candidate, never combined (attribution at n≈40 breaks otherwise). The credit
applies to both branches; results are read per branch off the log's `branch` column.

## W2. The clone (`scripts/hiro_engine_v2/`)

- **W2.1** A copy of `scripts/hiro_engine/` with four config knobs, each defaulting (in
  `baseline_v2.yaml`) to the v1-equivalent value: `r6_entries.a_r30_lt` (the A **signal** needs
  `r30 < a_r30_lt`; `0.0` is exactly v1's `r30 < 0`; applied in `a_fires`, NOT in `a_conditions`, so
  A episodes are numbered exactly as v1 numbers them), `r4_vetoes.vt_broken_enabled`,
  `r4_vetoes.levels_invalid_enabled`, `r6_entries.late_enabled` (all `true`). Read fail-closed.
- **W2.1a (2026-09-06) five Branch-B knobs**, all at v1-equivalent defaults: `r6_entries.b_enabled`
  (true), `b_run_max` (1e9 — Branch-B signal needs run ≤ this, $B), `b_dur_max` (1e9 — run age ≤ this,
  min), `late_sticky` (false — true keeps a LATE-suppressed episode suppressed), `r1v3_limits.credit_b`
  (= credit — the Branch-B resting credit; `credit` now applies to A only in v2). Plus the existing
  `b_pull_min_pts` (3.0) is a candidate knob. English meanings: `rules_in_english.md`.
- **W2.2** Removed from the clone: live loop, ops checks, spikes, parity, R9a registration, golden
  verify, sweep. The clone only backtests and scorecards. It never fetches chains (`fetch` raises;
  the daily loop populates the shared cache through v1).
- **W2.3** Subcommands: `backtest`, `scorecard`. Nothing else.

## W3. The evening command (`scripts/hiro_watch/run.py`)

- **W3.1** `run.py <date>`: for every yaml in `configs/`, run `python -m <engine> backtest --day
  <date> --config <yaml>` with the yaml's own log paths. Refuses (before running anything) if
  `<date>` already appears in any candidate's `sessions_backtest.csv`, or if the baseline has no row
  for `<date>`.
- **W3.2** `run.py --rebuild <name>|all`: delete the candidate's log dir and backtest every stored
  session in order. Candidate logs are deterministic outputs of (yaml, stored data) and may be
  rebuilt at any time; the baseline log is the only ledger.
- **W3.3** ≈ 3 s per candidate-session. Six candidates ≈ 20 s.

## W4. The compare (`scripts/hiro_watch/compare.py`)

Reads the baseline log(s) and every candidate log; prints, per candidate:
- **W4.1 Trades:** n signals / entries / fills (bombs), fill rate, net cash (credits + failed-attempt
  P&L), worst loss, MAE worst, minutes-to-fill median — per branch, split DISCOVERY | CONFIRMATION.
- **W4.2 Book:** every completed bomb still open, marked at the latest session's close (closing-NBBO
  mid of the spread × 100, capped at the width; `UNMARKED` if either leg has no valid closing quote);
  settled payoff for expired bombs (max(0, K_long − S_settle) − max(0, K_short − S_settle), S_settle =
  last regular-hours SPX 1-min close of expiry day); MTM = cash + marks + settlements. Baseline gets
  the same book. Quotes are pulled once per (date, expiry) and cached in
  `~/Dev/central_trade_data/thetadata/spxw_marks/`; a pull that stops before the close is refused,
  not cached. The `asof` session must itself be complete (bars to 16:00).
- **W4.3 Per-candidate detail:** `credit030` — baseline fills lost at 0.30 (join on setup);
  `a_depth_m4` — the Θ ladder {−1,…,−5} over baseline A signals (r30 parsed from the signal note)
  plus passed/rejected cohorts; `diag_*` — sole-blocker attribution: a refused baseline setup is
  scored only if the diag run actually entered it, and the other refusal reasons the same setup
  carried are shown. **Setup identity** = (session_date, branch, episode): one entry per episode
  (R11.1) and episodes are numbered identically in every candidate (W2.1). Signal minute is NOT part
  of the key — a candidate whose earlier trade was still open re-signals the same episode later.
- **W4.4 LB95:** completion lower bound = min(session-bootstrap 5th percentile, Clopper–Pearson),
  `DRAWS`/`SEED` imported from `hiro_engine.register`.

## W5. Firewall and checkpoints

- **W5.1** A session is DISCOVERY if its date ≤ the candidate's `watch.registered` date;
  CONFIRMATION if it is after that date, countable (baseline disposition `countable`) and among the
  first 40 such sessions; otherwise EXCLUDED (partial / event_standdown / post-terminal). Only
  CONFIRMATION rows feed a bar, a verdict, or an immediate path; EXCLUDED rows are shown, not counted.
- **W5.2** Verdict lines print only when the number of confirmation sessions is in {10, 20, 30, 40};
  otherwise `INCONCLUSIVE (n/next)`. The 40th is terminal: sessions after it are EXCLUDED and the
  40-session verdict stands. The ONLY immediate path (prints on the session it occurs) is a
  baseline fill lost at 0.30 (`credit030`). Every other REJECT/PROMOTE waits for a checkpoint.
- **W5.2a** Books used by a verdict are built on CONFIRMATION rows only: whole-portfolio for
  `a_depth_m4` (the gate's capacity spill into B is part of the candidate), branch-only for
  `credit030` (W1: read per branch). The all-sessions book is printed for context only.
- **W5.3 Bars (frozen with this file):**
  - `a_depth_m4` (passed = baseline confirmation A signals with r30 < −4): ≥ 20 confirmation A
    signals over ≥ 10 days AND ≥ 10 passed over ≥ 5 days, no day > 25 % of passed; passed completion
    LB95 > 0.55; passed cash + book per signal > baseline's per signal on the same sessions;
    candidate MTM ≥ baseline MTM → PROMOTE. REJECT: LB95 ≤ 0.55, or expectancy ≤ baseline, or
    candidate MTM < baseline MTM − credits earned. 40 confirmation A signals without either →
    REJECT-EXPIRED.
  - `credit030`, per branch: A — ≥ 15 confirmation baseline A fills, **zero** lost at 0.30
    (immediate REJECT otherwise), net cash ≥ baseline, MTM ≥ baseline → PROMOTE. B — same with
    ≥ 10 B entries and ≥ 5 baseline B fills.
  - **v2.1 note (2026-09-04, after confirmation session 1):** v2.0 carried "no trade P&L < −$150
    (immediate REJECT)" for both candidates and "no MAE < −$350" for credit030. Removed. The engine's
    exits are the 60-min clock and the 3.5-pt cap (≈ $350) and produce > $150 losses by design
    (3 of 14 discovery losers; 3 of 16 discovery winners were > $150 underwater before filling —
    `branch_accounting_2026-09-03.md` §7 rejected a $150 stop at −$870). Neither candidate changes
    an exit, so a per-trade loss line measures nothing about them and would have killed both on the
    first cap exit (it fired on credit030 on 09-03, on a trade the baseline took identically). This
    is a bar REMOVED after seeing one confirmation session, on the strength of discovery analysis
    that predates it; recorded here so it cannot be mistaken for tuning.
  - `diag_*`: never a verdict; table labeled INCONCLUSIVE until ≥ 20 refused episodes.
- **W5.4** A verdict comparing books requires both books fully marked; otherwise it defers and
  names the unmarked bombs.
- **W5.5** PROMOTE means "eligible for the R7.2 → spec-edit → R9a re-registration path". The watch
  changes nothing in the engine.

## Acceptance

- `pytest scripts/hiro_engine_v2/tests` green; a test asserts W0.2 on the stored sessions.
- `run.py --rebuild all` over the 16 stored sessions, then `compare.py` reproduces
  `branch_accounting_2026-09-03.md` §1 (baseline 29/16, A 22/13, B 7/3, realized −$1,050) and §7
  (`credit030` +$320, 13/13 A fills held).
- `run.py <date>` on a new session appends exactly one session to every candidate and refuses on a
  second invocation.
- `/code-review` round 1 (2026-09-04): 10 findings, all fixed in the same day
  (`build_notes.md` §"Review round 1").
