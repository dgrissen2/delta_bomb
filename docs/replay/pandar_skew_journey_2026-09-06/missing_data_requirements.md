**To test persistence cleanly, backfill a session-by-session coverage ledger first.**
It must distinguish a failed download, a listed contract with no valid quote, a stock
that was not yet listed, a delisted/renamed stock and an observation that lies after the
cutoff. Those are different situations; filling them all with yesterday's number would
invent a continuous skew episode.

- For each historical HIRO-universe stock, obtain adjusted closes and the same
  fixed-tenor option surface on every actual exchange session, at least 252 sessions
  before the evaluation period, then through the final required exit. To know an
  episode's start, extend backward until an observed below-threshold session precedes
  it; if that cannot be found, retain unknown age. For recent-persistence tests, require
  complete 20-session windows as well as the complete RV windows.
- Retry only documented provider gaps, then check alternate ORATS/ThetaData coverage
  with reconciled timestamps, adjustments and IV conventions. Investigate the six
  missing-price names **FSR, GPS, MPW, NYCB, PARA and SQ** with dated security identifiers.
  Do not splice an assumed replacement ticker. Pre-IPO and post-delisting history
  cannot be manufactured by buying another feed.
- For a HIRO timing test, obtain the actual archived intraday series for the eligible
  dates and following sessions. Membership in today's HIRO ticker list does not provide
  historical flow. If the older feed cannot be recovered, the daily-surface test can
  continue, but that portion cannot establish HIRO's contribution.
- Freeze the new persistence hypotheses (high days/20, distance below the known
  20-session peak, and any permitted brief threshold interruption), then rebuild
  episodes and compare them with the existing consecutive-age rule on a later period.
  Apply the same earnings and coverage requirements to both groups, and retain the
  excluded/censored ledger. These additions have not yet been tested as entry gates.

The ten-contract follow-up has every expected nearer-call minute row for its admitted
entries through the available cutoff, but some rows contain invalid/non-executable
quotes and are skipped. A complete timestamp grid therefore does not prove continuous
liquidity, tick-level completeness or that an order would fill.
