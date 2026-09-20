# B09 opportunity expansion and volume: fixed execution protocol

Authorized September 20, 2026. Execute the three proposals in the preceding
research review plus its separate volume experiment. Prepare the short-dated
sector/constituent pilot without running its outcome test or collecting data.
This is additional exploration on reused history, not an untouched holdout.

Reference: existing B09 sector F4 OR SPX_F, full cohort, no spacing, on the same
239 non-development research dates in 2025–September 18, 2026. Keep original
native SPX prices, causal above-VT eligibility and +5 before −10 within 60 native
minute bars including entry. Only target_first wins; other labels remain in N.
No post-target test, new trading hours, threshold sweep or combined multi-test winner.

## Comparisons fixed before new outcomes

1. Base OR union existing B05 F4. Deduplicate exact date/known_min executions.
   Check duplicate outcomes/prices agree. Score additions separately from base.
2. SPY RVOL: volume in the five completed minutes T−5…T−1 divided by the median
   volume in the exact same clock interval over the 60 preceding SPY-cache session
   dates. Require all five actual nonnegative finite observations on current and
   all 60 historical sessions, plus positive median. No filling absent rows with
   zero. Use RVOL>1 versus <=1; equality is no. No new cutoff or lookback search.
   Missing current dates remain unknown. Historical calendar completeness is an
   assumption of the existing exchange-date cache; report its source and limitations.
   This is Nasdaq-venue SPY volume, not consolidated SPX/US volume.
   Compare both within base OR and within all B09 parents, on common observed
   coverage. Publish the OR-state × RVOL-state table. A new OR-volume union is
   not authorized: the rejected-parent cell is diagnostic only. Report source
   support, prior-30-minute SPX return and realized price volatility balance,
   and same-date/09:30-anchored-hour yes/no contrasts. These are descriptive
   controls, not complete matching or causal isolation of volume.
3. Five-minute IV persistence on B09: u in {T−5,…,T−1}. Sector admission requires
   one common u with at least four identical ETF identities satisfying M(u)>1,
   b2(u)<−1e−12 and observed b2(T−1)<−1e−12. Current source eligibility must be
   valid (finite current M and b2). SPX has the same rule with one instrument.
   OR the two routes; preserve unknowns. No assembling votes from different
   timestamps. Earlier unavailable endpoints remain unknown. Exact T−1 is
   included, so every current OR yes must remain yes. Use each endpoint's own
   previously computed causal baseline, including across calibration-hour boundaries.
4. Base OR union B07 original_accelerating_6 from the frozen prior-IV experiment.
   Restrict to the identical 239-date calendar. Preserve original quote policy,
   six-of-eleven rule, complete T−35…T−6 reference and existing memberships.
   Do not substitute MAD F4, newer window timing, or the old full-calendar rate.

Run each expansion independently against the same reference. Do not combine all
three expansions. For every union: all entries primary; first/day and greedy
60-minute spacing from the full chronological union as sensitivities. Filtering
precedes thinning. Re-thinning may displace existing entries: report newly kept
and displaced executions/winners, not just the raw set difference.

## Opportunity, attribution and uncertainty

For pooled and every half: target/adverse/neither/ambiguous, N, dates, median N
per research date, union and added-only hit rates, new active dates, exact-time
duplicates, and additions within 60 minutes of a base entry. The latter is an
overlap diagnostic that may look forward and MUST NOT be used as an admission gate.
Preserve the poor/sparse partial 2026 H2 and do not give it decisive weight.

Whole-date percentile bootstrap: 5,000 shared draws, seed 20260920, within each
reported period using its research calendar including zero-entry dates. Report
union-minus-base and rate intervals, finite draws, support and clear unestimable
cases. These are descriptive and unadjusted for prior search/cross-day dependence.
Leave one date out for base and each expansion, and report winner concentration.
No claim of noninferiority based on a nonsignificant difference or an invented margin.

## Provenance and verification

Reuse hashed source memberships/events/calendar and exact sector/SPX scored-window
caches. Prepare and hash new memberships, volume features and source support
before joining new outcome groups. No quote repair or provider call. Reconcile
base198/318 and B05F4 70/112; replay original B07 votes against its sector-feature
table; replay persistence with an independent scalar implementation, including
same-sector/current-slope constraints and source timestamps. Verify deduplication,
thinning, native above-VT/outcome agreement, and every summary count.

New data only under
`/Users/dgrissen/Dev/central_trade_data/thetadata/b09_opportunity_expansion_2026-09-20-v1`.
Code, full findings, learning notes, pilot design and extensive commit notes live
in the project. Commit only these changes and the explicitly related idea/day-
influence notes; preserve unrelated work. No independent Claude review is claimed.
