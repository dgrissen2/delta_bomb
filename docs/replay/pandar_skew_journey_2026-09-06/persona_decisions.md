# Charlie and Brent: delta, distance and the call-skew journey

Independent simulations of the canonical global personas; the actual people were not
contacted. Their proposals and Brent's protocol review preceded this experiment's results.

- [Charlie persona](/Users/dgrissen/.config/skillshare/personas/market/charlie-mcelligott.md)
- [Brent persona](/Users/dgrissen/.config/skillshare/personas/strategy/brent-kochuba.md)

## Charlie — decision summary

```json
{
  "coordinates": "Keep delta, percent OTM and expiry; normalize log strike/forward distance by ATM IV times square-root tenor. Delta is not strike-touch probability.",
  "journey": "Track consecutive elevated-skew age, accumulated intensity, known peak and retreat from it. Compare two falling wing observations against two rising observations. Persistent demand alone is not exhaustion.",
  "variance": "Compare annualized trailing 30/60-calendar-day realized variance with matched IV squared. Keep earnings effects distinct; historical versus forward variance is not guaranteed carry.",
  "exhaustion": "Test prior strength followed by slowing price returns and falling ATM IV; separately test accelerating IV decline. All are research hypotheses.",
  "counterexample": "Spot down and IV up can reflect downside protection demand. Lower call delta value can coexist with higher volatility value.",
  "evidence": "Freeze rules before outcomes. Use next-session entry references, 1–3-session outcomes, failed cases and clustered observations. Exact contract profit and conversion-versus-covering require executable quotes."
}
```

## Brent — decision summary

```json
{
  "coordinates": "Combine delta, percent OTM, tenor and distance in ATM expected-move units with event and gap context. Longer-horizon IV can conceal front-week risk.",
  "journey": "Use age, cumulative richness, persistence, current distance from the known peak, slope and change in slope at constant delta and tenor.",
  "controls": "A high percentile can still have a negative absolute wing. Compare journey stages at similar rank, absolute wing, ATM IV and event premium. Separate signal-to-entry drift from post-entry results.",
  "mechanics": "Temporal second differences, cross-strike skew curvature, option gamma, vanna and charm are different quantities. HIRO does not establish dealer inventory or gamma containment.",
  "evidence": "Proceed with the authorized daily-surface retrospective study. Preserve universe bias, missing outcomes, maximum-horizon nonoverlap and whole-panel month blocks. Do not label it exact-option P&L or a historical HIRO-flow backtest."
}
```

Both support broader strike discovery and testing journey effects rather than inventing
another narrow Pandar admission band. Their recommendations are complementary; no
material disagreement required an arbitrator. The study implements their daily-surface
hypotheses and joins them to the recent 73 exact-call selections. It does not establish
which exact delta/OTM combination optimizes realized trading returns.

## After the frozen results

Charlie and Brent separately reviewed the result packet. Both retain **rollover and
mature skew as modest volatility-normalization hypotheses**. Rollover was relatively
stable across chronological slices; the matched all-signal difference was about
+2.75 percentage points. Older skew's mean spot return was approximately zero, so
neither interprets this as a dependable directional short signal.

Both reject positive 30/60 variance premia as a useful standalone timing gate in this
sample. The exhaustion advantage faded in 2026 and the larger combined filter weakened
there with only 28 nonoverlapping observations. Neither recommends promoting it.

Their next-test recommendation is a frozen exact-option comparison of rollover versus
still-expanding skew, matched on starting richness, episode age, tenor, delta and
normalized distance. Use next-session executable quotes; retain unsuccessful paths,
interim exposure, preset completion deadlines, costs, and covering versus nearer-call
completion. HIRO should be a paired timing comparison on identical available coverage.
These recommendations do not claim that the surface results establish option profits.
