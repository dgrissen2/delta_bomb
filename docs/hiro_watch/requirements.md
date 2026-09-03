# Requirements — Shadow-Candidate Watch ("hiro_watch")

*v1.2a — 2026-09-03. v1.2 + design-review alignment (code lineage recorded at snapshot-manifest granularity, W8.3; isolated W5 replays are diagnostic and capped while the portfolio layer replays every refused setup, W5.2; `hiro_health`/`option_quotes_health` derived from the engine's single health state, W2.6; no snapshot pruning). v1.2 = v1.1 + review round 2 (FAIL 18/9 → applied: code identity split from WATCH_HASH, snapshot-directory atomic commit, all replay inputs pinned by sha, session calendar, SPY input, MAE sign, episode/disposition field names, candidate cash from replay outputs, candidate opportunity ledger, A-DEPTH economics formula, verdict checkpoints, regime representation, scale-monitor constants registered, LB95 boundary rule, branch-isolated credit variants, absolute loss/MAE limits for CREDIT, sole-blocker attribution for W5, marks-completeness gate, eligibility enums, settlement provenance, test list). Round-2 residuals accepted as design-level (fill-quality realism is the engine's frozen R1.4d physics, parity-gated live; not re-litigated here). v1.1 = v1.0 + round 1 (FAIL, 25 findings → all applied; `requirements_review_2026-09-03.md`): hash canonicalization + code binding, minimum passed cohorts and explicit REJECT paths, positive-expectancy bar, LB95 bootstrap defined, portfolio (sequential) replay as the verdict basis with isolated replays demoted to diagnostic, setup identity + reason precedence, NaN/health rules, settlement formula, mark-quality controls, atomic commits, chronological processing, r30 scale-drift monitor, per-candidate shadow book, scenario grid, test list. Prior: v1.0 product-owner pass (product-operating-partner lens; no product-manager persona
exists in the global stores — noted, not fabricated). Motivation: the Charlie McElligott / codex review
of the first seven out-of-sample sessions (`../hiro_engine/charlie_oos_review_2026-09-02.md`) and the
full-book accounting (`../hiro_engine/branch_accounting_2026-09-03.md`) ordered a WATCH: a set of
shadow rules that are scored on every new session WITHOUT touching the frozen engine, each with a
pre-registered definition and evidence bar, so that candidate improvements earn or lose their place on
fresh data instead of being fitted to the sessions we have already looked at. This document is the
PM spec for that watch. It is self-contained: every rule the watch scores is stated here with a
W-number; acceptance criteria reference W-numbers only. The frozen engine's rules are referenced by
their R-numbers in [`../hiro_engine/requirements.md`](../hiro_engine/requirements.md) v3.0 and are
NEVER restated or modified here.*

## User Story

As the **trader running the frozen hiro_engine paper test**,
I want **a separate, read-only "watch" that, after every session, replays the day's signals under a
small pre-registered set of candidate rules — a Branch-A flow-depth gate, a wider-credit ladder, and the
sell-first signals the safety rules refused — and keeps a running, session-clustered ledger of what each
candidate would have done, with a fixed evidence bar per candidate**,
So that **when a candidate finally clears its bar it is promoted on out-of-sample evidence I could not have
fitted, and when it fails it is dropped — without me ever editing the live rules mid-test or fooling
myself with the sessions I have already inspected**.

## Scope

- **In:** a per-session regime panel for every signal (fired, entered, or refused); three shadow
  candidates (W3, W4, W5) with frozen definitions and evidence bars; book reporting that separates
  realized cash from the open-bomb inventory (W6); a discovery/confirmation firewall (W7); a hashed
  registration for the watch itself (W8); one report command (W9); deterministic re-runs.
- **Out:** ANY change to the frozen engine's behavior, config, or CONFIG_HASH; order placement; new
  entry/exit rules beyond the three registered candidates; parameter search or "optimization" over
  thresholds not listed in W3/W4; live (intraday) evaluation — the watch runs on completed sessions only.

---

# Part 1 — The Watch (normative)

## W0. Hard constraints (P0 — violating any of these voids the watch's evidence)
- **W0.1 Shadow only.** The watch reads the engine's outputs and data caches and writes ONLY its own
  ledger files. It never imports mutable engine state, never writes to the engine's logs, config, or
  registration, and never changes what the engine prints. The engine's CONFIG_HASH (`80c3a41026c8…`)
  is unchanged by the existence or execution of the watch.
- **W0.2 Contemporaneous inputs only.** Every variable the watch uses to classify a signal must be
  observable at that signal's minute from the same feeds the engine had (R2). Full-day labels
  ("falling day", "day low", "rally day") are forbidden as inputs; they may appear only as
  descriptive columns clearly marked `post_hoc_`.
- **W0.3 Same execution physics as the engine.** Every counterfactual fill, exit, and P&L uses the
  engine's own definitions: closing-NBBO conservative bookings (R7.0), limit marketability on the
  option's 1-min NBBO from signal+2 (R1.4d), the 60-min clock (R7.5), the 3.5-pt cap (R7.3), the
  15:30 resolution (R7.6), B's flow-shutoff scratch (R7.2), veto/state-flip exits (R7.4). The watch
  may not invent a cheaper fill or a kinder exit.
- **W0.4 Nothing is skipped silently.** A session missing any required input (W1) is REFUSED with the
  missing items listed; a partial ledger is never written.
- **W0.5 Frozen definitions.** Candidate definitions, thresholds, and evidence bars are fixed in W3–W5
  and hashed (W8). Changing any of them is a re-registration: new hash, evidence counters reset to
  zero, and the previous ledger retained read-only.

## W1. Inputs (all existing; the watch adds no data source)
- **W1.1** The engine's event logs for the session (`paper_log_*.csv`, schema v2 per R8.1): every
  `signal`, `skip`, `gate_fail`, `late_no_entry`, `entry`, `fill`, `limit_canceled`, `exit`, `banner`,
  `disposition`, `veto_change` row.
- **W1.2** The session's option-chain cache (`spxw_bomb_chains/date=<D>/chain_1m.parquet`, R2.5) —
  the same file the engine replayed — with its manifest sha verified at load.
- **W1.3** SPX 1-min bars, the HIRO partition (identity-verified per the evening ops guard), and the
  SpotGamma levels row for the session (R2.1–R2.3) — needed to recompute the regime panel (W2) and
  to replay refused B signals (W5).
- **W1.3a** SPY 1-min OHLCV (R2.4; `spy_parquet`) when available — the engine's context read and
  state-flip exit depend on it; when absent the engine ran DEGRADED_VWAP and the shadow replays run
  the same way (the log's `health` column says which).
- **W1.4** The engine's `registration.json` (R9a), `config.yaml`, and `sessions_backtest.csv` /
  `sessions.csv` (the disposition ledger: columns `date, disposition, outage_min, mode, config_hash`)
  — read-only, used to stamp the ledger with the CONFIG_HASH and to label countability (W7.1).
- **W1.6 Input identity.** Every replay input is pinned per session in the ledger: chain cache sha
  (from the chain manifest), SPX parquet sha256, SPY parquet sha256 (or `absent`), HIRO normalized
  CSV sha256 (from the HIRO manifest), levels row bytes sha256 (or `absent`), engine log sha256,
  and the event-calendar sha256. A re-run whose inputs differ from the pinned shas refuses (W9.4)
  — byte-identity is only meaningful over identical inputs.
- **W1.7 Session calendar.** The authoritative list of trading sessions is the engine's disposition
  ledger (W1.4) — every session the engine ran. A trading day with no disposition row is a MISSING
  session and `watch <date>` refuses until it is replayed (W9.3); the NYSE calendar in
  `docs/hiro_engine/event_calendar.csv` + weekday rule is used only to DETECT such gaps.
- **W1.5** For terminal P&L (W6.4): the SPX settlement close on each bomb's expiry date (SPXW
  PM-settled: the 16:00 bar close of the expiry session from W1.3's store).

## W2. Regime panel — one row per signal event, fired OR refused
- **W2.1** Population: every `signal` row AND every refused sell-first/buy-first setup (`skip` with
  reason vt_broken / levels_invalid / 3-entries-per-day / one-unpaired-leg, `late_no_entry`,
  `gate_fail`) in the session, keyed (session_date, minute, branch).
- **W2.2** Columns, all computed at the signal minute from the engine's own R3 features (recomputed by
  the watch from W1.3 with the engine's feature module, never hand-rolled): `r15`, `r30`,
  `flow_accel` = r15 − (r30 − r15) (last 15 min vs the 15 before), `run`, `rate`, `share`,
  `weak_side`, `pull30`, `bounce30`, `range60`, `range60_p75`, `close_minus_mid30`,
  `close_minus_open0930`, `ret_prior30` (close − close 30 bars ago), `vt_state` (above/below),
  `vt_distance_pts`, `levels_valid`, `signal_min`, `context_read` (10:30/13:00 state per R3.4),
  `hiro_health`, `option_quotes_health`.
- **W2.3** For entered trades, appended after the trade closes: `entry_min`, `leg1_fill`, `limit_L`,
  `outcome` (fill/timeout/scratch/cap/veto_exit/state_flip/resolution_close/censored),
  `minutes_to_fill`, `mae_usd` (max adverse mark of the lone leg at the conservative NBBO side,
  entry→exit), `mfe_usd`, `pnl_usd` — all from the engine's log, not recomputed.
- **W2.4** Post-hoc descriptive columns are permitted only with the prefix `post_hoc_` (e.g.
  `post_hoc_session_return`). Firewall, stated precisely: a candidate's **classifier** (the rule that
  decides pass/reject or the limit price BEFORE the outcome is known) may reference only W2.2
  columns and the registered constants; a candidate's **scorer** may additionally use W2.3 outcomes,
  the chain caches, refusal reasons, and replay results. The registration file declares each
  candidate's `classifier_columns` (validated ⊆ W2.2 at `watch register`) and `scorer_inputs`.
- **W2.5 Identity & dedup.** Every panel row has `setup_id = (session_date, branch, signal_min,
  episode_id)` from the engine's R3.5 episode tracker. One episode can emit several engine rows
  (`gate_fail` then `skip`, or `late_no_entry` and `skip` in the same minute); the panel keeps ONE
  row per setup_id with `refusal_reason` chosen by precedence **vt_broken > levels_invalid > late >
  gate_fail > capacity(3/day, one-unpaired-leg) > none(entered)** and `refusal_reasons_all` listing
  every reason seen.
- **W2.6 Units, enums, nullability.** $B for `r15/r30/flow_accel/run/pull30/bounce30`; $B/hr for
  `rate`; fraction [0,1] for `share`; SPX points for `range60/range60_p75/close_minus_*/ret_prior30/
  vt_distance_pts`; `weak_side` = min(dC, dP) in $B; `vt_state ∈ {above, below, at, invalid}` ("at" =
  close == VT; "invalid" when levels_valid is false); `context_read ∈ {UP, DOWN, CHOP, NONE}`;
  `hiro_health ∈ {OK, DEGRADED_VWAP, HIRO_DOWN}`, `option_quotes_health ∈ {OK, OPTION_QUOTES_DOWN}`;
  `outcome` enum per R7 plus `censored`, `data_invalid`, `entry_aborted`; `mae_usd` = the most
  NEGATIVE conservative-side mark-to-market of the lone leg (long leg at bid, short leg at ask)
  relative to leg-1 fill, from the entry bar through the exit-decision bar inclusive, in $ (×100),
  so MAE ≤ 0 always (a trade that was never under water has MAE = 0); `mfe_usd` is the symmetric
  most-positive mark (≥ 0). Both are computed by the watch from the chain cache (the engine logs
  only `liq-loss` heartbeats, which are not minute-complete) and reconciled against the engine's
  logged `adverse` (SPX points, context only) by sign. `minutes_to_fill` is null unless
  `outcome = fill`. "Completion" ≡ `outcome = fill`. `episode_id` = the engine's `episode` column
  (R3.5 tracker id, per branch).
- **W2.7 NaN / health rule.** A signal whose classifier input is NaN (e.g. `r30` before warm-up) is
  labeled `unclassifiable` and counted in its own column — never as passed, never as forgone. A
  replayed episode that hits the engine's R10.4 quote-gap rule becomes `data_invalid` and is
  reported, not scored (the engine's own convention). Crossed or non-positive NBBOs are invalid
  quotes per R10.4 and never used for marks or fills.
- **W2.8 Scale monitor (report-only; constants registered in W8.1).** `r30_scale(D)` = median of
  |r30| over all minutes in [10:30, 13:00] of the 20 stored sessions strictly before D that have a
  countable disposition and non-NaN r30 for ≥ 100 of those minutes (fewer than 10 such sessions →
  monitor `INSUFFICIENT`, verdicts NOT withheld). `r30_scale_ref` = the same statistic over the 16
  discovery sessions, frozen at registration. If `r30_scale(D) / r30_scale_ref` is outside
  [0.5, 2.0] on the current session, A-DEPTH prints `SCALE_DRIFT` for that session and its verdict
  checkpoint (W3.5) is deferred to the next checkpoint. NaN/zero r30 minutes are excluded from the
  median; the direction of drift is printed.

- **W2.9 Candidate opportunity ledger.** Each portfolio replay (W3b, W4b, W5b) emits its own panel
  with the same schema and `setup_id` rule, plus `candidate_id` and `in_baseline` (true iff the same
  setup_id exists in the baseline panel). Opportunities that exist only under the candidate (freed
  capacity) are counted, clustered, and scored in the candidate's tables; they are never mixed into
  the baseline tables. **Eligibility enum** (`eligibility ∈ {scored, unclassifiable, data_invalid,
  censored, entry_aborted, capacity_blocked, safety_blocked, late_blocked, gate_failed}`): only
  `scored` rows enter rates and count bars; every other value is tallied in its own column.

## W3. Candidate A-DEPTH — Branch-A flow-depth shadow gate (R7.2 candidate (1) lineage, redefined)
- **W3.1 Definition.** For every Branch-A `signal` row, the gate PASSES iff `r30 ≤ θ` at the signal
  minute, for each θ in the registered ladder **Θ = {−1.0, −2.0, −3.0, −4.0, −5.0} $B**. The PRIMARY
  registered threshold is **θ* = −4.0 $B** (the only bucket that was 5/5 on the discovery data;
  `branch_accounting_2026-09-03.md` §4). The ladder exists to show the shape of the response — it is
  NOT a search: no θ outside Θ is ever computed, and θ* is fixed before the first confirmation session.
- **W3.2 No r15 clause in v1.** The review split on whether r15 belongs in the gate; the registered
  candidate is r30-only. r15 is REPORTED beside every row (W2.2) so a later, separately registered
  candidate can be defined from it — it is not part of this one.
- **W3.3 Scoring — two layers.** (a) DIAGNOSTIC (isolated): for each θ, over CONFIRMATION sessions,
  classify every A signal passed/rejected/unclassifiable and attribute its ACTUAL engine outcome
  (W2.3) — this shows the shape of the response. (b) **VERDICT (portfolio):** a chronological
  shadow-engine replay of each confirmation session with the gate ACTIVE at θ* (the engine's own
  rules, run read-only with the candidate injected — design decides the mechanism), so that capacity
  effects (one-unpaired-leg, 3/day) and later-setup eligibility are real. All W3.4 quantities come
  from layer (b). Both layers print; (a) is labeled DIAGNOSTIC. **Economics, defined:** per-signal
  expectancy of a cohort = (Σ credits + Σ failed-attempt P&L + Σ settled payoffs + Σ open-inventory
  `mark_liq_usd` at the checkpoint session's close) ÷ (number of `scored` signals in the cohort);
  every cash term comes from the REPLAY's own trades (never the baseline log) for candidate cohorts,
  and from the engine log + baseline book for the baseline cohort; "forgone" = the baseline trades
  whose signals the gate rejected, valued the same way.
- **W3.4 Evidence bar for θ* (frozen).** Counts, all on the confirmation set: ≥ 20 Branch-A signals
  overall across ≥ 10 signal-days AND ≥ 10 PASSED signals across ≥ 5 passed-days with no single
  day > 25% of the PASSED cohort (denominator = passed). Economics (portfolio replay): completion
  LB95 (W6.5) of the passed cohort > 0.55; passed net expectancy per signal > 0 AND > the baseline
  engine's per-signal expectancy on the same sessions; the candidate's total-book MTM (W6.7) ≥ the
  baseline book's on the same sessions; no passed loss < −$150. All hold → **PROMOTE**.
  **REJECT** paths (any one, once the count bars are met): completion LB95 ≤ 0.55; passed expectancy
  ≤ 0; any passed loss < −$150 (immediate, count bars not required); candidate book MTM < baseline
  by more than the sum of credits it earned. **EXPIRE:** 40 confirmation A signals without PROMOTE
  or REJECT (e.g. concentration never satisfied) → `REJECT-EXPIRED`. Otherwise INCONCLUSIVE.
  Promotion means "eligible for the R7.2 → spec-edit → R9a re-registration path"; the watch itself
  promotes nothing into the engine.
- **W3.5 Verdict checkpoints (multiple-testing control).** Progress lines print every session, but
  a VERDICT for any candidate is COMPUTED only at checkpoints: every 10th countable confirmation
  session (10, 20, 30, 40). Between checkpoints the status is INCONCLUSIVE(progress). The immediate
  REJECT paths (a passed loss < −$150; a baseline fill lost at c) are the only exceptions — they
  fire on the session they occur. Maximum 4 checkpoints per registration; the 4th is terminal.
- **W3.6 Regime representation.** The PASSED cohort at a checkpoint must include signals from ≥ 2
  above-VT sessions AND ≥ 2 below-VT sessions (`vt_state` at the signal minute) and from ≥ 3
  distinct ISO weeks; otherwise the checkpoint prints `UNREPRESENTED` and defers.
- **W3.7 Marks completeness.** Any verdict condition comparing candidate and baseline books is
  evaluated only if BOTH inventories are fully marked (no UNMARKED bomb) at the checkpoint close;
  otherwise the checkpoint defers and prints which bombs are unmarked.

## W4. Candidate CREDIT — per-branch resting-limit credit ladder (R7.2 candidate (3) lineage, extended to B)
- **W4.1 Definition — two layers.** (a) DIAGNOSTIC (isolated): for every ENTERED trade, replay the
  second leg at leg1 ∓ c for each c in **C = {0.10, 0.20, 0.30}** (tick-rounded against us, R1.4c;
  fill = minute closing-NBBO marketable from signal+2, R1.4d) with recorded flow exits held fixed —
  the quick per-trade Δ table. c = 0.10 must reproduce the engine's actual outcome and fill minute
  exactly (self-check, W9.4). (b) **VERDICT (portfolio):** chronological shadow-engine replay of each
  confirmation session with `rest_offset = c` active, so that a leg still resting after the baseline's
  fill minute is managed minute-by-minute by the engine's full exit set (scratch / veto / state-flip /
  cap / clock / resolution recomputed, not assumed) and capacity effects are real.
- **W4.2 Scoring, per branch and per c (layer b, with layer a beside it):** n_trades, fills, fill-rate
  LB95, median minutes-to-fill, naked-leg minutes (median and max), MAE, net P&L (credits + failed-
  attempt losses), worst loss, candidate book MTM (W6.7), and Δ vs c = 0.10.
- **W4.1a Branch isolation.** Each CREDIT variant is (branch, c): the shadow run applies c to the
  target branch's resting leg ONLY; the other branch rests at the frozen 0.10. Four portfolio
  replays per session: (A,0.20), (A,0.30), (B,0.20), (B,0.30).
- **W4.3 Evidence bars (frozen), one verdict per (branch, c).** Branch A at c: ≥ 15 confirmation-set
  baseline A fills, of which **zero** are lost at c (R7.2(3)'s bar); median naked-leg minutes at
  c ≤ 1.5 × baseline; **no trade at c with P&L < −$150** (absolute; replaces the earlier relative
  allowance); **no trade at c with MAE < −$350** (the frozen cap, so the candidate never widens the
  engine's tail); net P&L at c ≥ baseline; candidate book `mark_liq_usd` ≥ baseline's (W3.7 gate)
  → PROMOTE. REJECT for that c if any baseline fill is lost at c, or any trade at c breaches the
  −$150 line (immediate paths, W3.5), or at a checkpoint net P&L at c < baseline. Branch B at c:
  ≥ 10 confirmation-set B entries AND ≥ 5 baseline B fills before any verdict; identical conditions.
  B evidence never pools into A's. Verdicts obey the W3.5 checkpoints.

## W5. Candidate B-REFUSED — counterfactual score of the sell-first signals the safety rules blocked
- **W5.1 Population.** Every Branch-B setup the engine refused for **vt_broken (R4.1)** or
  **levels_invalid (R4.2)**, plus those suppressed as **LATE (R6.3)**, grouped by refusal reason.
  Setups refused for capacity (3/day, one-unpaired-leg) are reported but scored separately: they were
  refused by structure, not by a safety rule.
- **W5.2 Replay — two layers.** (a) DIAGNOSTIC (isolated, causal): each refused setup_id is entered
  as the engine would have entered it (sell the nearest −0.20Δ put at the next bar's closing bid, rest
  the K+5 buy at sale − 0.10) and run under the FULL B exit set of W0.3 with the flow-shutoff scratch
  and flow-veto exits recomputed from the session's HIRO features. (b) PORTFOLIO: a chronological
  shadow-engine replay of the session with the refusing rule disabled (vt_broken for the R4.1 table,
  levels gate for the R4.2 table, late suppression for the R6.3 table — one rule per table, never
  combined), so that one-unpaired-leg, 3/day, and competing signals are enforced. Headline numbers
  come from (b); (a) is labeled DIAGNOSTIC. **Sole-blocker attribution:** a setup is scored in a
  reason's table only if, with that ONE rule disabled, the shadow engine actually ENTERS it; a setup
  still blocked by another rule is tallied `multi_blocked` (with the remaining reasons) and not
  scored. `levels_invalid` episodes: the shadow disables only the R4.2 short-block; everything else
  runs exactly as the engine ran that day with its actual inputs (whatever context read R3.4
  produced from the inputs it had — the watch forces nothing) — flagged `levels_valid = false`.
  Output per episode: fill?, minutes-to-fill, outcome, P&L, MAE, naked-short minutes (entry →
  fill/exit), `data_invalid` if R10.4 fires.
- **W5.3 Scoring.** Per refusal reason and per layer: episodes, fills, fill-rate LB95, net P&L,
  worst loss, total and max naked-short minutes, share of episodes with MAE < −$150, and the
  counterfactual book (W6.7) of the portfolio layer vs the baseline book.
- **W5.4 No promotion rule.** R4.1/R4.2 are safety rules; the review's instruction is to PRESERVE
  them and SCORE the counterfactual. The watch reports; it does not propose relaxing a safety rule.
  Reporting threshold: the table is labeled INCONCLUSIVE until ≥ 20 refused episodes exist.

## W6. Book reporting (every session, cumulative)
- **W6.1 Realized cash:** credits banked and failed-attempt losses, by branch and by set
  (discovery / confirmation), from the engine's logs — never recomputed.
- **W6.2 Inventory:** every completed bomb still open, marked at the session's closing NBBO of BOTH
  legs from the chain caches (W1.2). A needed expiry absent from that day's cache is pulled ONCE via
  the engine's ChainStore, persisted into the watch's own mark cache (`docs/replay/hiro_watch/marks/
  <date>_<expiry>.parquet`, sha recorded in the book row) and never re-pulled — determinism (W9.4)
  reads the persisted file. **Mark quality:** a leg's mid is usable only if the quote is valid (R10.4)
  AND spread ≤ max(0.50, 5% of mid); otherwise use the last usable quote within 3 minutes of the
  close, else the bomb is `UNMARKED` for that session (reported, excluded from the MTM sum, never
  estimated). Two marks per bomb: `mark_mid_usd` and `mark_liq_usd` (executable liquidation: long
  leg at bid, short leg at ask). Concentration by expiry and by strike band; inventory max drawdown
  since planting on `mark_liq_usd`.
- **W6.3 Common-horizon P&L:** realized + inventory mark at the session close = MTM, reported WITH
  the caveat line "inventory is one correlated position: N bombs, expiries E1..Ek, strikes S1..Sn".
- **W6.4 Terminal P&L:** on the EXPIRY session itself, after its close, each bomb expiring that day
  is settled and moved from inventory to `settled_usd` (it appears in inventory on the prior session,
  never after the expiry session). Settlement value S = the expiry session's last regular-hours SPX
  bar close from W1.3 (proxy for the official SPXW PM settlement; provenance stamped `spx_1m_close`;
  early-close sessions use their last bar). Payoff per bomb = ×100 × clamp(max(0, K_long − S) −
  max(0, K_short − S), 0, 5) where K_long is the strike we are long and K_short the strike we are
  short (A: long K1 / short K1−5; B: short K1 / long K1+5) — i.e. 0 ≤ payoff ≤ $500. The $10 (or c)
  credit stays in realized cash; `settled_usd` is payoff only. **Provenance:** S is the official
  SPX closing value when the central store's index EOD table carries the expiry date
  (`settle_source = index_eod`), else the last regular-hours 1-min close (`settle_source =
  spx_1m_close`); when both exist they are reconciled and a difference > 0.50 pt is printed as a
  warning with the EOD value used. The cumulative ledger shows realized
  cash, settled bombs, open inventory (mid and liq), and their sums, separately.
- **W6.5 LB95 (session-clustered lower bound), defined once:** universe = confirmation sessions with
  ≥ 1 eligible observation for the statistic; draw sessions with replacement (universe size each
  draw), pool their observations, compute the rate; 2,000 draws, `numpy.random.default_rng(42)` —
  the R9a constants; LB95 = the 5th percentile of the draw distribution (linear interpolation),
  i.e. a one-sided 95% lower bound. **Boundary rule:** LB95 is reported as the MINIMUM of the
  bootstrap 5th percentile and the Clopper–Pearson exact one-sided 95% lower bound on the pooled
  (successes, n_obs) — so ten straight successes report ≈ 0.74, never 1.0. Fewer than 2 sessions
  in the universe → LB95 undefined → INCONCLUSIVE. Every printed rate carries its LB95 and its
  (n_obs, n_sessions).
- **W6.6 Correlated-risk grid:** for the open inventory, payoff at expiry under SPX shocks
  {−8, −6, −4, −3, −2, −1, 0, +1, +2}% from the session close (each bomb settled per W6.4 at the
  shocked spot), printed as one line per shock with totals by expiry — the single correlated
  position made visible.
- **W6.7 Per-candidate shadow book:** the portfolio replays of W3(b), W4(b), W5(b) each produce
  their own bombs; each candidate carries its own W6.1–W6.6 book, printed beside the baseline
  book on the same sessions. Verdict conditions that mention "candidate book MTM" use
  `mark_liq_usd`.

## W7. Discovery / confirmation firewall
- **W7.1** Every session is labeled DISCOVERY or CONFIRMATION in the ledger. DISCOVERY = the 8 frozen
  in-sample sessions (R11.4) plus every out-of-sample session inspected before the watch was
  registered (2026-08-24 → 2026-09-02, inclusive) — these built the candidates and may never count
  toward an evidence bar. CONFIRMATION = sessions whose date is strictly after the registration date
  in `watch_registration.json` (W8) and that were countable per the engine's disposition (R10.3;
  PARTIAL and event_standdown sessions are labeled but excluded from bars).
- **W7.2** Discovery sessions are still scored (they are the reference tables in
  `branch_accounting_2026-09-03.md`), but every table shows the two sets in separate columns and
  every verdict (W3.4, W4.3, W5.4) is computed on the confirmation column only.
- **W7.3** A re-registration (W0.5) moves the boundary: all sessions before the new registration date
  become discovery for the new hash.

## W8. Registration & freeze
- **W8.1** `docs/hiro_watch/registrations/<WATCH_HASH>.json` holds: the candidate definitions and
  constants of W3–W5 (Θ, θ*, C, every evidence-bar number), each candidate's `classifier_columns`
  and `scorer_inputs` (W2.4), the W6.5 constants, the registration date, the engine CONFIG_HASH the
  watch is bound to, the engine's `frozen_manifest_hash`, the W2.8 constants, and `schema_version`
  of the ledgers. **WATCH_HASH = sha256 of the canonical JSON (sorted keys, no whitespace, UTF-8) of
  that payload** — it binds DEFINITIONS only. Code identity is separate: `code_hash` = sha256 over
  the watch package's source files (sorted relative paths + contents) is recorded in
  `registrations/<WATCH_HASH>.code` (an append-only list of `code_hash, timestamp, reason` lines);
  the current line is the one the runtime must match. The hash is written as the filename and into
  `registrations/active.txt`.
- **W8.2** Run-once: `watch register` refuses if `active.txt` exists. A change is a NEW registration
  file (new WATCH_HASH), `active.txt` repointed, a fresh ledger directory `docs/replay/hiro_watch/
  <WATCH_HASH>/`, and the old directory retained read-only (W0.5, W7.3).
- **W8.3** Every ledger row is stamped with WATCH_HASH, the engine CONFIG_HASH, and the W1.6 input
  shas; `code_hash` is recorded once per snapshot in its manifest (code lineage), so that a rebind
  can be verified by table byte-identity. Rows with a different WATCH_HASH are never aggregated. If the watch code changes
  (`code_hash` ≠ the current `.code` line) every command refuses except `watch rebind --reason`,
  which recomputes EVERY ledgered session under the new code into staging, verifies byte-identity
  (W9.4), and on success appends the new line to the `.code` file — WATCH_HASH unchanged, ledger
  unchanged; on any mismatch the rebind is refused and the change requires a new registration.

## W9. Command, outputs, determinism
- **W9.1** One command, `watch <session_date>` (run after that session's engine replay): refuses per
  W0.4, otherwise appends the session's W2 panel rows and W3–W5 counterfactual rows to the ledgers
  and prints the W6 book plus the W3/W4/W5 status tables (evidence progress vs bar, verdict
  PROMOTE / REJECT / INCONCLUSIVE per candidate).
- **W9.2** `watch report` prints the cumulative tables without appending. `watch register` performs
  W8.1 once.
- **W9.3** Ledgers live under `docs/replay/hiro_watch/<WATCH_HASH>/`, one parquet per table
  (`panel`, `a_depth`, `credit_ladder`, `b_refused`, `book`, `inventory`, `settlements`), each row
  stamped per W8.3. **Atomic commit (snapshot directories):** the ledger root holds immutable
  snapshot directories `snap_<NNNN>_<date>/` each containing the COMPLETE set of tables after that
  session, plus a single pointer file `current` naming the latest snapshot. A run copies the current
  snapshot's tables into a staging directory, appends the session, validates (schema, row counts,
  self-checks), then commits with ONE atomic rename of the staging directory to its snapshot name
  followed by an atomic write of `current`; readers always follow `current`. A crash before the final
  pointer write leaves `current` on the previous snapshot; orphan staging/snapshot directories not
  referenced by `current` are discarded on the next run. Snapshots are never pruned (every one is
  needed for identity verification and rebuild). **Chronological processing:** `watch <date>` refuses if any countable session
  between the registration date and `<date>` is not yet ledgered (book state, settlements, and
  drawdown depend on order); `watch rebuild` recomputes every ledgered session in order into a
  fresh staging tree and verifies byte-identity before replacing.
- **W9.4** Determinism: re-running `watch <date>` for a ledgered date recomputes in staging and
  verifies byte-identity with the committed rows, writing nothing (fail loudly otherwise). The W4
  c = 0.10 self-check (reproduce the engine's actual outcome and fill minute for every trade) and
  the panel self-check (W2.2 == logged features) run on every session.

## W10. Operations
- **W10.1** Sequence per session: capture → identity-verify → ingest → engine replay → `watch <date>`.
  The watch is the last step and never blocks the earlier ones.
- **W10.2** No network in the watch except the W6.2 mark pull through the engine's ChainStore, which is persisted on first pull and never repeated for the same (date, expiry).
- **W10.4 Fill realism (accepted limitation, not re-litigated here).** Every counterfactual fill uses the engine's frozen R1.4d physics — one-minute closing-NBBO marketability — because that is what the live parity gate (R12) validates against real resting orders. Queue position, size, and intraminute path are outside the watch's evidence and are recorded as a standing caveat on every CREDIT table.
- **W10.3** The watch refuses a session whose HIRO partition lacks the identity-verified manifest
  note (the evening guard's output) — unverified data never enters a ledger.

---

# Part 2 — Acceptance criteria (WHEN / THE SYSTEM SHALL; W-numbers only)

### Shadow guarantee
- WHEN the watch is installed, registered, and run over every stored session, THE SYSTEM SHALL leave
  every engine artifact (logs, config, registration, CONFIG_HASH, verification pins) byte-identical
  (W0.1) — asserted by a test that hashes them before and after.
- WHEN any candidate test references a column not in W2.2, THE SYSTEM SHALL fail at import/registration
  time, not at run time (W0.2, W2.4).

### Inputs & refusal
- WHEN a required input (W1) is missing for `<date>`, THE SYSTEM SHALL print the missing items and
  write nothing (W0.4).
- WHEN the HIRO partition for `<date>` lacks the identity-verified note, THE SYSTEM SHALL refuse (W10.3).

### Regime panel
- WHEN a session has S signal rows and K refused setups, THE SYSTEM SHALL write exactly S + K panel
  rows with every W2.2 column populated (NaN only where the engine itself had no value, e.g.
  `range60_p75` before warm-up) (W2.1–W2.2).
- WHEN the panel is recomputed from W1.3 for a session, THE SYSTEM SHALL match the engine's logged
  `r15`, `run`, `rate`, `share`, `pull30`, `bounce30` on every signal row exactly (W2.2 uses the
  engine's feature module).

### A-DEPTH
- WHEN a confirmation-set Branch-A signal has r30 ≤ θ, THE SYSTEM SHALL count it as PASSED for that θ
  and attribute its actual engine outcome to the passed set; otherwise to the forgone set (W3.1, W3.3).
- WHEN every W3.4 condition holds for θ* on the portfolio replay, THE SYSTEM SHALL print PROMOTE for
  A-DEPTH; WHEN any W3.4 REJECT path holds, REJECT (with the path named); WHEN 40 confirmation A
  signals exist without either, REJECT-EXPIRED; WHEN W2.8 fires, SCALE_DRIFT; otherwise INCONCLUSIVE.
- WHEN the count bars are unmet, THE SYSTEM SHALL print INCONCLUSIVE with progress fractions (e.g.
  `A-DEPTH 7/20 signals, 4/10 days, passed 3/10 over 2/5 days`).
- WHEN a Branch-A signal's r30 is NaN, THE SYSTEM SHALL count it as unclassifiable for every θ (W2.7).

### CREDIT
- WHEN a trade is replayed at c = 0.10, THE SYSTEM SHALL reproduce the engine's outcome and fill minute
  exactly, and SHALL abort the run on any mismatch (W4.1, W9.4).
- WHEN a leg is still resting at c after the baseline's fill minute, THE SYSTEM SHALL manage it in the
  portfolio replay under the engine's full exit set recomputed minute-by-minute (W4.1b, W0.3).
- WHEN the four W4.3 conditions hold for A at c on ≥ 15 baseline fills, THE SYSTEM SHALL print PROMOTE
  for CREDIT-A-c; WHEN any baseline fill is lost at c, REJECT for that c only; WHEN B has < 5 baseline
  fills, THE SYSTEM SHALL print no B verdict (W4.3).

### B-REFUSED
- WHEN a Branch-B setup was refused for vt_broken, levels_invalid, or LATE, THE SYSTEM SHALL replay it
  under the full B exit set including the flow-shutoff scratch, and report fill, P&L, MAE, and
  naked-short minutes grouped by refusal reason (W5.1–W5.3).
- WHEN fewer than 20 refused episodes exist, THE SYSTEM SHALL label the table INCONCLUSIVE (W5.4); THE
  SYSTEM SHALL never print a promotion verdict for B-REFUSED.

### Book
- WHEN a session closes, THE SYSTEM SHALL print realized cash, open-inventory mark by expiry and strike
  band, MTM with the correlation caveat, and settled bombs separately (W6.1–W6.4).
- WHEN the session being ledgered IS a bomb's expiry date, THE SYSTEM SHALL settle it after that
  session's close at ×100 × clamp(intrinsic, 0, 5) and move it to `settled_usd` (W6.4).
- WHEN a leg's closing quote fails the W6.2 quality test and no usable quote exists within 3 minutes,
  THE SYSTEM SHALL mark the bomb UNMARKED and exclude it from the MTM sum (W6.2).
- WHEN the inventory is printed, THE SYSTEM SHALL print the W6.6 shock grid beneath it.
- WHEN any rate is printed, THE SYSTEM SHALL print its session-clustered 5th-percentile lower bound
  beside it (W6.5).

### Firewall & registration
- WHEN a session is dated on or before the registration date, THE SYSTEM SHALL label it DISCOVERY and
  exclude it from every verdict (W7.1–W7.2).
- WHEN `watch register` is run with `active.txt` present, THE SYSTEM SHALL refuse (W8.2).
- WHEN the watch package's `code_hash` differs from the active registration's, THE SYSTEM SHALL refuse
  every command except `watch rebind`, which re-verifies every ledgered session (W8.3).
- WHEN `watch <date>` is run while an earlier countable session is unledgered, THE SYSTEM SHALL refuse
  and name it (W9.3).
- WHEN a run fails after computing some tables, THE SYSTEM SHALL leave every committed ledger unchanged
  (W9.3 atomic commit).
- WHEN ledger rows carry different WATCH_HASH values, THE SYSTEM SHALL never aggregate them (W8.3).

### Determinism
- WHEN `watch <date>` is re-run for a ledgered date, THE SYSTEM SHALL recompute and verify byte-identity
  with the stored rows, writing nothing (W9.4).

## Non-functional
- Python 3.13, pandas, no new services; reads only the paths in W1; runtime < 120 s per session on the
  stored caches (the portfolio replays run the engine three-plus times per session); `--debug` flag per
  the global CLI rule.
- **Tests (minimum list; each is a named test):** shadow guarantee (engine artifact hashes before/after);
  WATCH_HASH canonicalization (hash field excluded, key order irrelevant, whitespace irrelevant);
  classifier-column firewall rejects a non-W2.2 column at register time; setup dedup (gate_fail+skip
  same minute → one row, precedence honored); NaN r30 → unclassifiable; θ boundary (r30 == θ passes);
  LB95 on 1 session → undefined, on 2 sessions computes, empty sessions excluded; A-DEPTH each of the
  PROMOTE / REJECT / REJECT-EXPIRED / INCONCLUSIVE / SCALE_DRIFT paths on a fixture; W4 c = 0.10
  self-check catches a deliberately perturbed quote; W4 verdict variants (0.30 rejected while 0.20
  promoted; B vacuous-fill guard); W5 levels_invalid replay runs with CHOP context; settlement on the
  expiry session (present the day before, settled that day, payoff clamp 0..500, early-close last bar);
  UNMARKED bomb excluded from MTM; persisted mark cache reused (no second pull); atomic commit
  (crash injected after the first table → ledgers unchanged); chronological refusal (skipping a
  session refuses); byte-identical re-run no-op; code_hash mismatch refuses until rebind, and
  rebind with a changed result refuses; discovery cut-over labels (registration date inclusive →
  DISCOVERY); freed-capacity opportunity appears only in the candidate panel; (A,c) variant leaves B
  legs at 0.10; multi_blocked setup not scored; exit precedence in shadow == engine (fill wins the
  same-minute race); quote-gap → data_invalid tallied; settlement reconciliation warning; verdict
  deferred on UNMARKED; input sha mismatch refuses; crash injected between snapshot rename and
  pointer write → `current` unchanged; LB95 boundary (10/10 → ≈0.74); checkpoint gating (verdict
  absent on session 9, present on 10); UNREPRESENTED defers.

## Acceptance of this spec
Reviewed by: Charlie McElligott + generic via `/codex-plan-review` — round 1 FAIL (25 findings → v1.1), round 2 FAIL (18/9 → v1.2, all applied except the fill-realism item, accepted as W10.4). Both rounds in `requirements_review_2026-09-03.md`. Review closed at two rounds per the 98%-adherence discipline; remaining precision moves to design.md.
Design follows in `design.md`; implementation tasks in `tasks.md`. No code is written before both pass.
