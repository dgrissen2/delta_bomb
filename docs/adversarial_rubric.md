# Domain adversarial rubric — B06 IV research

Last updated: 2026-09-19. Scope: frozen 50-to-150-date B06 sector-IV expansion;
this is not a certification of the other research pipelines in this repository.
Discovery basis: sampling, parent generation, IV interpolation, availability,
scoring and reporting in `outputs/b06_iv_expansion_150d_2026-09-19/` and its
explicitly imported frozen sources.

## Data boundaries

| Boundary | Format | Validation | Failure mode |
|---|---|---|---|
| SPX native minute bars | Parquet OHLC | Complete unique 390-minute RTH grid, finite positive ordered OHLC, source hash | Misdated bars or invalid intraminute ordering contaminate signals/outcomes |
| Daily Vol Trigger | CSV plus preopen note | Positive same-date value, corroborating note | Opening-above status mistaken for entry-above or always-above status |
| Sector options | SDK IV and first-order Parquet | Matching keys/quotes, native timestamps, positive ordered quotes, age and tenor guards | Missing or failed inversion masquerades as an observed IV change |
| Frozen experiment | JSON containing Python functions | AST function-name selection, frozen hashes | Reproduction shares original implementation errors; trusted local source is executable |

## Type coercion vectors

| Coercion | Location | Risk | Test exists? |
|---|---|---|---|
| Numeric CSV/Parquet columns to floats | collection and surface preparation | NaN/Inf/bool accepted as market observations | Finite guards and targeted audit; strict bool rejection incomplete |
| Object array to float in replay assertion | resume_features.py | Conversion could hide a changed result | Real-only check; tolerance and missingness checks |
| Sector counts to yes/no/unknown | iv_rules.classify | Unknown silently treated as negative; fractional/NaN counts | Integer callers and count checks; malformed direct-call audit needed |
| Outcome labels to target counts | report/recalculate | Wrong label silently produces zero successes | Explicit enum check and independent outcome reconstruction |

## Trust assumptions

| Assumption | What breaks | Severity | Test exists? |
|---|---|---|---|
| Above VT at open means above VT at entry | Intended trading population | HIGH | Added all-date/all-entry VT audit |
| A day known afterward to stay above VT is a tradable entry filter | Causality | HIGH | Separate past-only and full-day descriptive gates |
| Identical frozen output implies correct methodology | Confidence in prior conclusion | HIGH | Independent signal/outcome/slope reconstruction |
| Positive IV change is independent new options information | Economic interpretation | HIGH | Not established by this price-path study |
| 30-DTE spot-ATM proxy is a full fixed-delta IV surface | Measurement interpretation | MEDIUM | Documentation/source inspection |
| All historical data is point-in-time available | Sampling generalization | HIGH | Preopen VT provenance, native timestamp checks; vendor corrections UNKNOWN |

## Cascade risks

| Cascade point | Blast radius | Isolation | Test exists? |
|---|---|---|---|
| One missing minute in 30-minute window | Entire sector/event unavailable | Explicit availability and fixed denominator 11 | Missing-minute and basket tests |
| Missing expiry bracket | Entire sector/day unavailable | Retain sampled day; classify unknown where appropriate | Manifest and full-grid reconciliation |
| Auth expiry | Remaining collection | Resume existing cache, bounded retry, errors retained | Transport tests and manifest reconciliation |
| Generic object assertion failure | Feature stage stops | Narrow compatibility adapter; no result changes | Replay assertions |

## Registry drift risks

| Registry | Code location | Drift detection | Last verified |
|---|---|---|---|
| Five fixed policies | PROTOCOL.md / iv_rules.py / evidence.json | Source hashes and original counts | 2026-09-19 |
| Timing, +5/-15, 60-minute score | b06_signals.py / screen.py | Independent native-price reconstruction | Audit in progress |
| Sample identity | selected/combined_days.csv | Unique 50+100 dates, frozen source hashes | 2026-09-19 |
| Storage inventory | central CHANGELOG/DATA_DICTIONARY | Counts, bytes and hashes | 2026-09-19 |

## Learned vectors

| Vector | Source milestone | Category | Recurrence |
|---|---|---|---|
| Cohort label narrower than implemented gate | 150-date VT audit | Intent/implementation mismatch | Present in original and added cohorts |
| Good replay can reproduce a wrong assumption | 150-date independent audit | Shared implementation dependence | Must independently check each stage |
| Opening minute cannot satisfy prior-quote guard | IV recovery/extension | Availability/time-of-day confounding | First eligible windows in both cohorts |
| New dates are not necessarily untouched research holdout dates | Expansion protocol | Inference | Label as extension, not certified holdout |
