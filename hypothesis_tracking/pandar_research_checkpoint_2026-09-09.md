# Pandar research checkpoint — September 9, 2026

This checkpoint preserves the completed research before E-PNDR-014 changes the position-valuation hypothesis. The user requested a commit with extensive notes, then execution of the whole-position follow-up. There is no trading, deployment or provider acquisition implied by this checkpoint.

## Scope and history

The original task was to examine the inventory of Pandar-style trades, qualify actual strikes, and test same-day or later leg entries. The work grew through eligibility audits, wider delta searches, historical skew-journey analysis, a three-round Codex-only hypothesis program, historical quote-event checks, strike-richness explanations and two larger no-HIRO follow-ups. The completed artifacts retain these distinct scopes; later studies do not retroactively validate earlier examples.

The user subsequently excluded HIRO from the active experiments. E-PNDR-012 onward uses the existing 323 stock names as membership only. It has no HIRO feature, timing signal or coverage gate. Existing earlier HIRO code/results remain historical evidence. The authorized actual-event exclusion removes earnings on the signal or entry date and through the following 30 calendar days. This is retrospective event knowledge, not proof that a dated schedule was known at the time.

The shared acquisition budget is 2,000 calls, with 1,363 used at this checkpoint. The September 8 no-HIRO extensions used existing caches and zero new calls. Future acquisition must use the remaining shared budget, batch requests and preserve the ledger.

## What is actually sourced from Pandar

The source transcript documents selling overpriced calls, comparing expiry/strike pricing and sizing for substantial upside. It does not prescribe the project's 2–6, 2–10 or 5–15 delta bands, a ten-day expiry target, a fixed z-score threshold or automatic later call-spread conversion. The statement about not particularly following delta answered a put-strike question and should not be silently universalized. Pandar's documented naked-call example and Brent's preference for protected exposure are different positions, not interchangeable source claims.

The source transcript remains in the sibling repository at `/Users/dgrissen/Dev/delta_bomb-nvda_call_strat/docs/sources/discord_transcript_clean.txt`. Core references and exact calculation inputs are identified in the explanatory notes. Canonical global personas are simulations through native Codex agents, not actual comments from Charlie or Brent. No Claude or other model runner is claimed.

## Preserved research components

- `docs/replay/pandar_leg_timing_2026-09-05/`: renamed eligibility/leg-timing report, daily qualifying reasons, delta/%OTM/rank audits, call-exclusion investigation, expanded call search and early-put backfill. Preserve failed selections and unsupported quote cases.
- `docs/replay/pandar_skew_journey_2026-09-06/`: historical stock/surface panel, age/depth/rollover comparisons, 30/60-day realized-versus-implied tests, quote examples and persona reviews. Earlier descriptive associations use their original population and event-gate status.
- `hypothesis_tracking/`, `scripts/_research_loop/`, and the round artifacts in `outputs/`: the Codex-only PNDR hypothesis framework, completed original three-round pilot, immutable findings and follow-up index. Later experiments are separately frozen follow-ups, not an invented fourth verified round.
- `scripts/pandar_hypothesis_*.py` and `data/pandar_hypothesis_2026-09-07/`: population selection, API accounting, event metadata, exact entries, quote/tick replay, adverse exposure, prior surface-coordinate history, paired controls and reporting. The June pilot had five entry dates; warmup or richness-history observations must not be counted as trade days.
- `outputs/pandar_strike_selection_explainer_2026-09-08/`: source-grounded Charlie/Brent interpretation, exact MRVL inputs and cost/sensitivity arithmetic. The earlier replay picked expiry/delta first and measured richness afterward; ranking contracts by richness was a proposal, not an implemented feature of that replay.
- `scripts/pandar_no_hiro_surface.py` and `outputs/pandar_no_hiro_2026-09-08/`: completed E-PNDR-012 with causal feature freezes, broad candidate ledger, chronological and month-block comparisons, outcome censoring and combined plain-language report.
- `scripts/pandar_no_hiro_exact.py` and `outputs/pandar_no_hiro_exact_2026-09-08/`: completed E-PNDR-013 with deterministic source selection, all candidate checks, fixed signal contracts, next-session rechecks, quote-side costs, policy pairing, incomplete-risk labels, provenance diagnostics and independent validation.

## Important calculation corrections

1. ORATS daily `hiPx` and `clsPx` are already adjusted. A preliminary double adjustment of highs was corrected before final validation. Convert raw option-snapshot spot to that basis only when measuring subsequent underlying excursion. Primary IV outcomes were unaffected.
2. ORATS vega in the calculation is dollars per share per one IV point. Multiply by 100 for a standard contract, and keep decimal IV versus IV-point units explicit.
3. A standardized five-delta/ten-day surface is a moving coordinate, not the frozen option sold. Fixed-coordinate IV changes cannot substitute for exact-contract P&L.
4. Call-wing IV change, ATM-IV change and total call-IV change are separate quantities. Wing compression can coincide with rising total IV, and falling call IV can coincide with a losing short when stock rises.
5. The earlier project `call_kink` was a five-delta term comparison, not local strike curvature. A true strike residual needs valid neighboring quotes on both sides; a bid residual that disappears against neighbor asks is not established executable richness.
6. MRVL's illustrative June $425 call had a 14.95-point wing, but a two-point fall produced only about $17.87 local mark benefit against a $29.30 modeled round-trip hurdle. The apparent midpoint local kink was negative. Large z-scores alone did not establish an attractive sale.
7. A naked-call premium is cash received against an open liability. It is not earned profit and does not make a later long-call purchase free. A higher-strike protective call and lower-strike bullish conversion have different payoffs.
8. E-PNDR-013's linear wing recovery was capped at current ask value before outcome replay to prevent an impossible negative modeled buyback. Stopped pre-outcome run artifacts are preserved. The capped sensitivity remains a local approximation, not full repricing.

## E-PNDR-012 outcome

The panel has 921 background sessions from January 2023. The eligible high-wing evaluation contains **17,458 stock-dates, 304 stocks and 643 distinct signal dates**, January 2, 2024–August 4, 2026. Warmup is not counted as a traded day. A common nonoverlap reservation retains 6,364 cases. There are 32 month blocks, not thousands of independent market regimes.

The proposed slowdown state does not improve wing compression with ATM flat/up over two sessions after the next-session reference. The joint rates are **26.14% slowing/rolling versus 28.08% continuing/accelerating**. The raw difference is −1.94 percentage points; adjusted difference −0.91 points has an interval spanning zero. The three-condition rates requiring total call IV to fall are nearly identical, 13.27% versus 13.32%. This specification is not supported. It does not reject every possible form of mean reversion or prove that the alternative is a profitable call sale.

## E-PNDR-013 outcome

Exact-chain input eligibility covers **1,163 stock-dates, 71 stocks and 203 signal dates**. Four-session exits are priced for at least one policy in 552 cases across 139 dates and 42 stocks. Selection is based on signal/entry availability; future missing quotes do not remove candidate dates beforehand.

The economic selector searches all supported OTM calls in a 1–35 calendar-DTE envelope, without a narrow delta/%OTM band. It ranks estimated net benefit from removing a quarter of positive bid-IV-minus-spot-ATM wing against local 1%-rally loss. It chooses 107 signals, but 74 lose positive scenario economics at the actual next-session snapshot. The remaining 33 entries all belong to five names in the previously studied six-stock cache. No additional-name trade is discovered. Thirty-two priced trades average −$77.27.

The 273-case common nonoverlap sample has eight economic entries; all are priced and total **−$3,211.40**, with three positive outcomes. The control enters 260 times, with 129 priced exits and 131 censored exits. Across 142 observed paired cases, the economic-minus-control mean is +$38.72, with a 95% month-block interval [−$7.94, +$118.78]. This is inconclusive. On the same eight entered cases, the control loses $7,119.40: the apparent advantage is smaller losses. Another $1,590.30 of paired advantage comes from staying flat. Excluding the prior six leaves no economic entries.

All five measurable losing economic trades show actual wing compression. MRVL's May 29 $320 call loses $2,731.30 while its wing falls 16.96 points, ATM rises 30.88 points and stock rises from $205.47 to $316.56. ORCL's May 4 $210 call loses $105.30 even with a 5.46-point decline in total call IV. These examples motivate larger joint-position scenarios; they must not be used to tune rules until these particular losses disappear.

## Remaining limitations

The cache was acquired for earlier research, including a source explicitly named as winner recreation. Freezing source precedence does not undo that selection bias. Current membership applied backward also has survivorship limits. Chain truncation below five DTE causes substantial unequal exit missingness. Complete-case policy comparisons are not sufficient to establish superiority.

Full historical option deliverables, listed identity changes, quote-event freshness, assignment and American exercise are not comprehensively verified in the broad exact-chain extension. Standard 100-share contracts remain an explicit assumption. Broad comparable-delta/DTE and comparable-forward-moneyness/DTE histories do not satisfy the requested 60-prior-observation minimum everywhere. Missing history is unavailable, not extrapolated. No strategy is promoted as Pandar-approved or live-ready.

## Validation and reproduction

Use `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python` from this repository. E-PNDR-012's ten tests and nine artifact checks passed. E-PNDR-013's fourteen tests and Ruff passed; 3,072 input/source hashes and the selection/candidate freeze remained unchanged. The root independently reconciled all 1,402 priced policy/horizon cash flows, selection and entry counts, unique keys, the primary paired mean and report links. The checkpoint also runs the full existing `tests/` collection; its result is recorded in the commit message.

Large raw and generated datasets remain local. `pandar_checkpoint_artifact_manifest_2026-09-09.csv` records paths, sizes, SHA-256 hashes and inclusion decisions. This is a code/documentation/result checkpoint with a data inventory, not a promise that a fresh checkout contains every historical market-data input. Preserved manifests continue to identify external central-cache and sibling-repository dependencies. No data is deleted.

## Next authorized work

E-PNDR-014 must value the whole candidate position with nonlinear repricing under larger joint stock/ATM/wing scenarios, include hedge quotes and costs, and compare separate short-only, higher-strike protection and lower-strike conversion policies. The later lower-strike purchase needs its own fixed causal timing and benchmark; it must not inherit the protective call's payoff. A local kink is a supported-neighbor diagnostic, not assumed executable mean reversion. Freeze this specification and its selection inputs before reading its new outcome comparison; preserve failures and missing data, continue without HIRO, and do not call any result validated merely because a new score produces winners.
