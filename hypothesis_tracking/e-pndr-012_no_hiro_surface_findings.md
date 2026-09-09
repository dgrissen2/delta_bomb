# E-PNDR-012 findings: broad wing normalization without HIRO

Parent: [H-PNDR-003](h-pndr-003_skew_rollover_2026-09-07.md). [Index](RESEARCH_HYPOTHESIS_INDEX.md). This is a separately frozen follow-up experiment, not a replacement for the completed three-round June pilot.

**Verdict for this specification: not_supported.** The proposed slowing/rolling state does not improve the probability of wing compression with ATM flat or higher. This does not establish that every form of skew mean reversion is useless, or that the alternative state is a profitable call sale.

## Target / Outcome Definition

Two sessions after the next-session daily reference, compare P(wing compression AND ATM flat/up), slowing/rolling minus continued/accelerating. State uses two adjacent three-session wing slopes. W is the fixed five-call-delta, ten-calendar-day implied-volatility excess over ATM. This is not a fixed option contract.

## Sample Integrity and Method

The study uses no HIRO observations, gates or timing. Existing membership supplies 323 stock names. January 2023 onward supplies warmup; 671 evaluation dates span January 2024 through September 3, 2026. After the specified quality, actual-event 30-day earnings, positive-wing and prior-rank criteria, the analyzed population is 17,458 stock-dates, 304 stocks and 643 distinct signal dates, ending August 4. A common four-session-after-reference nonoverlap reservation retains 6,364 observations across 633 dates. Rich observations span 32 months and 7,939 stock-episode identifiers; these are not independent trials.

[Frozen protocol](pandar_no_hiro_surface_protocol_2026-09-08.md) · [Complete report](../outputs/pandar_no_hiro_2026-09-08/no_hiro_surface_results.md) · [Candidate ledger](../outputs/pandar_no_hiro_2026-09-08/candidate_reason_ledger.csv).

## Results

| Two-session outcome | Slowing/rolling | Continued/accelerating |
|---|---:|---:|
| Wing compresses | 59.18% | 58.81% |
| Wing compresses AND ATM flat/up | 26.14% | 28.08% |
| Total call IV falls | 59.46% | 56.33% |
| Wing compresses AND ATM flat/up AND call IV falls | 13.27% | 13.32% |

The primary difference is −1.94 percentage points, 95% whole-month bootstrap interval [−3.28, −0.56]. Controlling for starting wing/ATM, ticker and month gives −0.91 points, interval [−2.22, +0.40]. The common nonoverlap raw difference is −3.54 points, interval [−5.64, −1.36]. Neither the adjusted result nor the chronological/nonoverlap checks meets the frozen support condition.

These are joint rates over all valid observations. Among cases where ATM later stayed flat/up, the descriptive wing-compression rates are 58.15% versus 59.53%. This future regime is an outcome condition, never an entry rule.

## Interpretation and Decision Impact

Do not make this slowdown state a required gate for the next selector. Keep call-wing change, ATM change and total call-IV change separate. A falling wing does not necessarily cheapen the call in IV terms, and a falling call IV does not by itself prove a profitable short when the stock moves.

The [exact-chain experiment](pandar_no_hiro_exact_protocol_2026-09-08.md) tests a different proposed improvement: selection based on net scenario proceeds relative to a stated local upside sensitivity, with exact contracts retained at entry and exit. It carries its own limitations and cannot borrow a profitability verdict from this study.

## Threats To Validity

Current-universe membership is applied backward, and the historical panel was examined before this new specification. Earnings are a retrospectively known event purge. Fixed-coordinate surfaces roll through different strikes/expiries and are model measurements, not executable prices. There are 32 month blocks, not thousands of independent market regimes. Stock daily highs and closes are both already adjusted according to ORATS; the implementation corrected an initial double-adjustment of highs before final validation. Primary volatility and close-return results were unaffected. Sparse/invalid high observations censor the excursion separately.

## Persona Commentary

Charlie proposed the simple two-slope state and requested that ATM-held-up compression and total call-IV decline be separated. Brent's independent review found no material leakage in ranks, state, reference timing or overlap policy; he emphasized that the primary rate is joint rather than conditional, and that the failed specification should be described as no demonstrated improvement rather than proof that slowing causes inferior trades. Both personas are native Codex simulations of canonical global definitions, not actual statements from the named individuals.

## Reproduction

Run `/Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python scripts/pandar_no_hiro_surface.py` from the repository root. Ten causal tests and Ruff passed. [Validation](../outputs/pandar_no_hiro_2026-09-08/validation.json) records nine artifact checks, including input/ledger hashes, call-IV accounting and nonoverlap integrity. [Summary](../outputs/pandar_no_hiro_2026-09-08/summary.json) records the exact sample and estimated differences. No provider calls were used; shared acquisition usage remains 1,363/2,000.

## Plain explanation

We asked whether an already expensive call wing becomes easier to sell after its expansion slows. Across hundreds of dates, that particular waiting signal did not improve the outcome we specified. Some wings narrowed while overall volatility rose enough to keep the calls expensive. We should next test what the actual option pays relative to costs and exposure, instead of turning slowdown into another mandatory checkbox.
