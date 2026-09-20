# Prepared pilot: short-dated sector and rising-constituent skew

Status: **measurement pilot prepared; collection, measurement and outcome testing
not performed.** This preserves the user's corrected hypothesis. The earlier
SPX experiment was30-day ATM acceleration; it does not answer this question.
Older sector30-day skew diagnostics also do not establish the new hypothesis.

## Concrete first scope

- Ten research dates, sampled with seed20260920 without reading outcomes:
  three each from2025H1,2025H2,2026H1 and one from partial2026H2. These are reused
  research dates; random sampling here makes a measurement pilot, not a holdout.
- All eleven existing sector ETFs. Raw minute observations09:30–14:29 ET;
  each entryT can use onlyT−30…T−1, matching the B09 study's clock.
- Proposed fixedseven-calendar-day tenor, ATM and25-delta call richness; retain
  the25-delta put wing as a diagnostic. Seven days is a design choice, not an
  optimized or demonstrated best tenor.
- A second measurement phase uses the three largest holdings of each ETF as
  known before that pilot session, using the most recent prior-published holdings.
  Three names is a collection-budget limit, not a proposed trading threshold.
  Membership can change by date. Do not substitute today's winners or current
  holdings. Do not promote a top-three result as evidence about the entire sector.

`skew_pilot_dates.csv` and `skew_pilot_preparation.json` in the central experiment
namespace are the concrete calendar and readiness record. `prepare_pilot.py`
reproduces them without loading outcomes.

## Availability before collection

The existing sector-MAD protocols use a30-day target and8–65DTE expiry brackets.
Those selected quote caches cannot certify a properly bracketed7-day surface.
Native contract listings may help inventory availability, but listed contracts
alone do not prove usable historical minute quotes or deltas. Do not interpolate
outside a bracket or silently substitute30DTE for missing7DTE.

The inspected central reference catalogue contains historicalIVV weight snapshots.
Those are not each sector ETF's historical holdings. Prior-published sector
holdings, constituent identities, publication timing, native price observations
and short-tenor option coverage must be established before phase two. An inability
to obtain a dated holdings snapshot remains a coverage failure, not permission
to reconstruct the past from today's constituents.

If acquisition proceeds, use the ThetaData Python SDK for native one-minute
`option_history_greeks_implied_volatility` and first-order Greeks, plus underlying
OHLC/quotes and dated contract listings as required. Save native requests,
responses, selection receipts and derived data under `~/Dev/central_trade_data/`.
Provider access and exact endpoint parameters must be checked at execution time;
this preparation made zero provider calls and did not change any shared service.

## Measurement question

For each instrumenti, including each constituent separately:

`C_i = IV_i(25-delta call,7D) − IV_i(ATM,7D)`

Fit actual-time OLS slopesb1 andb2 to the first and second15-minute halves of
the same30-minute reference. Strengthening meansb2>0. Acceleration is the
two-slope proxy`a_C=(b2−b1)/15`; positive means strengthening is speeding up.
IV uses volatility percentage points, slope points/minute and acceleration
points/minute². These signs are different from the negative ATM-IV acceleration
used by currentF4. A call wing can strengthen while remaining below ATM IV.

Pair these measurements with the same instrument's observed return over exactly
the same reference. A constituent's positive price return is known atT−1, not
the future session close. First compare similar price rises with and without
skew strengthening; then ask whether acceleration adds information among cases
where skew is already strengthening. Do not credit acceleration for the effect
of stronger price or first-derivative movement.

RetainATM IV andput richness separately. A call-minus-put risk reversal can
improve because puts cheapen; this is not identical to upside calls getting
richer. Constant delta, expiry interpolation, earnings timing and spot changes
can move computed IV. Inspect actual bid/ask changes and same-contract traces;
fresh quote timestamps with unchanged option prices are not proof of new flow.
Use midpointIV for the coordinate, with quote/IV validity and spread information
recorded. A missing bid-IV calculation is not automatically a valid recovery.
Inherited recovery guards require explicit short-tenor measurement validation.

## Pilot deliverables and stopping conditions

Produce coverage by date/instrument/minute/coordinate; actual expiry and strike
brackets; raw and derived timestamps; midpoint/bid/ask IV support; interpolation
weights; slope/acceleration traces and quote uncertainty. Identify whether
apparent curvature is supported by multiple usable observations rather than one
outlier or stale-price/spot interaction. Do not pretend a conservative bid/ask
envelope is a statistical confidence interval.

For constituent summaries retain the full declared weight denominator, including
unobserved weight. Report price-rising, skew-strengthening and unknown weight
separately. Top-three pilot measurements do not authorize full-sector breadth
claims. Sector-ETF weights also are not automatically exactSPX contribution weights.

If short-tenor brackets, quotes, historical holdings or measurement stability fail,
report that obstacle. Do not loosen guards, replace instruments, change delta,
extend tenor or select a different group after looking at outcomes. Before an
eventual accuracy test, freeze aggregation, eligibility and any one admission
threshold separately. No second-derivative/MAD threshold grid is authorized.

The orthogonal transaction-pressure/order-book idea remains a separate queued
hypothesis. OHLCV and minute-end quotes do not reconstruct true order-book flow.
No syntheticHIRO engine is required or proposed for this preparation.
