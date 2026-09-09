# Plannotator follow-up protocol — September 7, 2026

Recorded before fetching the ten examples' additional option quotes or examining their
four/five-session results. The original daily-surface tables remain frozen.

- Keep the ten report examples and their preselected far/nearer call strikes and expiry.
- Use the next trading session's 10:01 ET quote. Require a non-crossed, finite far-call
  bid >= $0.20 with size >=1 and a valid nearer-call ask with size >=1. No replacement
  entry time or contract if that fails. This is a clock benchmark, not a HIRO entry test.
- After entry, buy the nearer call at the first valid minute ask <= original sale bid
  minus $0.10. This is the existing source-credit sensitivity, not a fitted threshold.
  Buying the nearer call completes a spread; it does not close the position.
- Interpret four/five days as four/five trading sessions including entry day (day 1).
  Also retain elapsed calendar days. Liquidate at 15:50 on day 4/day 5, or on expiry if
  earlier. If financing never occurs, cover the far call at that deadline. Do not assume
  an unquoted contract expires worthless. End data at September 4, matching prior replay.
- Use sell bid / buy ask, 100 multiplier and $0.65 per contract transaction. Report net
  cash at completion, final P&L, additional one-cent-per-action slippage, and short-only
  control at the same exit. A zero-bid long may be conservatively valued at zero but is
  not an executable closing sale; identify that result separately from fully closed.
- Missing entry, missing exit, incomplete observation grid and not-yet-observed deadlines
  remain separate statuses. A first observed financing quote after a missing observation
  cannot be claimed as the true first trigger. Record coverage and lower confidence.
- No option-order submission. At most 20 exact-contract ThetaData requests, one per
  contract with existing cached histories reused, no automatic retry. No new ORATS calls.

New user-directed admission rule: exclude an underlying with earnings on the evaluation
date or within the next 30 calendar days, inclusive. Check both signal and actual entry
date, using the schedule known then. Unknown/stale dates are not clearances. Audit the
central earnings files and the retained same-date estimates, but do not reclassify the
frozen surface tables as earnings-filtered or claim a point-in-time calendar from a
later revised event list. Quote outcomes remain counterfactual when admission is unknown.

After report updates and validation, the canonical global Richard Feynman-style persona
will review the updated report and evidence, then supply exactly four summary paragraphs.
