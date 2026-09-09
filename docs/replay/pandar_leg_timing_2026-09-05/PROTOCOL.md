# Frozen leg-timing research protocol — 2026-09-05

Written before calculating trade outcomes. Source: the user-linked 81 exact confirmations
(75 put rows, six MSTR call rows), reduced to 63 distinct ticker/expiry/strike-pair episodes
for the primary summary. Every original row remains in the audit. No substituted contracts.

The primary entry date is the session after the EOD qualification. Signal-day quotes are
descriptive only. The final observation cutoff is September 4, even if newer data exists.

## Persona decision

Canonical Charlie McElligott and Brent Kochuba personas were independently consulted.
Charlie proposed downside-momentum acquisition; Brent proposed calm put acquisition.
The panel arbitrator selected Brent's calm entry to preserve the put-inventory mechanism.
No momentum-entry optimization will be run. Charlie's exhaustion logic informs call entry.
These are simulations of the saved personas, not communications with the actual people.

## Inputs and entries

- HIRO: individual-stock All Trades; Total plus separate call/put increments. Regular
  session 09:30–16:00 America/New_York. Never add All, Next Expiry and Retail.
- Use cumulative RTH sums reconstructed from increments; rolling changes use 15 minutes.
  Evaluate every five minutes, 10:00 through 14:30. The first eligible quote is one minute
  after the observation, with no forward-filled missing quote.
- Put HIRO entry: positive 15-minute put-HIRO change and price at/above 15 minutes ago.
  Require live higher-put ask minus lower-put bid in (0, $0.10], with both executable.
- Call HIRO entry: negative 15-minute call-HIRO change, preceding 15-minute call change
  positive, price below the preceding 15-minute low, and far-call bid at least $0.20.
- Fixed-entry control: 10:01 next session, same live quote/cost gates. HIRO coverage is
  not required for this price-only control. It is not a paired proof of HIRO entry value
  unless both entries exist for the same episode.

## Completions and exits

For each fixed entry, compare identical contracts and entry cash across:

1. Complete both legs immediately.
2. Buy only the put / sell only the call, then close at the common exit.
3. Complete at a fixed 15:50 clock on entry day, +1, or +2 trading sessions.
4. Price-only financing: first subsequent minute where put lower-strike bid covers long
   entry ask plus $0.026/share, or call nearer ask is at most initial short bid less $0.026.
5. Price+HIRO financing: same price condition; puts additionally require negative rolling
   15-minute put HIRO and price below preceding 30-minute low. Calls require their
   exhaustion condition above. A gate uses only information at the previous minute.

Financing has identical day-0/+1/+2 deadlines. If it never fills, close the single leg
at the deadline; do not erase the failed attempt. A deadline beyond September 4 is
right-censored and excluded from complete-horizon comparisons; show its available mark.
Missing deadline quotes are unpriced. Fixed-clock completion is a control and may leave
a debit; financing requires enough cash to cover all four contract transactions.

Common exit for completed spreads and standalone controls: 15:50 on entry+3 sessions,
or expiry/September 4 if earlier. A shortened exit is explicitly flagged. Exit long at
bid, short at ask. One share-equivalent uses 100 contract multiplier. Each contract
transaction costs $0.65; full spread round trip is $2.60, single leg $1.30. No midpoint
fills or presumed zero-value settlements. Bid and ask must be finite, non-crossed;
action-side size >=1 and action-side price >0. Zero-bid holdings can be valued at zero
for conservative liquidation, but no zero-price sale is credited as an executable fill.
Also report an additional $0.01 adverse slippage per transaction sensitivity.

Report full original-row coverage, distinct-episode results, completed and failed attempts,
net cash at completion, executable liquidation P&L, interim adverse liquidation marks,
and completion benefit against simply closing the first leg. Positive construction cash
is not the same as executable exit profit. Call short-first phase has unlimited upside
risk; sampled losses do not bound it. No sizing or margin-return claim is made.

Quote snapshots show displayed liquidity, not actual fills, queue priority or tick-by-tick
execution. No point-in-time synthetic gamma terrain is available in this input set.
Results are exploratory within a short selected inventory, not an out-of-sample validation.

## Separately labelled source-rule sensitivity

After the primary run, the supplied master's pre-existing call-conversion formula
(`entry sale minus $0.10`) was also checked on the same two admitted call episodes.
It uses the same entries, causal flow gates, 0/+1/+2 deadlines and common exits. The
price credit target is $0.10 rather than the primary fee-covering $0.026. This is an
externally specified source-rule comparison, not a fitted parameter sweep. Its 12 rows
are in `source_dime_target_sensitivity.csv`; the primary 891 rows remain unchanged.
