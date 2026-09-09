# E-PNDR-013: preliminary exact-chain economics without HIRO

Frozen September 8, 2026 before reading this experiment's outcome prices. This is a cache-selected exploratory comparison, not an unseen test, certified historical richness, or a Pandar-prescribed rule. Pandar's original short-call sale motivates it; the numerical selector below is our proposal. No HIRO data or availability requirements.

## Sample and timing

Use the existing 323 stock names, signals from 2024-01-02 onward, and raw historical chains in the cache inventory produced before outcome selection at `outputs/pandar_no_hiro_2026-09-08/exact_chain_cache_inventory.csv`. Freeze that inventory's hash at the run start. Full-field signal and next-session chain presence determines input availability; retain absent later chains as censored outcomes. Resolve duplicate ticker/date sources deterministically: central_strikes first, then full-field sources before slim, then lexical path; do not inspect favorable prices to choose a source. Save the selected source for every required stock-date and flag conflicting copies rather than combining quotes.

Use daily quality and the authorized actual-event 30-day earnings gate from E-PNDR-012. Require coverage at signal and actual next-session entry. Do not require the summary five-delta wing rank to pass: this experiment searches the actual quoted options. Retain that rank, journey state, IV-versus-RV and year only as descriptive columns. Older six-stock histories have selection bias from the prior study; report results including and excluding CRM, DIS, MRVL, ORCL, PLTR and QCOM.

Signal EOD t chooses contracts. Entry uses next SPY session EOD quotes t+1. Here EOD means the provider's daily snapshot, often 15:46 ET, not a guaranteed 16:00 closing quote; preserve actual quote timestamps. Signal-day daily quality is already known before next-day entry; never gate that entry on its day's later official closing price or completed turnover. Close at the daily snapshot four sessions after entry (fifth holding session including entry). Also show two-session-after-entry results as a fixed secondary horizon. Reindex on the SPY calendar. Every source must identify the actual requested ticker/date; a later full chain is never a replacement for an absent earlier chain.

Common nonoverlap policy: earliest quality/earnings-clear input-available ticker-signal reserves through the maximum exit. Apply that same population to both selectors; do not release a reservation because an entry fails or its later outcome is missing. Save all dates and the common nonoverlap subset. Compare per-stock-date policy results, assigning zero only to known no-entry decisions; unknown execution or exit data remain censored. An active contract needs complete intervening quote/stock observations for an adverse-exposure estimate; incomplete intermediate coverage does not establish zero adverse exposure.

## Candidate contracts and measurements

Enumerate all listed calls with strike>signal spot, actual calendar DTE between 1 and 35, and expiry on or after the maximum closing date. No additional delta band or % OTM cutoff. Require positive bid, ask>=bid, both displayed sizes>=1, positive finite bid/mid/ask IV, finite delta strictly between 0 and 1, nonnegative finite gamma, positive vega and positive stock price. Preserve each failed candidate's reasons. This snapshot check does not establish event-level freshness, execution, deliverable identity or American exercise handling.

Use matched same-expiry spot-ATM call-mid IV, interpolating only between adjacent usable strikes bracketing spot; never extrapolate or skip an invalid closest bracket for a more convenient one. This is explicitly spot-ATM, not verified forward-ATM. Record all inputs. Wing Wk is 100×(callBidIV−matched ATMmidIV), in points.

For each standard 100-share contract, calculate:

- A common **scenario**, not expected return: raw local sensitivity to a fall of 25% of max(Wk,0) = 100×vega×0.25×max(Wk,0). **Pre-outcome valuation correction:** modeled gross recovery is the lesser of that raw estimate and 100×the current ask. This enforces a nonnegative hypothetical buyback ask; estimated net profit cannot exceed the sale premium minus modeled fees/slippage. Preserve the uncapped estimate and a ceiling-hit flag. The earlier linear proposal and aborted pre-outcome selection manifests remain available. This is a capped local approximation, not full nonlinear repricing.
- Estimated net scenario proceeds subtract 100×(ask−bid), two $0.65 fees, and $0.01/share adverse slippage on each side. Future quote width is assumed unchanged for this diagnostic only.
- Local loss for a 1% stock rally with strike IV fixed = 100×[delta×(0.01S)+0.5gamma×(0.01S)^2]. This denominator is a sensitivity comparison, not a bound on naked-call loss. Report its units and larger-move model limitations.
- Required IV-point decline to cover these costs = total modeled round-trip cost/(100×vega); required fraction of current positive wing = that value/Wk.
- An isolated-strike diagnostic: target mid and bid IV relative to adjacent valid strikes' log-strike interpolated mid, and target bid relative to interpolated neighbor asks. Require neighbors on both sides with usable quotes; unsupported kink remains unavailable. A positive raw residual is not a verified fair-value error or tradeable arbitrage.

The simple Greek approximation is a ranking hypothesis. It does not replace full nonlinear scenario pricing, a 60-observation comparable-delta/DTE and comparable-forward-moneyness/DTE richness history, or proof of quote freshness. Those requirements stay explicitly unmet where unsupported; no entry here is called Pandar-approved.

## Frozen selectors

Mechanical control: among valid candidates, choose expiry nearest ten calendar days (earlier expiry breaks ties), then the listed call nearest 0.10 delta (higher strike breaks ties). This is the previous style of mechanical choice, not a claim that Pandar uses ten delta.

Economic alternative: rank candidates by net scenario proceeds divided by the positive local 1%-rally loss. Break ties with narrower displayed spread, earlier expiry, then higher strike. If the maximum net proceeds are nonpositive, record `no_positive_net_scenario`; do not change the 25% assumption. Report all candidates and runner-ups so the selection is inspectable.

Keep each exact selected contract at actual entry. Recheck the same quote/OTM/expiry validity and supported spot-ATM measurement. For the economic alternative, require its recomputed net scenario proceeds to remain positive; otherwise record a failed entry with no replacement. Do not choose the highest-scoring different strike at entry. The control does not acquire this new scenario gate. Save entry delta/distance and signal-to-entry changes.

Sell at actual entry bid less $0.01/share, close at actual exit ask plus $0.01/share, and charge $0.65 per action. Never use midpoint as an assumed fill. Record observed EOD worst ask-to-cover mark where intermediate valid observations exist, plus underlying high exposure on consistent price basis. ORATS `hiPx` is already adjusted; use it directly. To normalize the actual entry-snapshot spot to that basis, multiply it by the entry-date `clsPx/unadjClsPx` adjustment factor, used solely for outcome measurement. Missing/ambiguous basis censors that excursion. Use subsequent sessions' highs; an entire entry-session high may precede the order and cannot establish post-entry exposure. This daily-high proxy still does not capture the exact intraday option loss. This is a conservative quote-side EOD replay under explicit conventions, not proof of fills or complete intraday risk. No long call is automatically added.

## Evaluation and interpretation

Report per-contract dollars, actual selected delta/%OTM/DTE, estimated versus observed economics, failures, censored entries/exits, and counts of ticker-dates, unique dates, stocks and nonoverlapping episodes. Policy comparisons share the same starting population; known no-entry receives zero policy P&L, unknown outcomes remain missing and require paired observed coverage for differences. Show trade-conditioned P&L separately. Do not equate many strikes with independent observations.

Primary comparison: economic-minus-mechanical net policy P&L at four sessions after entry, on paired observed common nonoverlap cases, with 2,000 reference-month block draws (seed 20260908) and individual chronological slices. Report all-signal sensitivity and exclude-prior-six sensitivity. Results are exploratory; no automatic promotion to a deployable strategy, especially where historical contract identity or full richness history is unavailable.

Reproduction: `scripts/pandar_no_hiro_exact.py`; outputs: `outputs/pandar_no_hiro_exact_2026-09-08/`. Tests cover deterministic selection, ATM no-extrapolation/invalid brackets, fixed-contract entry with no reselection, causal deadlines, costs, and missing-data versus known-no-entry policy outcomes. Use cached data only; the root owns any later provider requests under the existing shared 2,000-call cap.
