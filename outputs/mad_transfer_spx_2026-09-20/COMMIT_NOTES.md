Execute reviewed MAD transfers and SPX disagreement study with complete learning notes

Implement the supplied independent review's accepted amendments: fixed B07/B05
S4/F4 transfers, six sign controls, existing B09 references and a single SPX
falling-MAD rule plus its OR with F4. Preserve the previous 105-rule and 48-cell
search history and the reviewer's premature B09-control calculations. This is
exploratory reuse of known dates, not an untouched holdout or new optimizer.

Keep the user's objective exactly +5 before -10 in 60 native minute bars. Retain
adverse-first, neither and ambiguous in N; ignore reversals after the target.
Use only causal above-VT entries: every prior RTH minute low and entry open
strictly above same-day VT. All IV sources end at T-1, with unchanged quote
guards, tenor interpolation and 60-prior-session MAD calibration. Scope stays
2025 through September 18, 2026, where all sector histories support comparison.
The completed SPX history extends into 2024 but does not extend sector coverage.

Main observations
- B09 F4 OR SPX is 198/318=62.3%, versus sector F4 115/188=61.2% and plain
  B09 1704/3141=54.3%. Active dates increase 95 to 121. The union adds 130 raw
  entries and 83 targets; it still excludes 1,506 of the parent's targets.
- Definite sector-no/SPX-yes additions are 72/109=66.1%; sector-unknown/SPX-yes
  coverage recovery is 11/21=52.4%. Keep those explanations separate. All 3,141
  B09 SPX endpoints are measured. Common-cohort OR is 187/297=63.0% against
  1,593/2,958=53.9%. Unknown sector votes are never filled as negative votes.
- OR spacing gives 107/175=61.1%, versus sector-only 76/121=62.8% and parent
  285/554=51.4%: more opportunities at a modest accuracy cost versus F4. First/day
  OR is 70/121=57.9%, below sector F4 61/95=64.2%. SPX alone falls from 61.5%
  raw to 48.1% first/day. The improvement is not execution-policy independent.
- The definite incremental group does not beat its negative benchmark in
  2026 H1: 8/14=57.1% versus 58.7%. Its best completed half is 2025 H2. Do not
  confuse the OR's favorable half-year totals with stable incremental value.
- Both sector and SPX yes is only 32/57=56.1%, versus sector yes/SPX no 83/131
  =63.4%. The observed opportunity is disagreement, not requiring both signals.
- B05 S4 is 91/149=61.1%; F4 70/112=62.5%, and 65/100=65.0% spaced. F4's
  within-date/hour difference is +14.0pp, descriptive interval +3.0 to +26.1.
  Outside blocks containing a qualifying B09 signal, F4 is 37/70=52.9%, against
  B05's 53.4% there. Its higher headline largely shares favorable B09 contexts;
  its N/dates/spaced N remain below B09 F4. No combined-parent portfolio tested.
- B07 S4 is 19/32=59.4%; F4 14/21=66.7% across just 20 dates. F4 half-year N
  is 4,8,7,2; parent-uplift interval -10.4 to +30.3pp. Outside qualifying B09
  blocks it is 6/12=50.0%. Explicitly underpowered/uninformative, not validated.
- Broad sign controls reproduce B09 1378/2544 and 1046/1933. Pooled all-entry
  changes across parents range -2.3 to +0.2pp, with some sensitivity to thinning.
  Their much broader selectivity cannot isolate MAD normalization's contribution.

Accepted review diagnostics
- Full outcome decomposition, retention, active dates and all four halves,
  keeping partial 2026 H2 and sparse cells visible.
- Whole-date uncertainty for all execution policies and relevant comparators;
  5,000 shared draws, seed 20260920. New Monte Carlo intervals for unchanged B09
  references differ slightly from old seed20260919, without data or rule changes.
- Selected-date parent and equal-date/equal-hour yes/no contrasts with overlap
  support. B09 OR's raw +8.0pp shrinks to +4.7 on selected dates and +2.9 within
  date/hour, whose interval crosses zero. SPX alone within-block is only +0.5pp.
- One fixed all-eleven-observed sensitivity and corresponding restricted parent.
  B09 OR112/180=62.2% versus parent50.8%; B05F4 44/69=63.8% versus53.5%.
  This preserves some directions while reducing N; it does not cure missingness.
- B09 block and exact-minute overlap, explicitly retrospective: a B09 event later
  in the same hour may label a block. These are never new causal entry filters.
- Every missing ETF-entry slot reconciled to source receipts: 2,742 slots /2,630
  unique instrument endpoints;1,417 absent permitted brackets,1,325 rejected
  current windows. XLRE contributes2,051 (1,220/831). No blind refetch, quote
  relaxation, new expiry, extrapolation or imputation. Remaining OR unknowns
  have100/162 targets and must not be described as failed signals.

Implementation and verification
- Freeze input/code/protocol hashes and memberships before attaching outcomes.
- Ten boundary tests first fail before implementation, then pass; Ruff passes.
- Separate scalar replay26,654memberships and2,592summaryrows; direct native
  replay5,093entry/VT/outcome checks;36inherited half/policy baselines; priorB09
  memberships/control counts;204within-block and324SPXcross rows all reconcile.
- Verify all registered sector/SPX score inputs, scale arithmetic, strictly prior
  date ledgers and actual source-minute causality; unchanged outcome hashes.
- Data, detailed ledgers, coverage, plot and provenance stored only in the new
  central_trade_data namespace; dictionary/changelog registered. No provider calls.
- Add findings, exhaustive fixed-rule tables, review-compliance matrix, extensive
  learning note and reproduction commands. Preserve unrelated working changes.

Independent strategy review was supplied before execution. This implementation
has local verification, not a new independent Claude code/results verdict. Keep
B09 OR and B05 F4 as fixed exploratory candidates with the stated policy/overlap
limits; no deployment, dashboard edit or additional threshold sweep.
