# DECISION 2026-09-04 — the WATCH is a config-per-candidate clone of the engine, not a shadow harness

**Owner's question (verbatim):** "why can't i just create a clone of v1 and mod it as v2 and keep
it really simple. and then i can run v1 and v2 independently."

**Architect's answer: yes — and it is better than either WATCH.** Reproduced below, then the
verification I did of its load-bearing claims, then the decision.

---

## Architect — answer to "why not clone v1 as v2 and run both"

Short version: **yes, and it is better than either WATCH.** The engine already has a `--config` override (cli.py:128–129, stamped as CONFIG_HASH per R8.2), per-config logging paths, a refuse-to-mix scorecard, and a disposition ledger. Most candidates do not even need a clone.

### 1. Does it work? What must change

**CREDIT-0.30 needs no clone at all.** `python -m hiro_engine backtest --day D --config docs/hiro_watch/configs/credit030.yaml` with a yaml that differs from v1's in exactly three lines: `r1v3_limits.credit: 0.30`, `logging.paper_log: docs/replay/hiro_credit030/paper_log.csv`, `logging.sessions_log: docs/replay/hiro_credit030/sessions.csv`. Everything follows: cli.py:53 derives `paper_log_backtest.csv` from `paper_log`; session.py:361 derives `sessions_backtest.csv` from `sessions_log`; scorecard.py:368–375 derives its outdir and takes `--config` too. CONFIG_HASH = sha256 of the yaml bytes (config.py:88), so the candidate is hashed and stamped on every row by the engine itself. Zero files under `scripts/hiro_engine/` change. (Branch-isolated credit — A at 0.30, B at 0.10 — would need a per-branch knob = clone. Not worth it: B trades ~1/week; run one credit for both and read the branches off the log's `branch` column.)

**A-DEPTH and B-REFUSED need one clone** because `c.r30 < 0` is hard-coded (rules.py:67) and vt_broken/levels/late have no off-switch. Concrete edits to `scripts/hiro_engine_v2/` (copy of v1):

| file:line | edit |
|---|---|
| `chains.py:55` | `import hiro_engine.live as _live` → `from . import live as _live` |
| `cli.py:150,155` | `__import__("hiro_engine.parity"…)` / `"hiro_engine.register"` → relative `importlib.import_module(".parity", __package__)` (2 lines); `cli.py:125` `prog="hiro_engine_v2"` |
| `sweep.py:70` | `import hiro_engine.session as sm` → `from . import session as sm` |
| `rules.py:67` | `(c.r30 is not None and c.r30 <= cfg.num("r6_entries", "a_r30_max"))` — one knob; v1-equivalent value is `0.0` (strict `<` vs `≤` differ only at exactly 0.0; note it in build_notes) |
| `session.py:99–104` `_vetoes` | `vt_broken=self.vt_broken and cfg.bool("r4_vetoes","vt_broken_enabled")`, same for `levels_invalid`; `late`: one line in `rules.py:120` `row.late_state and self.e6["late_enabled"]` |
| `config.yaml` | add the four knobs at v1-equivalent values (`a_r30_max: 0.0`, three `*_enabled: true`) + logging paths → this yaml is **v2-baseline** |
| delete from the clone | `live.py`, `spike_*.py`, `ops/`, `parity.py`, `register.py` entries in cli — v2 never runs live, never re-derives R9 thresholds, never touches the ops loop. Also `tests/`: `sed 's/hiro_engine/hiro_engine_v2/'` over 21 files, or drop them and rely on the baseline check below. |

Pins that do **not** need touching: `verification.artifact_hash`, `control_dataset.data_hash`, `chains.control_frame_hash`, `r9a_formulas_hash` pin data/derivation source, not rules; `backtest.py:36–46` interlock only fires over the 8 control days and `verify_frozen` passes on the shared chain cache. `r9a_registration_hash` + the hard-coded `docs/hiro_engine/registration.json` in scorecard.py:245 mean a v2 scorecard grades against **v1's registered R9 thresholds** — that is what you want (same bar), leave it. `_hash_warning` (cli.py:23) only reads live rows; irrelevant. `REPO_ROOT` (config.py:13) still resolves to the repo root. ChainStore root is shared and read-only for stored days — desirable, same inputs.

**Baseline check, once:** `hiro_engine_v2 backtest --from 2026-08-12 --to 2026-09-02 --config v2_baseline.yaml` must equal `docs/replay/hiro/paper_log_backtest.csv` on every `EVENT_FIELDS` column except `config_hash`. That is design §3's `assert_matches_log`, run one time instead of every evening.

Then each candidate is a yaml: `a_depth_m4.yaml` (`a_r30_max: -4.0`), `diag_vt_off.yaml`, `diag_levels_off.yaml`, `diag_late_off.yaml`, each with its own logging dir. Evening = 5 backtest commands ≈ 15 s, one shell loop in RUNBOOK.md.

### 2. Combined or per-candidate

**Per-candidate, one config each — never combined.** W3.4/W4.3 bars are single-change bars ("zero baseline A fills lost at c", "passed cohort vs baseline"). In a combined run the gate changes *which* trades exist and the credit changes *what they earn*; joining v1↔v2 on `(session_date, branch, signal_min, episode)` still separates most of it, but every gate rejection that frees a 3/day slot creates an entry with no v1 twin, and you cannot say whether its P&L belongs to the gate or the credit. At n≈40 that is 3–6 trades — enough to flip a verdict that hangs on ~10 passed signals. Per-candidate costs nothing: same clone, N yamls, N log dirs, 3 s each. B-REFUSED yamls are **diagnostics** (safety rules off); name them `diag_*`, keep them out of any promotion table (W5.4).

### 3. What the engine gives for free

Freeze: CONFIG_HASH over the whole rule config, stamped on every row — stronger than WATCH_HASH. Refuse-to-mix hashes (scorecard.py:53–56). Missing inputs refused and listed (ReplayFeed, R13.1). Full event log (`EVENT_FIELDS`, incl. `leg_liq_loss_usd` = MAE on every exit event) and `sessions_backtest.csv` dispositions. Scorecard: six stages, R9 criteria incl. the would-have-filled counterfactual, the $-risk lines, best-session re-check, R11.4/R11.5 controls, `summarize.py` R13.3 contract. **Not free: marking open bombs.** `scorecard.py`/`summarize.py` have zero references to marks/inventory; §5–6 of the accounting doc were done offline. `register.py` is the R9a *threshold* derivation (run-once, pinned) — it is not a candidate-definition freeze; the yaml hash is.

### 4. What it loses vs the minimal WATCH, at n≈40

- **Regime panel:** signal rows carry `run/rate/dC/dP/share/r15/pull30/bounce30` (rules.py `_stamp_conditions`) and the A note string carries `r30=`; not logged: `flow_accel`, `range60`, VT distance. Enough for the Θ ladder (parse r30 from the note, 2 lines) and for W3.6 representation if you join the levels CSV. Loss: minor.
- **Sole-blocker attribution:** v1 skip rows (`short blocked: vt_broken`) joined to `diag_vt_off` entry rows on `setup_id` — 5 lines. Same result as the WATCH.
- **LB95:** scorecard has none (point estimate vs floor + sample minimum, R9's form). Either 15 lines in compare.py (bootstrap + CP, `DRAWS/SEED` from `register.py`) or grade v2 on R9's form like v1 is graded. Either is defensible; pick one and write it down.
- **Discovery/confirmation firewall:** the engine has no notion of it — scorecard grades `--from/--to` of one hash, and R9's 10-session count starts at the first countable session of that hash. For a clone: discovery = backfill of the 16 stored sessions; confirmation = `--from <clone commit date + 1>`. The firewall is a `--from` argument and a git commit date. Checkpoints = you run compare.py at 10/20/30/40 confirmation sessions; a 3-line guard in compare.py refuses verdict lines otherwise.
- **Per-session input shas:** ReplayFeed refuses missing files but does not pin bytes; the chain cache is manifest-sha'd. Marginal loss with a store you control and git-tracked logs.
- **Baseline==log every run:** moot — v1's log is the baseline, and the once-only v2-baseline check covers the clone.
- **Book/MTM/shock grid:** lost unless compare.py does it. It matters — W3.4/W4.3 compare candidate MTM to baseline — so compare.py must own marks (pull-once per (date, expiry) via `chains._sdk_pull_day`, ~40 lines).

### 5. Recommendation

**Clone-and-mod (one clone, one yaml per candidate) plus `compare.py` (~150 lines: read N logs, join on setup_id, per-candidate trades/fills/P&L/MAE, mark + settle open bombs, LB95, confirmation-only columns, checkpoint guard, print).** Line count: ~8 edited lines in the clone, 5 yamls, ~150 compare.py, ~80 tests for compare.py → **~250 new lines, 3 concepts** (a candidate is a yaml; its CONFIG_HASH is its registration; `--from` is the firewall), against 1,250 for the minimal WATCH and 1,800 for the spec. The 6,300 duplicated lines are inert — v1 is frozen, so there is no drift to maintain.

**The one rule that keeps it honest:** *A candidate is a config file committed to git before its first confirmation session; the commit date is its registration date; its CONFIG_HASH on every log row is its identity; it is never edited — any change is a new file with a new name, and the scorecard's refuse-to-mix enforces it.* Corollary: the clone's four knobs are committed at v1-equivalent values and the v2-baseline log is diffed against v1 before any candidate yaml exists.

This supersedes §5 of my earlier audit: the minimal WATCH was the right answer to "simplify the spec"; the clone is the right answer to "what should be built".

---

## Verification of the load-bearing claims (done before deciding)

| Claim | Where | Result |
|---|---|---|
| `--config` override exists and stamps its own hash | `cli.py:78,129` | ✔ |
| log paths derive from the config, so a candidate yaml gets its own log dir | `cli.py:53`, `session.py:369`, `scorecard.py:370-377` | ✔ |
| `r30 < 0` hard-coded in the A condition | `rules.py:67` | ✔ (`c.r30 < 0`) |
| absolute `hiro_engine.` imports to fix in a clone | `chains.py:55`, `cli.py:150,155`, `sweep.py:70` (+ spike scripts, deleted in the clone) | ✔ |

## Decision

1. **Build the clone route.** `scripts/hiro_engine_v2/` (four knobs, ≤ 10 edited lines, live/ops/spikes
   removed) + one yaml per candidate under `docs/hiro_watch/configs/` + `scripts/hiro_watch/compare.py`.
2. **Retire the shadow-harness spec** (requirements v1.2a / design v1.3 / tasks v1.2 and their three
   review transcripts). Removed from the tree in this commit; they remain in git history at `90b1d24`
   / `5515402` for the record. The two simplicity audits stay as the decision record.
3. **The one rule** above is the entire governance of the program. It goes into the new
   `requirements.md` as W0.
