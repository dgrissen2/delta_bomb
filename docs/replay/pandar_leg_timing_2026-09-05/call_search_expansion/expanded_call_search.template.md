## Wider call search and a controlled delta-band comparison

**The delta band was only part of the omission.** Keeping 2–6Δ but removing the
additional IVR, RR, kink, opposite-wing, trend and near-front-event surface vetoes
finds **51 quote-qualified stock-days across 23 names**. Widening that broader search
to **2–10Δ finds 73 stock-days across 33 names**.
The comparison keeps the contract quote, OI, selected midpoint-wing and selected-expiry
earnings checks fixed. It does not select on subsequent profit.

Discovery checked **413 stock-days across 134 stocks** with front 5Δ/10D call-wing
rank ≥85, within the existing liquid-stock universe. This remaining rank threshold
is also a project proxy. It is a broader search, not an exhaustive inventory of
everything Pandar might trade. September 4 remains unavailable. **TFC August 19** has
no OTM call with a nearer strike in the returned 1–30-DTE slice; that coverage
limitation is retained in the ledger rather than treated as a complete chain rejection.

{{bands}}

Counts are ticker/dates with at least one qualifying contract, followed by distinct
stock symbols; they are **not independent trades**. One contract is shown per date:
earliest passing expiry, then closest to 4Δ. The all-contract ledger retains the other
choices. Widening the band can change the selected expiry/strike even on an existing
passing date. The 13–19-DTE fallback is shown separately from the front 5–12-DTE bucket.

For the **original 24-row surface**, fixing selection recovers three dates: **6 → 9**.
Widening only its delta band to 2–10 adds **SMCI Aug 13 and JNJ Aug 24**: **9 → 11**.
The broader surface contributes the other **62** dates at 2–10Δ: **11 → 73**.
Thus neither “only MSTR qualified” nor “the delta band caused all the omissions” is accurate.

**Use 2–10Δ as the next research search envelope**, with 2–6 as its benchmark,
while treating both as project parameters. Retain % OTM and approximate ATM
expected-move units separately: SMCI's 9.26Δ call was 24.78% OTM; JNJ's 9.43Δ call
was only 3.56% OTM. The latter needs a separate far-tail judgment. No outcome-based
optimal delta band has been established. Selection nearest 4Δ is a reproducibility
convention, not evidence that it is the richest strike; subsequent richness review
should compare all the passing strikes.

The shared scanner now checks every candidate's quote before selection, tries later
expiries when needed, and accepts an explicit **--call-delta-max 0.10** override.
Its original default remains reproducible. **22 scanner tests pass**, and its selections
agree with the independent audit for **826 comparisons across all 413 stock-days**.

### Are the actual calls rich enough to sell?

The midpoint wing check alone is insufficient. Among the 73 selected 2–10Δ calls:

- **65** have bid IV at least two points above the same-expiry nearest-50Δ call's midpoint IV.
- **71** have a supported 20–30-DTE matched-delta comparison; **37** have front bid IV
  above that deferred midpoint IV.
- **33 selected calls** pass both diagnostics. Their deferred expiries also fall
  before the signal-day earnings estimate. This is a review subset, not a new
  backtested admission rule or proof of overpricing.

For example, **MRNA Aug 24, Aug 28 195C**, was 3.15Δ / 40.24% OTM with a
$0.26/$0.36 quote, bid IV **32.96 points above ATM** and **38.10 points above the
deferred matched-delta mid IV**. It was excluded by the within-5%-of-high rule.
**NVDA Aug 26, Aug 31 242.5C**, was 3.72Δ / 15.70% OTM at $0.34/$0.35;
its corresponding excesses were **+6.82 / +25.99**. Negative recent return, IVR below 30,
and distance from the recent high hid it. **TSLA Sep 2, Sep 9 407.5C**, was
4.14Δ / 14.77% OTM at $0.36/$0.37 with **+12.38 / +4.92**; local RR rank and
IVR gates hid it. Conversely, **NBIS Aug 28** had a **+12.87-point** bid wing but
was **6.77 points cheaper than the deferred call**: a rich wing does not automatically
make the front expiry unusually expensive.

The exact-strike historical z-score question remains separate. Only the six original
MSTR selections have a completed prior-60-session matched-delta/DTE z-score study.
The new CSV explicitly marks the other histories unavailable. Do not substitute a
fixed-5Δ surface percentile or the cross-expiry spread for that z-score. The existing
MSTR study interpolates ATM; the current contract check uses the nearest-50Δ call,
so small differences in their reported ATM excesses are expected. IV comparisons use
the provider's bid-IV and mid-IV fields. [ORATS definitions](https://orats.com/docs/definitions).

### Daily broader call inventory

All observations below are **signal-day EOD**, usable from the following session.
These broader discovery selections have **not received a new HIRO/minute-quote P&L
replay**. They do not establish profitable entries or successful second-leg timing.
The original nine call confirmations and 142 put confirmations remain the strict
complete-window cohort above; the 73-row research inventory is separately labelled.

{{daily}}

### Which broader candidates already have HIRO for leg-timing research?

{{hiro}}

[Every selected call, ranks, quote, delta, % OTM and exclusion](call_search_expansion/expanded_call_candidate_tables.md),
[73-row contract and prospective second-leg CSV](call_search_expansion/call_candidates_2_to_10_delta.csv),
[band comparison](call_search_expansion/band_summary.csv),
[all 413 discovery rows](call_search_expansion/surface_candidates.csv),
[chain coverage](call_search_expansion/coverage.csv), and
[scanner fix](call_search_expansion/selector_fix.patch).
