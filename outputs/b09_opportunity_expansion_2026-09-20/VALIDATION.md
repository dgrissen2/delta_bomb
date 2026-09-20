# Validation record

- Eight boundary tests initially failed at import because the implementation
  did not exist, then passed after implementation. Final test run: eight passed.
- Tests cover synchronous historic votes, same-sector current negativity,
  unknown current measurements, old-qualifier retention, earliest witnesses,
  strictly prior 60-date RVOL baselines and missing history, conflicting duplicate
  outcomes, and chronological spacing displacement.
- Ruff passes for the new execution and related day-influence code.
- Frozen original source/code/protocol and prepared artifact hashes verified.
- 3,141 persistence classifications independently replayed with scalar logic.
- 415 original B07 classifications independently reconstructed from eleven-sector
  frozen source features, preserving the old quote/window rules.
- 3,141 RVOL features replayed directly from raw minute-volume lookups, independent
  of the rolling matrix implementation; prior dates and missingness reconciled.
- 5,093 native SPX entry/causal-VT/first-touch outcome replays matched.
- 105 event summaries, 120 volume summaries and 1,912 leave-one-date-out records
  independently recounted.
- 45 chronological added/displaced execution records and both equal-date/hour
  volume contrasts independently checked.
- All derived data saved centrally; exact hashes, table rows and sizes inventoried.
- Ten-date short-skew pilot samples only calendar fields with fixed seed and
  does not load event outcomes. No collection, new option measurements or skew
  accuracy test occurred.
- Local analytical verification only. No independent Quant, Charlie or Claude
  reviewer was launched or represented as approving the results.
