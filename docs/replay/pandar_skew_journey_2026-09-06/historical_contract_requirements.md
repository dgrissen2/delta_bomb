**We can obtain the contract histories needed to test this.** Use the existing
ThetaData account for historical option NBBO quotes and underlying prices; use
ORATS historical strikes for chain-wide Greeks, bid/ask IV and fitted surfaces where
needed. The follow-up below already fetched 18 missing contract histories and reused
two cached histories for the ten examples. That is enough for their specified price
replay, not for an optimal delta/% OTM test across the whole historical universe.

The full experiment needs these additional steps:

1. Freeze the eligible ticker-date population, the 30-day earnings gate, expiry rules,
   delta bands and % OTM/ATM-distance bins before fetching outcome quotes. Save every
   failed selection. Use historical listings, option deliverables and split adjustments
   so a renamed or adjusted contract is not silently replaced by another one.
2. Obtain each signal-date chain and the chain/underlying snapshot at the actual entry.
   Recheck delta, distance, spread and displayed size then: yesterday's 4Δ call need not
   still be 4Δ tomorrow. Keep the preselected far call and the rule-selected nearer call;
   no picking a better strike after seeing its price path.
3. For strike richness, build a strictly prior-only history of **comparable delta/DTE**
   and a separately reported **comparable forward-moneyness/DTE** coordinate. Interpolate
   only inside supported smiles, requiring at least 60 valid prior observations for the
   initial specification. Compare executable call-bid IV minus matched ATM IV with its
   own prior mean/dispersion, alongside a robust percentile. A newly listed weekly
   contract has no 60-day life of its own; the comparable surface history supplies the
   reference distribution. Sparse deep-wing quotes remain unavailable, not extrapolated.
4. Pull minute quotes for both legs through the fourth/fifth holding session or expiry,
   with quote timestamps, sizes, condition codes, underlying prices and corporate-action
   metadata. Use tick/quote-event history to assess staleness when necessary. Align the
   existing HIRO observations by ET session and use only information before each order.
5. Replay same-day, next-day and second-day purchases under fixed causal rules, with
   identical initial entries and closing deadlines. Compare the nearer-call conversion
   against covering the original short and against buying the spread immediately.
   Include fees, slippage, failed entries, uncompleted trades and short-phase adverse
   exposure. Preserve chronological evaluation periods and resample by date/episode.

ThetaData's [historical quote endpoint](https://docs.thetadata.us/operations/option_history_quote.html)
provides the contract quote history. ORATS offers [historical strikes and individual
contract histories](https://orats.com/docs/historical-data-api), with a separate
[minute-history product](https://orats.com/intraday-data-api). Confirm account entitlements
and a request budget before scaling: ORATS daily full-chain work costs roughly
ceil(tickers/10) × dates in requests; its minute-chain work is ticker × timestamp.
The small replay made no new ORATS requests and did not purchase a data subscription.
