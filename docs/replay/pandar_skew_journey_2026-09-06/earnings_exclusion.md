**New admission rule requested in review: automatically exclude a stock with earnings
on the evaluation date or within the next 30 calendar days, inclusive.** Recheck at
both signal and actual entry. A missing, placeholder, stale or subsequently revised
date is not an earnings-free clearance; keep it out of the tradable sample until the
schedule known at that time is verified. This is the user's added filter, not a
Pandar-attributed rule.

The central sources are present, but the reviewed copies do not cover these August/
September signals with dated schedules:

- [Central earnings history](/Users/dgrissen/Dev/central_trade_data/orats/earnings/earnings_long.parquet):
  latest actual row June 25, 2026 (the adjacent manifest is older and says June 11).
- [Extended event history](/Users/dgrissen/Dev/central_trade_data/orats/earnings/pit_constituents_earnings_long.parquet):
  latest event July 29, 2026. Its name does not itself establish what future dates were
  known on each historical signal date.
- [Daily next-earnings snapshots](/Users/dgrissen/Dev/central_trade_data/orats/stable_rrs_earnings_2026-07-29-v1/normalized/earnings.parquet):
  latest snapshot July 29, 2026. The recent retained screen rows have `nextErn=0000-00-00`
  for all 73 selected calls. Their weeks-to-earnings estimates are retained as estimates,
  not substituted for dated schedules.

The [73-row earnings audit](review_earnings_73.csv) therefore marks every recent selection
**unknown / not admitted under this new policy**. Refresh the central calendar through
at least the last intended entry plus 30 calendar days, retain retrieval/version and
announcement-time metadata, and use archived as-known snapshots for retrospective
admission. A calendar refreshed today alone cannot prove what was known then.

The original surface percentages below are **unfiltered by this newly requested rule**
and remain frozen. The exact-quote examples are explicitly counterfactual while
earnings admission is unresolved. Do not present either as earnings-cleared performance.
Excluding upcoming earnings also does not remove MRNA's earlier reported jump from
trailing RV; that price move still needs a separate corporate-action/cross-source check.
