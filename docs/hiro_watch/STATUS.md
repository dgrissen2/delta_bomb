# hiro_watch — STATUS (2026-09-11)

Single page that says exactly where the WATCH program is and what happens next. Update this file
whenever the state changes; it is the first thing to read after a context reset.

## Where we are — BUILT 2026-09-04, two `/code-review` rounds applied (20/20 fixed), confirmation session 1 logged

| piece | where | size |
|---|---|---|
| clone | `scripts/hiro_engine_v2/` | v1 minus live/ops/spikes/parity/register/verify/sweep; +4 knobs (≈10 edited lines); 140 tests green incl. W0.2 byte-identity over the 16 stored sessions |
| candidates | `docs/hiro_watch/configs/*.yaml` (+ `README.md` with hashes) | 7 files: `baseline_v2` (control), `credit030` (v1 engine), `a_depth_m4`, `a2_size1_c30` (three-knob pick, registered 09-08), `diag_vt_off`, `diag_levels_off`, `diag_late_off` |
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

### Session 2026-09-08 — levels gap found; three sessions re-run; `a2_size1_c30` registered (`session_2026-09-08.md`)

The engine's SpotGamma levels CSV had stopped at 09-01: sessions 09-02/03/08 had run `levels_invalid`
all day (B short-blocked for the wrong reason; the R4.2 banner was in the logs, unread). Rows appended
from the scraped notes, v1 re-run for the three days, all candidates rebuilt over 19 sessions,
`daily_session.py` now verifies the day's levels row before any engine runs. Only 09-03 changed: a B
trade v1 takes with levels valid — `veto_exit` −$200 — so 09-03 is **−$620**, not −$420, and the
baseline through 09-08 is A 24/13 −1,210, B 8/3 −460, cash −1,670, inventory +665 → **MTM −1,005**.
09-08 itself: SPX below the trigger all day, two B signals > 1.0 $B, no A signal — v1 0 trades,
`a2_size1_c30` 0 trades. `a2_size1_c30` (r30 < −2 + run ≤ 1.0 + A 0.30/B 0.10) registered
2026-09-04, first confirmation session 09-08; over all 19 sessions cash +70, MTM +580 (discovery,
not evidence). Its bar = W5.3 `portfolio`; `compare.py verdict_portfolio` (+1 test, 17 green).

### 2026-09-09 — event-day policy (W6): stand down on FOMC only; NFP / CPI / opex / month-end traded + tagged

Applied as data (`scripts/hiro_watch/events.py` → `docs/hiro_engine/event_calendar.csv`); engine
untouched. 08-31 and 09-04 re-run as trading days (08-31: 0 trades; 09-04: A timeout −$170 for v1
and the pick). Baseline through 09-08: cash **−1,840**, MTM **−1,175**; `a2_size1_c30` cash −100,
MTM +410. Per-day table: `python scripts/hiro_watch/daily_table.py [candidate]`. Confirmation
counts: a_depth_m4 / credit030 / diag 3 of 10 (09-03, 09-04, 09-08); a2_size1_c30 1 of 10.
Known: frozen v1 test `test_calendar_rules` fails by design (asserts an empty manual calendar).
Regime tags (W6.5: `vt_break`, `vt_deep`, `sgi_low`) added to compare/daily_table for the below-VT thesis;
the VT short-block stays.

### 2026-09-09 — owner's choice confirmed: `a2_size1_c30` is THE v2 variant on the clock

The 09-05 notes carried two front-runners (reviewers' B-PULL 8; owner's higher-N `r30 < −2` + `run ≤ 1.0`
+ A 0.30 / B 0.10). After the levels fix and the event policy the 60-cell grid was re-run on all 19
sessions (`diagnostics/grid_2026-09-09_19sessions.csv`): no cell is cash-positive; the owner's pick has
the highest MTM of all 60 (cash −100, inventory +510, MTM +410; 19 trades / 12 bombs, A 12/8 +30,
B 7/4 −130, worst −170) and pull8 fell harder (the 09-03 B trade had pull30 ≈ 13 and ate the −200
veto-exit the run cap scratched at $0). Owner (2026-09-09): keep `a2_size1_c30` as the chosen variant.
v1 on the same 19 sessions: 33/16, cash −1,840, MTM −1,175.

### Session 2026-09-09 (countable; `vt_deep` — opened 40 under the trigger, closed 7636; `compare_2026-09-09.txt`)

v1: two Branch-A trades on shallow flow (r30 −0.96 and −0.27): 11:17 bought 7375P, filled in 6 min
**+$10**; 11:30 bought 7330P, timed out **−$90** → −$80. Two B signals blocked `vt_broken`.
**Both v2 variants: 0 trades** — neither A signal reached r30 < −2. Inventory re-marked with SPX
−37 on the day: baseline MTM −830 (17 bombs, +1,090 inventory); `a2_size1_c30` cash −100, inventory
+810 → **MTM +710**; `a2_pull8_c30` cash −150, inventory +740 → MTM +590. Confirmation counts: pick
2/10, pull8 1/10, a_depth_m4 / credit030 / diag 4/10. `diag_vt_off` took a B bomb (+$10) again.
Disk had filled to 667 MB free mid-capture (ENOSPC, refused cleanly); rerun after space was freed.

### Sessions 2026-09-10 / 09-11 — the A gate's first real hit (`session_2026-09-11.md`)

09-10 (`vt_deep`, SG Index −0.67): v1 filled three shallow-flow A trades **+$30**; both variants sat out
(gate) → first day the gate cost money. 09-11 (**CPI**, first **`sgi_low`** session, SG Index −1.615):
flow went deep (r30 −2.36 / −3.02), **the gate passed, and both variants took v1's two trades** —
fill +$30 then a **cap exit −$380**, the worst trade of the program. Day: v1 −370, both variants −350
(the 0.30 A credit is the whole difference). First confirmation evidence AGAINST the A-depth premise
(n=1). Book after 22 sessions: v1 40/21, cash −2,260, MTM −1,260; `a2_size1_c30` 21/13, cash −450,
MTM +495 (4/10); `a2_pull8_c30` 17/11, cash −500, MTM +445 (3/10).

Ops: TradingView 2FA blocks `daily_run.py --steps 2,4`; SpotGamma headless auth fails. Working path —
drive `IntegrationWorkflow` over CDP against the logged-in Chrome :9222 (`connect_over_cdp`), which
scrapes the notes with no new login; then `append_recent_voltrigger_data`. Playwright chromium had to
be installed for sg_note_scraper.

## What's next

1. Registered: `a2_size1_c30` (the choice) and, since 2026-09-09, `a2_pull8_c30` — identical except the B
   filter (pull30 ≥ 8 vs run ≤ 1.0), so the pair separates B-SIZE from B-PULL. Discovery: 15/10, cash −150,
   MTM +318 (its B: 3/2 −180 — it took the 09-03 −200 veto-exit). Still unregistered: `a_depth_m2`,
   `b_size1`, `b_off`.
2. Next capture: 2026-09-14 (Mon) — `python scripts/daily_session.py 2026-09-14` then
   `python scripts/hiro_watch/compare.py`. Check the SpotGamma login in Chrome :9222 first (it had
   expired on 09-08) and scrape the day's Founders Note (`cd ~/Dev/core_spotgamma_spx_vix_data && .venv/bin/python daily_run.py --steps 2,4`)
   — the levels step refuses otherwise. 09-16 is FOMC (STAND DOWN); 09-18 is quarterly opex (traded, tagged).
2. Review loop is CLOSED (two rounds, 20 findings, all fixed or accepted in `build_notes.md`).

## Standing constraints that bind this program

- Never edit `scripts/hiro_engine/`; never refresh the 8 frozen control days; never point the HIRO
  backfill `--force` at the store (staging → ingest only).
- HIRO `stock_price` and any SpotGamma `Ref Px` are verification-only, never a price source.
- The daily capture loop continues regardless — vendor retention is ~5 sessions; a missed capture
  is permanent data loss. Next session to capture: 2026-09-14.
