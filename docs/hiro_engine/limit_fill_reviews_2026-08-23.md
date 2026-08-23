# v3.0 limit-fill proposal — review records (2026-08-23)

## Codex plan review (gpt-5.6-sol, verbatim verdict + findings)
```
Verdict: **FAIL**

The core resting-limit idea is sound, but the proposed deltas do not yet compose into an executable v3.0 specification. Three issues can directly produce completed trades or scorecard results that violate the stated mechanic.

1. **BLOCKER — R7.6 violates the defining invariant.**  
   R7.6 still permits `resolution_debit` when the partner can be purchased/sold for up to a $0.50 debit. Example: sell leg 1 at 20.00, then buy K+5 at 20.50 at resolution. That creates a completed spread with a $50 debit, not a $10 credit.  
   **Required:** R7.6 may complete only if the original resting limit fills. Otherwise close the lone leg. Every path classified as a completed bomb must book leg 2 at the limit and produce credit ≥ configured credit.

2. **BLOCKER — Minute timing permits look-ahead and false same-minute fills.**  
   “Leg 1 books from the execution minute’s NBBO” and “live uses the post-bar-close snapshot” are incompatible with “next-bar open.” If leg 1 is booked from the 10:01 post-close quote and leg 2 is tested against the same 10:01 quote, the qualifying partner quote may have occurred before leg 1 existed. The same ambiguity affects next-bar NBBO exits.  
   **Required:** Pin one causal sequence, including the first fill-eligible minute. For example: signal at minute *t* close → book leg 1 from the *t+1* snapshot → submit leg 2 after that snapshot → first fill test at *t+2*. Alternatively, obtain a genuine next-open snapshot. Update R7.0, minutes-to-fill, resolution timing, and adverse-window boundaries accordingly.

3. **BLOCKER — Fill precedence has no owner after fill detection leaves RuleEngine.**  
   The existing contract makes RuleEngine the owner of R7 precedence. The proposal moves fill detection into Executor while saying RuleEngine remains otherwise untouched. Scenario: in one minute the option quote fills the resting limit and R7.2 scratch fires. RuleEngine emits scratch; Executor separately sees fill. Nothing specifies which event survives or prevents contradictory log rows.  
   **Required:** Session must attach quotes before exit evaluation, and one pure arbitration point must evaluate `fill > scratch > cap > …`. Executor should apply the winning decision only. This can remain in RuleEngine via an attached `limit_fill=True`, or in a dedicated pure exit arbiter—not through competing decisions.

4. **MAJOR — Option-quote failure semantics and R9 denominators are missing.**  
   Full-tier “chain cache exists for date” does not establish complete quotes over each trade horizon. If quotes disappear for 20 minutes and the market crosses the limit during that gap, the engine may record a timeout and include it as a failed fill. Live has the same problem, while the accepted amendment correctly forbids an SPX fill fallback.  
   **Required:** Add `OPTION_DOWN`/`QUOTE_MISSING` behavior covering:

   - no valid quote at entry: do not open; define whether the signal remains qualifying;
   - missing leg-2 quotes while resting: mark the outcome unscorable/data-invalid rather than a no-fill;
   - missing quote for a non-fill exit: define fail-closed booking;
   - session PARTIAL/countability policy and exact R11.6 denominator treatment.

5. **MAJOR — R9/R11 still mix SPX proxies with option-dollar economics.**  
   The table misses changes to R11.2, R11.3, the best-session tie-break, would-have-completed scratches, and heartbeat semantics.

   Concrete breaks:

   - R11.3 still computes P&L from `S0`, although exits now book option NBBO.
   - R9 still asks whether a scratch’s “fill touch” later printed; this must replay the resting option limit.
   - R11.2 excludes the old SPX touch bar. Under a post-close quote fill, the fill-minute SPX range occurred before the observed fill and should normally be included.
   - Heartbeat “adverse” remains SPX points while new risk gates are option dollars.

   **Required:** Define separate fields and denominators: `spx_adverse_pts` as contextual excursion and `leg_realized_pnl_dollars`/conservative liquidation loss as economic risk. State which drives each R9 line and the best-session tie-break.

6. **MAJOR — R11 controls require substantially more chain data than Task 13 caches.**  
   Actual trades need a full-chain snapshot only at their signal minute plus two strikes thereafter. R11.4 evaluates every eligible minute; each control candidate needs its own expiry/−0.20Δ selection, next-minute leg-1 quote, partner limit, and complete horizon. That is potentially thousands of signal-time chain selections over eight sessions, not “the day’s entries.”  
   **Required:** Give control generation a separate bounded data contract and manifest. Define candidate-minute timing, strike selection, missing quotes, partner-listing failure, and complete-horizon eligibility. Prefer persisting a hash-pinned derived control frame after validation rather than retaining whole-chain full-day data.

7. **MAJOR — Threshold re-registration is not mechanically pre-registered yet.**  
   “Set thresholds and sample minimums in one sitting” remains discretionary. The accepted `point estimate − one bootstrap SD` rule only explains fill-rate floors; it does not derive branch sample minimums, total fills, sessions-with-fill, control margins, median loss, or maximum loss. Running the rehearsal before those formulas are frozen defeats the anti-overfit claim.  
   **Required:** Split Task 16 into:

   1. freeze every criterion’s form, denominator, transformation from 8 rehearsal days to a 10-session exam, rounding, and defect/rerun policy;
   2. hash that preregistration;
   3. run the rehearsal once and mechanically populate numbers.

8. **MAJOR — The verification chain remains circular/inaccurate.**  
   The v1 artifact does not represent a v3 full-tier replay; [build_notes.md](/Users/dgrissen/Dev/delta_bomb/docs/hiro_engine/build_notes.md) already records that it verifies legacy research semantics through `verify.py`. The proposal again describes it as an existing full-tier golden gate. Meanwhile, a v2 artifact produced by the new implementation and merely spot-checked cannot independently prove that implementation.  
   **Required:** Keep two explicitly separate gates:

   - legacy core-port verification using v1 and its legacy mode;
   - a small independently hand-calculated v3 fixture covering both sides, boundaries, same-minute conflicts, exits, missing quotes, and rounding.

   Then pin the v2 trade artifact, raw chain manifest, control artifact, and preregistration hash in CONFIG.

9. **MAJOR — The task list omits or misorders critical gates.**  
   Add ownership for R10 option health, Session quote attachment/arbitration, InstrumentSelector’s historical-chain path, R6.1/R6.2/R6.5 display/anchor changes, price-tier schema behavior, option-dollar scorecard metrics, and cache hashes in CONFIG. Move the live feasibility spike before live integration—and ideally before most pricing work. The spike must test both full-chain strike selection at signal time and two-strike cadence afterward; “two strikes” alone does not validate the live workflow.

10. **minor — Accepted amendments are not actually applied to the proposal.**  
    [limit_fill_upgrade_proposal.md](/Users/dgrissen/Dev/delta_bomb/docs/hiro_engine/limit_fill_upgrade_proposal.md) still contains material contradictions:

    - Executor queries ChainStore despite the accepted I/O-free Session design.
    - Credit sweep is `{0.05, 0.10, 0.15, 0.20}` versus accepted tick-valid `{0.00, 0.10, 0.20, 0.30}`.
    - SPX touch supposedly survives “only” in controls, is then retired from controls, yet survives in price tier.
    - Task 13 does not contain the accepted precise cache scope.
    - Task 17 tests SDK only, while the accepted gate is SDK **or** Schwab.
    - A/B/D remain labeled open after being decided.

11. **minor — The credit sweep and production SPX-touch diagnostic are overengineering.**  
    The requested faithful mechanic has a frozen $0.10 floor. Adding a credit optimization surface immediately creates another tuning opportunity without supporting the live-paper objective. Remove the sweep knob for v3.0. If historical comparison is useful, compute the old SPX-touch result once in the offline verification report rather than adding it throughout production state and logging.

Feasibility risks, ranked:

1. **Live quotes — high:** hard go-live dependency; must prove full-chain selection, two-strike freshness, timestamp semantics, failure behavior, and the five-second budget.
2. **Control-data volume — high but containable:** actual-trade caching is small; per-minute matched controls are the volume multiplier. A derived, hash-pinned control artifact keeps this bounded.
3. **Threshold re-registration — medium technical risk, high governance risk:** straightforward once formulas are frozen, but currently under-specified enough to invalidate the acceptance test.

The minimal faithful v3 is narrower than the current proposal: real chain selection, conservative leg-1 booking, one resting $0.10-credit limit, causal quote-fill arbitration, conservative lone-leg exits, option-data health handling, and a re-derived scorecard. Everything else should wait.
hook: Stop
hook: Stop Completed
tokens used
113,051
Verdict: **FAIL**

The core resting-limit idea is sound, but the proposed deltas do not yet compose into an executable v3.0 specification. Three issues can directly produce completed trades or scorecard results that violate the stated mechanic.

1. **BLOCKER — R7.6 violates the defining invariant.**  
   R7.6 still permits `resolution_debit` when the partner can be purchased/sold for up to a $0.50 debit. Example: sell leg 1 at 20.00, then buy K+5 at 20.50 at resolution. That creates a completed spread with a $50 debit, not a $10 credit.  
   **Required:** R7.6 may complete only if the original resting limit fills. Otherwise close the lone leg. Every path classified as a completed bomb must book leg 2 at the limit and produce credit ≥ configured credit.

2. **BLOCKER — Minute timing permits look-ahead and false same-minute fills.**  
   “Leg 1 books from the execution minute’s NBBO” and “live uses the post-bar-close snapshot” are incompatible with “next-bar open.” If leg 1 is booked from the 10:01 post-close quote and leg 2 is tested against the same 10:01 quote, the qualifying partner quote may have occurred before leg 1 existed. The same ambiguity affects next-bar NBBO exits.  
   **Required:** Pin one causal sequence, including the first fill-eligible minute. For example: signal at minute *t* close → book leg 1 from the *t+1* snapshot → submit leg 2 after that snapshot → first fill test at *t+2*. Alternatively, obtain a genuine next-open snapshot. Update R7.0, minutes-to-fill, resolution timing, and adverse-window boundaries accordingly.

3. **BLOCKER — Fill precedence has no owner after fill detection leaves RuleEngine.**  
   The existing contract makes RuleEngine the owner of R7 precedence. The proposal moves fill detection into Executor while saying RuleEngine remains otherwise untouched. Scenario: in one minute the option quote fills the resting limit and R7.2 scratch fires. RuleEngine emits scratch; Executor separately sees fill. Nothing specifies which event survives or prevents contradictory log rows.  
   **Required:** Session must attach quotes before exit evaluation, and one pure arbitration point must evaluate `fill > scratch > cap > …`. Executor should apply the winning decision only. This can remain in RuleEngine via an attached `limit_fill=True`, or in a dedicated pure exit arbiter—not through competing decisions.

4. **MAJOR — Option-quote failure semantics and R9 denominators are missing.**  
   Full-tier “chain cache exists for date” does not establish complete quotes over each trade horizon. If quotes disappear for 20 minutes and the market crosses the limit during that gap, the engine may record a timeout and include it as a failed fill. Live has the same problem, while the accepted amendment correctly forbids an SPX fill fallback.  
   **Required:** Add `OPTION_DOWN`/`QUOTE_MISSING` behavior covering:

   - no valid quote at entry: do not open; define whether the signal remains qualifying;
   - missing leg-2 quotes while resting: mark the outcome unscorable/data-invalid rather than a no-fill;
   - missing quote for a non-fill exit: define fail-closed booking;
   - session PARTIAL/countability policy and exact R11.6 denominator treatment.

5. **MAJOR — R9/R11 still mix SPX proxies with option-dollar economics.**  
   The table misses changes to R11.2, R11.3, the best-session tie-break, would-have-completed scratches, and heartbeat semantics.

   Concrete breaks:

   - R11.3 still computes P&L from `S0`, although exits now book option NBBO.
   - R9 still asks whether a scratch’s “fill touch” later printed; this must replay the resting option limit.
   - R11.2 excludes the old SPX touch bar. Under a post-close quote fill, the fill-minute SPX range occurred before the observed fill and should normally be included.
   - Heartbeat “adverse” remains SPX points while new risk gates are option dollars.

```

## Red-team audit (agent, condensed findings)

VERDICT: FAIL (4 blockers, 5 majors) on draft 1 — all resolved in proposal v2:
1. BLOCKER R1.4 vs R11.4/R11.5 contradiction (touch "survives in controls" AND
   "retired from controls") → resolved: touch fully retired; controls use the
   limit-fill indicator from a pinned derived control frame.
2. BLOCKER controls uncomputable from the amended cache scope → resolved:
   full-day full-chain caches + controls_build → hash-pinned control frame.
3. BLOCKER R7.6 resolution_debit (≤0.50 debit completion) falsifies "+$10 by
   construction" → resolved: resolution_debit RETIRED; completed bomb ==
   leg 2 booked at L, credit ≥ 0.10, invariant.
4. BLOCKER cancel semantics absent (limit vs scratch/veto/clock/resolution;
   same-minute race; entry-minute self-fill) → resolved: §1.4-1.5 of the
   proposal (cancel at decision close; fill wins; first eligible minute t+2).
5. MAJOR R11.2/R11.3/heartbeat/would-have-filled still in SPX-touch units →
   resolved: two unit families; $ drives R9; touch replay replaced by limit
   replay.
6. MAJOR 1-min NBBO flicker honesty → mitigated: closing-snapshot convention
   + margin logging + 2-consecutive-minute sensitivity column (report-only);
   residual risk accepted and documented.
7. MAJOR live/backtest parity asserted not tested → resolved: parity diff
   test with pre-registered tolerance as a shakedown gate (task 18).
8. MAJOR chain cache unpinned (vendor re-fetch nondeterminism) → resolved:
   chain manifest sha256 + SDK version into CONFIG (R8.2); artifacts declared
   cache-relative.
9. MAJOR threshold floor ill-defined at small n; form chosen post-peek →
   resolved: empty-resample rule, 0.10 hard floor, minimums carried over
   unchanged, form+formulas frozen and hashed BEFORE the first v3 run (16a).
10. minor leg-1 booking instant skew → resolved: end-of-minute NBBO both paths.

## Prior context in this decision chain

- docs/replay/hiro/bomb_repricing_2026-08-23.csv — the 19 rehearsal trades
  repriced at real SPXW chain mids: completed bombs avg $46 legging cost (not
  ~$0); failed legs −$170 total; spreads marked +$995 at completion; net MTM
  +$135. The gap between the ±3-touch proxy and real economics is what
  motivated v3.0.
- Trade sparsity probe: a bomb strike traded 6 of 391 minutes → fill detection
  must be quote-based (marketable NBBO), not trade-OHLC.
- Architect × PM amendments (draft 1): Executor I/O-free, additive schema v2,
  tick-valid pricing, live-quotes hard gate, $10-is-floor-not-objective.
