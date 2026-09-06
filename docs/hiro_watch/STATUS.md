# hiro_watch — STATUS (2026-09-04)

Single page that says exactly where the WATCH program is and what happens next. Update this file
whenever the state changes; it is the first thing to read after a context reset.

## Where we are — BUILT 2026-09-04, two `/code-review` rounds applied (20/20 fixed), confirmation session 1 logged

| piece | where | size |
|---|---|---|
| clone | `scripts/hiro_engine_v2/` | v1 minus live/ops/spikes/parity/register/verify/sweep; +4 knobs (≈10 edited lines); 140 tests green incl. W0.2 byte-identity over the 16 stored sessions |
| candidates | `docs/hiro_watch/configs/*.yaml` (+ `README.md` with hashes) | 6 files: `baseline_v2` (control), `credit030` (v1 engine), `a_depth_m4`, `diag_vt_off`, `diag_levels_off`, `diag_late_off` |
| evening command | `scripts/hiro_watch/run.py` | 109 lines |
| registry + accounting | `scripts/hiro_watch/registry.py`, `compare.py` | validated candidate list; accounting; 16 tests |
| outputs | `docs/replay/hiro_watch/<name>/` (engine-written logs); marks in `~/Dev/central_trade_data/thetadata/spxw_marks/` | rebuildable |
| spec | `requirements.md` v2.0, `design.md` v2.0, `tasks.md` v2.0 | 250 lines total |

Registration: committed **2026-09-04**; `watch.registered` = **2026-09-02**, the last session whose
data was inspected when the candidates were defined (corrected on day 0, before any confirmation
session was logged — the first cut had used the commit date, which would have made 09-03 discovery).
DISCOVERY = 2026-08-12 → 09-02 (16 sessions). CONFIRMATION session 1 = **2026-09-03**. Checkpoints
at 10/20/30/40 countable confirmation sessions.

### Confirmation session 1 — 2026-09-03 (`docs/replay/hiro_watch/compare_2026-09-03.txt`)

v1 took two Branch-A trades on shallow flow (r30 −0.96 and −1.20): cap −$350, timeout −$70 → −$420.
SPX rallied; the 16-bomb inventory marked +$165 (was +$1,265) → baseline MTM −$1,305.
`a_depth_m4` took neither trade (both gated) → 0 confirmation trades. `credit030` took both at the
same prices and lost the same −$420. Its A branch first printed an immediate REJECT on v2.0's
"no trade P&L < −$150" bar — a bar that measured the engine's own cap exit, not the credit. The
owner asked what the data says: accounting §7 had already rejected a $150 stop (−$870; 3 of 16
winners were > $150 underwater before filling). **Requirements v2.1 removes the $150 line from every
bar** (note in W5.3); the engine's exits stay the 60-min clock and the 3.5-pt cap. No candidate
yaml changed. Both promotable candidates now read INCONCLUSIVE (1/10).

**Session 2026-09-04** (NFP): engine stood down by rule (R4.4); no candidate traded; not a confirmation
session. Inventory marked +$590 (SPX −30 on the day) → baseline MTM −$880. Tally + Charlie/Brent
plain-language diagnosis + Feynman: `tally_review_2026-09-04.md`. Both reviewers: the trade's
economics are broken ($160 earned vs $1,630 lost on naked legs), the inventory is one correlated
guess, and the tape has confirmed nothing yet (1/10).

The daily loop is now one command: `scripts/daily_session.py <date>` (SPX → HIRO capture/identity/
ingest → chain → v1 backtest → hiro_watch/run.py), then `hiro_watch/compare.py`.

### Backfill result on the 16 discovery sessions (asof 2026-09-02, marks pulled)

| candidate | A trades/bombs | B trades/bombs | cash | inventory | MTM | note |
|---|---|---|---|---|---|---|
| baseline (v1 log) | 22/13 | 7/3 | −1,050 | +1,265 | **+215** | matches `branch_accounting_2026-09-03.md` §1/§5/§6 exactly |
| `baseline_v2` | 22/13 | 7/3 | −1,050 | +1,265 | +215 | byte-identical to v1 except `config_hash` (W0.2) |
| `credit030` | 22/13 | 7/**1** | −690 | +1,170 | +480 | A: 13/13 fills held; **B: 2 of 3 fills LOST** in the portfolio replay (08-12 ep4, 08-25 ep1) — the isolated replay in accounting §7 had said 08-25 fills at +34 min; the engine's own exits got there first. Charlie's portfolio-vs-isolated point, demonstrated on discovery data. |
| `a_depth_m4` | 5/5 | 10/3 | −570 | +530 | −40 | A 5-for-5 as in §4; B gets the freed capacity (10 trades vs 7) and loses it back. Θ ladder: −1 0.58/12, −2 0.71/7, −3 0.83/6, −4 1.00/5, −5 1.00/2. |
| `diag_late_off` | 22/13 | 7/3 | −1,030 | +1,315 | +285 | 14 LATE episodes (12 also vt-blocked), 2 entered, 1 bomb |
| `diag_levels_off` | 22/13 | 9/3 | −1,220 | +1,265 | +45 | 2 levels_invalid episodes, both entered, 0 bombs, −$170 |
| `diag_vt_off` | 22/13 | 13/7 | −1,370 | +1,460 | +90 | 31 vt_broken episodes (11 also late-blocked), 6 entered, 4 bombs, −$320 cash |

None of this is evidence (all discovery). It is the reference table the confirmation columns will
sit beside.

**Branch B (2026-09-05):** failure modes and actionable candidates from Charlie + Brent on GPT-6 Astra —
`branch_b_review_2026-09-05.md`, `branch_b_actions_astra_*.md`, CIO memo `branch_b_cio_memo_2026-09-05.md`.
Ranked single-knob candidates to register before the next session: B-PULL (pull30 ≥ 8), B-SIZE (run ≤ 1.0 $B),
B-CREDIT-0 (B rests at fill − 0.00), B-OFF (control), then LATE-sticky and run-age ≤ 15. Rejected: wider
scratch window; pull30 10 as a separate test. Owner's go needed to register (each needs a v2 knob).

**Knobs built (2026-09-05/06):** the five Branch-B knobs exist in v2 at v1 defaults (160 tests green,
byte-identity holds; candidate hashes regenerated, tally identical). Diagnostic replays of every knob,
the A-gate combos and a 60-cell grid: `knob_results_2026-09-05.md`; the rules in plain English:
`rules_in_english.md`. Owner's higher-N pick: `r30 < −2` + `run ≤ 1.0` + A credit 0.30 / B 0.10 →
12 bombs, cash +$160, MTM +$620 on discovery data. Nothing new registered yet.

## What's next

1. Owner's go on WHICH candidates to register (each = one yaml; the knobs exist). Suggested set:
   `a_depth_m2` (−2 alone), `b_size1` (run ≤ 1.0 alone), `b_pull8`, `b_off` (control), and the named
   three-knob pick `a2_size1_c30` — so confirmation can tell which knob earns.
2. Next capture: 2026-09-08 (Tue, after Labor Day) — `python scripts/daily_session.py 2026-09-08` then
   `python scripts/hiro_watch/compare.py`.
2. Review loop is CLOSED (two rounds, 20 findings, all fixed or accepted in `build_notes.md`).

## Standing constraints that bind this program

- Never edit `scripts/hiro_engine/`; never refresh the 8 frozen control days; never point the HIRO
  backfill `--force` at the store (staging → ingest only).
- HIRO `stock_price` and any SpotGamma `Ref Px` are verification-only, never a price source.
- The daily capture loop continues regardless — vendor retention is ~5 sessions; a missed capture
  is permanent data loss. Next session to capture: 2026-09-03.
