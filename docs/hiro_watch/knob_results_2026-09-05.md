# Branch-B knobs and the A×B×credit grid — portfolio replays through 2026-09-04 (diagnostic, not registered)

All replays: `hiro_engine_v2`, 18 sessions 08-12 → 09-04, marks at the 09-04 close (SPX 7718). Every
number is DISCOVERY data (16 sessions used to find the patterns + one confirmation session + one NFP
stand-down). The knobs live in `hiro_engine_v2/config.yaml` at v1-equivalent defaults; the byte-identity
test still passes. Registered candidates unchanged.

## Singles on v1

| variant | A trades/bombs · cash | B trades/bombs · cash | cash | bombs | inventory | MTM | vs v1 |
|---|---|---|---|---|---|---|---|
| v1 baseline | 24/13 · −1,210 | 7/3 · −260 | −1,470 | 16 | +590 | −880 | — |
| `adepth` (a_r30_lt −4) | 5/5 · +50 | 10/3 · −620 | −570 | 8 | +300 | −270 | +610 |
| `pull8` (b_pull_min_pts 8) | 24/13 · −1,210 | 2/2 · +20 | −1,190 | 15 | +575 | −615 | +265 |
| `size1` (b_run_max 1.0) | 24/13 · −1,210 | 5/4 · −40 | −1,250 | 17 | +610 | −640 | +240 |
| `boff` (b_enabled false) | 24/13 · −1,110 | 0/0 | −1,110 | 13 | +535 | −575 | +305 |
| `credit0` (credit_b 0.00) | 24/13 · −1,160 | 7/3 · −290 | −1,450 | 16 | +590 | −860 | +20 |
| `age15` (b_dur_max 15) | = v1 | = v1 | −1,470 | 16 | +590 | −880 | 0 |
| `sticky` (late_sticky) | = v1 | = v1 | −1,470 | 16 | +590 | −880 | 0 |

`age15` and `sticky` are no-ops on v1: the trades they target were capacity-refused in v1 anyway.

## Combined with the A gate (−4)

| variant | A | B | cash | bombs | inventory | MTM | vs v1 |
|---|---|---|---|---|---|---|---|
| `pull8 + adepth` | 5/5 · +50 | 2/2 · +20 | +70 | 7 | +285 | +355 | +1,235 |
| `pull8 + credit0 + adepth` | 5/5 · +50 | 2/2 · 0 | +50 | 7 | +285 | +335 | +1,215 |
| `boff + adepth` | 5/5 · +50 | 0/0 | +50 | 5 | +245 | +295 | +1,175 |
| `size1 + adepth` | 5/5 · +50 | 6/4 · −100 | −50 | 9 | +320 | +270 | +1,150 |
| `age15 + adepth` | 5/5 · +50 | 8/3 · −320 | −270 | 8 | +300 | +30 | +910 |
| `sticky + adepth` | 5/5 · +50 | 9/3 · −540 | −490 | 8 | +300 | −190 | +690 |
| `credit0 + adepth` | 5/5 · +50 | 10/3 · −650 | −600 | 8 | +300 | −300 | +580 |

## The grid (60 cells): A gate {none, −1, −2, −3, −4} × B filter {none, run ≤ 1.0, pull ≥ 5, pull ≥ 8} × A credit {0.10, 0.20, 0.30}; B credit 0.10
Full table: `docs/replay/hiro_watch/diagnostics/grid_2026-09-05_a_depth_x_b_filter_x_a_credit.csv`.
Objective the owner set: highest N of completed bombs on both branches, with the A credit used to
offset the small failures.

| A gate | B filter | A credit | trades | bombs | A | B | credits | failed | cash | inv | MTM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| none | run ≤ 1.0 | 0.30 | 29 | 17 | 24/13 | 5/4 | +430 | −1,420 | −990 | +610 | −379 |
| r30 < −1 | run ≤ 1.0 | 0.30 | 25 | 15 | 20/11 | 5/4 | +370 | −990 | −620 | +555 | −64 |
| **r30 < −2** | **run ≤ 1.0** | **0.30** | 16 | **12** | 11/8 | 5/4 | +280 | −120 | **+160** | +460 | **+620** |
| r30 < −2 | run ≤ 1.0 | 0.10 | 16 | 13 | 11/9 | 5/4 | +130 | −170 | −40 | +480 | +440 |
| r30 < −2 | pull ≥ 8 | 0.30 | 13 | 10 | 11/8 | 2/2 | +260 | −40 | +220 | +425 | +645 |
| r30 < −3 | run ≤ 1.0 | 0.30 | 12 | 10 | 7/6 | 5/4 | +220 | −190 | +30 | +360 | +390 |
| r30 < −4 | run ≤ 1.0 | 0.30 | 11 | 9 | 5/5 | 6/4 | +190 | −140 | +50 | +320 | +370 |
| r30 < −4 | pull ≥ 8 | 0.30 | 7 | 7 | 5/5 | 2/2 | +170 | 0 | +170 | +285 | +455 |

Findings: no-gate is never cash-positive at any credit (24 A trades' failures swamp it); −2 is the
highest-N gate that turns cash positive (A 11/9 vs −4's 5/5; v1's 17 shallower A trades were 8 bombs
and −$1,170); 0.30 on A adds +$20 per A bomb and cost one A fill in the −2 rows (11/9 → 11/8); `run ≤
1.0` keeps B at 5/4 (80 %) vs `pull ≥ 8`'s 2/2; every dime on B costs a bomb (3 → 2 → 1).

## Owner's pick for the higher-N objective: `r30 < −2` + `run ≤ 1.0` + A credit 0.30 / B 0.10
16 trades on 8 of 18 days; 12 bombs (A 8, B 4); credits +$280; failures −$120 (one −$110 timeout,
one −$80 scratch, two timeouts that closed +$50/+$20); cash +$160; inventory +$460; MTM +$620.
Per-trade list in the session log of 2026-09-05. Fragility: the B cap sits on a knife (best B win had
run 0.996 $B); the whole cell is one of 60 chosen on the data it was fitted to.

## Why the B cap works (mechanism)
The ten B trades split cleanly on run size: ≤ 1.0 $B → 5 trades, 4 bombs, −$40; > 1.0 → 5 trades, 0
bombs, −$510 (2 scratches, 3 veto exits — every failure was the wave stalling). A run is the total
upward hedging pressure since the wave began; above a billion most of the dealer buying it implies has
already happened. The LATE rule measures speed and the last 30 minutes, not accumulated size, which is
why it let 08-25 11:37 through three minutes after suppressing it. The floor stays: 10 min × 2 $B/hr.
