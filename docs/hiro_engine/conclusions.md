# hiro_engine — Conclusions & Learnings

*Running record of what the engine has established, in order of discovery.
Each entry states the evidence, the decision, and what remains open. Companion
docs: `requirements.md` (the frozen rules), `build_notes.md` (implementation
decisions), `bh_scratch_forensics_2026-08-23.md`, `registration.json`.*

---

## 1. HIRO is a thermometer, not a barometer (research phase, 2026-08-21/22)

Across 845 tape sessions and 8 HIRO sessions with matched controls: HIRO is
coincident with price (ρ≈0.7 same-minute, no 1–15-min lead). Every entry-side
"HIRO confirms the move" claim died under matched controls — EXCEPT the
negative-flow filter (below). Exit-side value (flow-shutoff, negative-flow
veto) survived every test in touch-semantics research. The engine exists to
test the surviving composition without human fudging.

## 2. The ±3-pt touch proxy overstated bomb economics by ~$50/bomb (2026-08-23)

Repricing all completed rehearsal bombs at real SPXW chain mids: the "free"
bomb legged in for ~$46 average at the 3-pt touch (a 3-pt SPX move shifts a
20Δ put ~0.6 while 5 strikes shift ~1.0). Trade prints are too sparse for
fill detection (6/391 minutes on a bomb strike); marketable 1-min NBBO is the
faithful mechanic. → spec v3.0: leg 1 books at conservative NBBO, leg 2 rests
at fill1 ∓ 0.10, a bomb exists only when that limit fills. Every completed
bomb now nets ≥ +$10 by construction.

## 3. Exit rules must be measured, never reasoned-by-analogy (BH scratch, 2026-08-23)

The Branch-A bounce-high scratch was authored as a "common sense" mirror of
B's researched flow-shutoff and shipped unbacktested. First honest test: 8/8
scratches would have filled, 38.1 pts surrendered, and it CREATED the only
adverse>10 event. Root cause: the exit watched the same variable as the entry
(the bounce), so it fired on the entry's own signature. → removed (v2.3);
standing rule now in the spec: no exit may trigger off its entry variable,
and nothing ships without a backtest showing it saves more than it costs.

## 4. The honest baseline: a random-minute $10-credit limit fills ~46% of the time

The v3 control frame (2,168 candidate minutes, 8 sessions): sell-first
baseline 0.470, long-first 0.454; weighted to actual entry clocks, B's
baseline is 0.583 (B trades in GOOD slots) and A's midpoint-matched control
is 0.500. Any claimed edge has to beat THESE numbers, not the old 0.77 touch
fiction.

## 5. Branch A's edge is real and it is the FLOW FILTER (v3 rehearsal, 2026-08-23)

A (buy the put into a weak bounce on a heavy, big-range tape): 8/12 scored
fills = 0.667 vs 0.500 midpoint control (+16.7 pp, clears the +10 pp bar).
The control differs from A by exactly one condition — 30-min HIRO flow NOT
negative — so the +16.7 pp IS the surviving entry-side HIRO value. Cleaner
still: A's five timeouts were limit-replayed and ZERO would have filled — the
signal separates fills from duds with nothing left on the table, and its only
exits (clock/resolution) cost nothing.

## 6. Branch B's entries are fine; its EXITS are mistimed for limit fills (2026-08-24)

B scored 0.333 (2/6) vs its 0.583 control — but the no-exit counterfactual is
0.667, ABOVE control. Decomposition of B's four non-fills:
| trade | exit | limit would have filled? |
|---|---|---|
| 08-12 scratch (−$80) | correct — never fills |
| 08-14 scratch (−$100) | **yes, minute 39** |
| 08-14 veto (−$60) | **yes, minute 58** |
| 08-17 veto (−$50) | correct — never fills |
The flow exits were researched under touch semantics (fills in minutes 1–28);
real fills arrive in minutes 8–58, and exits tuned to the fast world clipped
two slow winners. Mixed (2 correct / 2 harmful, n=4) — NOT the BH pattern
(8/8 harmful). Also: 5 of 8 sessions were below the Vol Trigger, so B was
starved to 6 entries from 28 qualifying signals; n is tiny.
**Decision (user, 2026-08-24): run the live test AS FROZEN; the B-exit
re-timing is PRE-REGISTERED as an inactive candidate in R7.2** (test on stored
sessions across ≥ 20 B episodes before any activation; any activation is a
spec edit + full R9a re-registration + test reset).

## 7. The registered exam (R9a record, stated plainly)

The run-once boundary was exercised three times; the TRADE LIST never changed
(19 trades / 10 fills / −$670 cash, independently verified each time); only
the grading derivation was corrected, each time toward the frozen text, each
time making the test HARDER: data_invalid mis-scoping fixed → p95 population
per R11.3 (cap $250→$150) → countable-only population (A floor 0.50→0.55).
Final registered thresholds: fills ≥ 11 (10-session projection), sessions
with ≥1 fill ≥ 7, B rate ≥ 0.10 and not below its control, A rate ≥ 0.55 and
≥ control +10 pp, max single loss ≤ $150, median scratch ≤ $140.

## 8. The honest v3 rehearsal economics (8 in-sample sessions, 1-lot)

19 attempts → 10 bombs planted (0.526). Credits +$100, losing legs −$770,
net cash −$670; the 10 owned 5-wide spreads marked +$645 at completion
(max payout $5,000) → MTM ≈ −$25 with the payoff optionality intact. Fills
took 8–51 minutes. The rehearsal FAILS its own registered thresholds on the
two count floors (10-session projections graded against 7 countable
sessions — an incomplete-test artifact) and on the $290 max loss vs the $150
p95 cap (a 08-20 timeout; the cap intentionally demands better tail control
than the rehearsal's worst trade). None of that is tuning feedback.

## 9. Process lessons that now bind

- A hand-computed fixture written BEFORE the code catches real bugs: it
  caught the cap-vs-leg-1-fill deviation — but only after its hand-derived
  MINUTES became load-bearing assertions. Decorative expecteds catch nothing.
- Silent search-and-replace is how "fixed" bugs survive: assert every patch.
- Controls must share the mechanics of the thing they benchmark (limit
  replay, same rounding, same gap rules) or the comparison is fiction.
- Every review round (2 planning + 2 build break points, red-team + codex in
  parallel) produced at least one finding that would have corrupted the live
  record. None were style nits. The 98%-adherence discipline (fix blockers/
  majors, log-and-accept documented residuals) held throughout.

## Open questions for the live test

1. Does A's +16.7 pp edge survive out of sample? (The 8 sessions were one
   heavy, below-VT week — A's home field.)
2. Does B reach 20 qualifying signals on executable days, and does the frozen
   exit set keep costing fills? (The pre-registered candidate waits on this.)
3. Live/backtest parity: do post-bar snapshots match the historical series
   within 1 tick / 95%? (Shakedown gate.)
4. Are 10 fills per 10 sessions (the registered floor: 11) realistic at
   exactly 0.10 credit, or is the honest bomb a 0.20-credit trade? (Only a
   post-test re-registration may ask this.)

## 10. The credit knob barely touches A; the walk-down is a dead end (2026-08-24)

Counterfactual replays on the pinned caches (pure limit replay, engine
untouched):
- **A @ 0.20 credit: the identical 8/13 fills**, +$10 more per bomb (+$80 on
  the week; MTM +$260 vs +$190 on the pure-replay basis). Headroom is
  BIMODAL: the 8 fills had **$40–$460** of achievable credit within the hour
  (median ~$160); the 5 timeouts never came within **$30 of flat**. On this
  sample even **0.30 keeps all 8 fills** (tightest headroom $40). A separates
  winners from duds so cleanly that the limit level in 0.10–0.30 mostly just
  sets the pay-per-bomb.
- **Walk-down (0.10 → 0.00 @30m → −0.10 @45m): rejected.** It rescued ZERO
  fills — unfilled trades are $30–$110 away even at the day's best print, and
  B's two rescuable trades die from FLOW EXITS at minutes ~2–25, before the
  walk begins. All it does is cheapen the five late fills (+$120 → +$60
  credits). This independently re-proves conclusion 6: B's problem is exits,
  not price.
- Both registered as R7.2 pre-registered candidate (3) with an out-of-sample
  evidence bar (≥ 15 A fills, zero lost vs 0.10). The live test runs frozen
  at 0.10; the credit knob stays out of the sweep whitelist.
- Caveats that bind: n = 8 fills, one heavy below-VT week, in-sample days,
  and this is precisely the knob-peeking the R9a honesty note exists for —
  which is why it is a pre-registered candidate and not a change.

## 11. There is NO held-out HIRO set — and the identity check that proved it (2026-08-24)

Correction of an error in this record's own section-6 discussion: the "5
additional sessions (08-05..08-11)" proposed as a held-out set for the B-exit
study DO NOT EXIST as data. The user demanded a day-identity check before
using them (guarding against mislabeled captures); the check found the five
partitions are EMPTY SHELLS — the manifest records them `status: unavailable`
(the vendor's ~5-session retention window had already rolled past them when
the 08-19 backfill ran). Directory count is not data count.

The identity method itself is now permanent: each session's HIRO payload
carries a per-row basket stock_price; matched per-minute against the ACTUAL
SPX closes of every candidate day, the labeled day must win with median
|diff| < 5 pts (verification-only use of stock_price — never a price source,
per the standing Ref-Px rule). All 8 frozen sessions PASS (median diffs
0.26–0.64 pts; nearest wrong-day 5.4–14 pts). The evening ops check now runs
this guard on every new capture — an unverifiable or empty capture is RED,
not silently banked.

**Consequence for the B-exit study**: usable HIRO data = exactly the 8 frozen
sessions (all burned in-sample). The study's ≥ 20-episode out-of-sample bar
can only be met by ACCUMULATION: daily captures during the shakedown + live
test (~3-4 B qualifying episodes/session on mixed-regime days) — roughly 2-4
weeks. Design work on the 8 in-sample sessions may proceed anytime; VALIDATION
waits for the accumulated out-of-sample days, which are clean by construction
(the frozen test never tunes on them).

## 12. The vendor window is real, moving, and has already eaten three frozen sessions (2026-08-24)

Live retention probe through the authenticated CDP session (fetch pipe
verified working — 08-21 and 08-18 return full data): the SpotGamma HIRO
endpoint now serves only ~2026-08-17 onward. **2026-08-11 is unrecoverable**
(the original question), and — the bigger finding — **2026-08-12/13/14, three
of the eight frozen control sessions, are no longer obtainable from the
vendor.** Our hash-pinned store is the only copy in existence. Actions taken:
full tar.gz backups of the HIRO v1 store and the SPXW chain caches written to
`~/Dev/central_trade_data/backups/` with SHA256SUMS (recommend an off-machine
copy); the daily-capture requirement is now demonstrably existential — a
missed session is permanently gone within ~5 trading days.

## 13. First out-of-sample week (2026-08-24/25/26): three sessions, three learnings (2026-08-27)

The first true out-of-sample sessions under the frozen CONFIG_HASH
`80c3a41026c8…` — backtest-mode replays over identity-verified captures
(0.33–0.49 pt medians, each a 15–40x cross-day winner), NOT part of the
10-session live clock. Every rule fired as written; what follows is evidence
about the *strategy*, not defects in the engine.

**The ledger.** 08-24: zero trades (correct abstention). 08-25: B bomb
COMPLETED +$10 (12-min fill) and an A timeout −$300. 08-26: A timeout −$50.
Realized −$340 cash; one armed bomb (long 7380/7375 put vertical, exp 09-25,
carried at negative cost) marked +$50 at the 08-26 close → MTM ≈ −$290.

### 13.1 The discipline layer earned its keep on the flow-positive days

08-24 was the archetype: SPX below the 7700 Vol Trigger every minute, +12.0B
one-way positive flow, five Branch-B sell-first signals (runs to 5.6B at
6-10B/hr) — ALL refused by R4.1 vt_broken (four also LATE per R6.3), and no
A signal because no negative-flow episode ever formed. A hand trader watching
those put-selling waves would have been sorely tempted to sell into them
below the trigger. The system's whole-day abstention was the correct trade.
08-26 repeated the pattern (2 more B blocks + 1 LATE below VT 7675).
Standing clarification (asked and re-verified): R4.1 blocks NEW UNPAIRED
SHORTS only — Branch A (buy-first) is deliberately legal below VT, because
its unpaired exposure is LONG downside in the regime where downside extends.

### 13.2 The early OOS tape mildly INVERTS the in-sample story: B filled, A didn't

- **B's first out-of-sample completed bomb** came sell-first on the one
  above-VT morning (08-25, VT 7660): sold 7375P @ 39.90 (bid), rested the
  7380P buy at 39.80, marketable 12 minutes later. In-sample, B fills were
  the registered worry (b_fill_rate floor 0.10); first OOS data point says
  the mechanism works when the regime admits it.
- **A went 0-for-2 on fills** against its 0.55 in-sample floor. Both A
  entries fired on SHALLOW negative-flow readings — 08-25: r30 = −0.11B
  (essentially flat), close<mid30 by 0.65 pts, bounce 3.18; 08-26:
  r15 = −0.44B, bounce 5.24 — and both bought the put at what proved to be
  the START of an upswing, not a pause in a downswing. 08-25's 10:30 low
  (7650.92) was the LOW OF THE DAY; the "bounce" the signal bought into was
  minute one of a V-reversal that ran +12.8 pts through the 60-min clock
  (−$300). 08-26 rhymed (+10.3 adverse, −$50).
- **This is the mid30 premise-check scenario, verbatim.** R7.2 pre-registered
  candidate (1) exists to test whether close<mid30 + bounce30 selects
  continuation dips or reversal bottoms. The first two OOS entries both vote
  "reversal-catcher," specifically when the flow evidence is thin (|r30| ≪ 1B).
  n=2 — no rule change; the candidate's evidence file is now open and
  accumulating. A natural sharpening hypothesis for that file: A's flow gate
  passed here on readings indistinguishable from noise; the winning B signal
  17 minutes earlier had 0.59B of actual directional run.
- **Tail note:** the −$300 A loss exceeds the registered
  max_single_trade_loss line ($150). Informational (OOS replay, not the live
  test; the rehearsal already flagged the p95 tail line) — but it is the
  second consecutive dataset in which A's losers, not B's, carry the tail.

### 13.3 Credit-ladder counterfactual on the completed bomb: 0.20 was free, 0.30 filled too

Replaying the 08-25 B bomb's resting buy at wider credits (all guardrails
live; cap never threatened — max adverse mid 40.05 vs 43.40 trigger):

| credit | limit | fill | minutes after entry | clock slack |
|---|---|---|---|---|
| 0.10 (frozen) | 39.80 | YES | 12 | 48 min |
| 0.20 | 39.70 | YES — SAME minute | 12 | 48 min |
| 0.30 | 39.60 | YES | 34 | 26 min |

The 10:58 dip printed ask 39.70 exactly: **0.20 credit was free on this
trade** (identical fill minute, double the credit). 0.30 needed the second
leg down at 11:20 — it filled with 26 min of slack and was then marketable
virtually every remaining minute, but the extra $10 was bought with 22 more
minutes of naked-short exposure through the same 11:05 bounce that, after
the window, became the rally that killed the A trade. First BRANCH-B data
point for the credit family (candidate (3) is A-specific; in-sample "0.30
keeps all fills" was built on A fills). Running counterfactual: at 0.20 this
week is identical except the bomb pays +$20; at 0.30, +$30.

### 13.4 Ops lessons now standing

- **Never point the backfill's `--force` at the store.** The 08-24 evening
  recapture rewrote the store's canonical manifest in the backfill's own
  schema; recovered byte-verified from the same-day backup tarball (all 8
  frozen partitions re-verified, ALL OK). Since 08-25 the standing workflow
  is: capture to a STAGING dir, identity-check, then ingest canonically —
  the store manifest is written only by the ingest step.
- **Intraday captures are short.** The first 08-24 pull ran at 15:57 ET and
  missed the close; evening recapture (attempt=2) superseded it. Captures
  are evening-only unless deliberately partial.
- The SpotGamma login expires and blocks capture (08-27: session dead at the
  first attempt; one human login fixed it). With the ~5-session vendor
  window, a login outage that outlasts the window IS data loss — check login
  the same day, not capture day + 4.

**§13.2 addendum (2026-08-28, OOS day 4 = 08-27):** A is now **0-for-3** on
out-of-sample fills, and the third loss deepens the premise-check evidence in
one important way: this time the flow reading was NOT thin — r15 = −0.85B,
r30 = −0.69B, a genuinely negative episode — and the outcome was identical:
the 10:47 entry (bought 7475P @ 37.40 at S0 7712.86, first above-VT-all-day
session, VT 7675) bought the morning dip of a +55-pt rally day; 16.1 pts
adverse, timeout, −$70. So the failure is not fully explained by "flow gate
passes on noise" (the 08-25/26 hypothesis) — the deeper common factor across
all three is that close<mid30 + bounce30 fired at the morning low of an
up-trending day. Candidate (1) evidence: 3 episodes, 3 reversal-bottoms
bought. B: zero signals on 08-27 (one-way rally never armed a qualifying
run). Running OOS: 4 sessions, realized −$410; armed bomb marked +$35
(7380/7375, exp 09-25).

## 14. OOS days 5-7 (08-28, 08-31, 09-01): A works in its regime — 5-for-5 fills, zero losers (2026-09-02)

The strongest out-of-sample evidence yet, and it lands on the OTHER side of
the §13.2 story. Three sessions: 08-28 countable, 08-31 event_standdown
(month-end rebalance — R4.4 stood the engine down all day, exactly as
designed), 09-01 countable.

**Five A signals, five entries, five COMPLETED BOMBS, +$50, zero losers:**

| day | entry | legs (exp) | leg1 | fill in | credit |
|---|---|---|---|---|---|
| 08-28 | 11:19 | 7530/7525 (09-25) | 34.40 | 22 min | +$10 |
| 08-28 | 11:55 | 7525/7520 (09-25) | 37.80 | 2 min | +$10 |
| 08-28 | 12:04 | 7480/7475 (09-25) | 34.00 | 15 min | +$10 |
| 09-01 | 12:24 | 7375/7370 (10-02) | 40.90 | 4 min | +$10 |
| 09-01 | 12:40 | 7375/7370 (10-02) | 43.60 | 22 min | +$10 |

08-28 even hit the 3-entries/day cap (R6.4) with more qualifying signals
behind it — the cap did its job on a target-rich day.

**The discriminator between A's winners and losers is now legible: r30
depth.** The five winners fired on r30 = −4.7 to −5.7 $B (08-28 #2/#3, 09-01
both) — real, directional, put-buying flow — on days that were FALLING
(08-28: 7771 high → 7711 close; 09-01: below VT all day, low 7611). The
three §13 losers fired on r30 = −0.11 / −0.69 / −0.14* $B against rallies.
(*08-28 #1 is the instructive near-miss: r30 −0.14 — as thin as the losers —
but r15 −1.26 and a genuinely falling tape bailed it out in 22 min.) A
one-line candidate hypothesis for the R7.2 file: A's premise holds when the
30-min flow is deeply negative (|r30| ≳ 1-2 $B) and fails when close<mid30 +
bounce30 fire on flow noise; the current gate accepts both. Now 8 OOS episodes, honestly
split (correction per the 2026-09-02 Charlie/codex review): **4 wins on deep
r30 / 0 losses on deep r30 / 1 win on thin r30 (the 08-28 #1 exception —
rescued by r15 −1.26 and a falling tape) / 3 losses on thin r30**. A
suggestive 4/4-vs-1/4 pattern, NOT a clean single-variable discriminator —
and deep-r30 wins cluster in just two falling sessions, so the effect is
confounded with continuation regime. Not yet a rule change — the pattern is
registered here and keeps accumulating.

**Running OOS ledger (7 sessions, 6 countable + 1 standdown):** realized
−$360 (credits +$60, losers −$420); armed-bomb inventory SIX verticals
marked $585 at the 09-01 close (7380/7375 $75; 7530/7525 $120; 7525/7520
$120; 7480/7475 $130; 2× 7375/7370 $70) → **MTM +$225, first positive mark
of the out-of-sample period.** Every bomb is held at negative cost; the
09-25 expiries have 24 days to run, the 10-02s have 31.

**Ops/infra learnings:**
- **Expiry listing gap (new failure mode):** on 08-31 the convention expiry
  (Friday nearest 30 DTE = 10-02) did NOT YET exist at the vendor — the
  weekly was listed between 08-31 and 09-01. Protocol set: probe, and cache
  the day under the nearest LISTED Friday in [20,40] (08-31 → 09-25, 25
  DTE), which is what a live trader could actually have traded. No engine
  change — the cache manifest carries the expiry and `expiry_of` reads it.
  Live-path corollary: the same listing gap will eventually hit LiveChains
  on a real session; the spike/fallback should be checked before the
  shakedown.
- The SpotGamma web session expires in days, not weeks (second expiry in a
  week). The pool browser + fresh login recovers it; captures remain
  evening-only and staged.
- Store-manifest running totals had silently missed the 08-19/20/21
  partitions; totals are now recomputed from per-session entries (the
  authoritative source) — 15 sessions, 1,083,583 raw / 590,239 normalized.
