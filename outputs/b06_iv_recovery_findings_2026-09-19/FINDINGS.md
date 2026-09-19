# B06 sector IV: prior evidence, missing-data recovery, and quote-quality findings

Documented 19 September 2026. This records the completed side-conversation experiment and the earlier findings that led to it. The recovery run was executed before this document was written. Its exact protocol, Python source, stdout, structured results, and prior diagnostic source/output are preserved in [evidence.json](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/evidence.json).

## Decision and objective

**The objective is SPX reaching +5 points before −15 within the original 60 minutes. Accuracy comes first; the number of opportunities comes second. A reversal after +5 does not invalidate a success.**

The original acceleration filter selected 93 B06 entries with 67 successes, or **72.0%**, versus **239/374 = 63.9%** for plain B06. Recovering midpoint IV when bid IV was invalid expanded the selected sample to **78/112 = 69.6%**. Applying the primary conservative quote guards selected **49/69 = 71.0%**. The association survives these measurement-policy changes, but its advantage remains uncertain.

Most missing strike-bracket observations can be rebuilt from existing data: **4,904/5,311 = 92.3%**. Rebuilding a numerical midpoint measure does not prove the underlying quote is trustworthy. Conversely, a zero bid-IV field does not by itself make the midpoint IV unusable.

The strictest tested spread ceiling produced **22/29 = 75.9%**, but covers only 17 active dates and excludes 45 original successful signals. It was a predeclared sensitivity, not the primary candidate. We do not choose it because it has the highest observed percentage.

The primary 100% spread-ceiling guards improve a retrospective measure of extreme IV jumps, but do not demonstrate improved target accuracy over the original rule. They reject 25 original qualifying entries containing 18 successes; the original entries retained and excluded both hit approximately 72%.

No dashboard filter or production measurement policy was changed by this experiment. Documentation and evidence are being saved now; the completed calculation itself wrote no files.

## Earlier findings that motivated the recovery test

These are historical findings from the same repeatedly studied 50-day sample. They are not independent replications of one another. The original matched-price and acceleration studies were checked against their existing findings documents. Their statistics are preserved here without pretending they were rerun with recovered IV.

### 1. Does IV add information when sector prices look comparable?

Imagine two B06 signals with the same number of rising sectors and almost the same typical sector return. Matching those conditions asks whether the options measure distinguishes their next price movement after accounting for those two observable price features. The original IV-confirmed condition was the same six-of-eleven falling-and-accelerating ATM condition used here.

There were **73 one-to-one matched pairs, 146 entries**:

| Original IV state in matched sample | Signals | +5 first | −15 first | Neither | Hit rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Confirmed | 73 | 51 | 12 | 10 | 69.9% |
| Definite nonconfirmation | 73 | 42 | 12 | 19 | 57.5% |

The confirmed group had nine more targets and nine fewer unresolved outcomes. Both groups had twelve adverse outcomes. That supports a narrower hypothesis: **IV may distinguish initial upward progress from stalling.** Equal adverse counts do not negate the observed gain in the user's target score.

The matching used complete 30-sample price coverage for all eleven ETFs, exact rising-sector count, and a signed median sector-return difference no larger than ten basis points. Pair count was maximized first, then total distance minimized, without reuse. Actual absolute gaps were median **0.58 bps**, maximum **3.92 bps**. Of 374 original parents, 97 lacked complete price coverage; 277 remained, of which 41 had unknown IV state; 236 had known IV and complete prices (76 yes, 160 no); 146 were matched and 90 remained unmatched.

Only **three of 73 pairs shared a date**. Clock time, advance maturity, sector leadership, regime, and the entire price path were not equalized. The target-rate difference was **+12.3 percentage points**, with a descriptive whole-date 95% interval **−3.5 to +27.4**. The matched sample is an analytical comparison, not an executable matching rule for live entries.

**What remains promising:** the target association was not explained away by rising-sector count and signed median return alone. **What remains unproven:** independent option-market information, a causal mechanism, or a reliable future improvement. These 73 pairs have not been rematched or rescored under the recovery policies below.

Source: [matched-price findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_matched_price_2026-09-17/FINDINGS.md).

### 2. Does acceleration add anything beyond falling IV?

Falling IV and an accelerating decline are different. A sequence 20.0%, 19.9%, 19.6% falls faster toward the end; 20.0%, 19.7%, 19.6% still falls but slows. The actual study compares fitted slopes in two fifteen-sample halves, rather than those illustrative three-point sequences.

The original broad-falling group contained **217 entries and 144 targets: 66.4%**:

| Within original broad falling IV | Signals | +5 first | −15 first | Neither | Hit rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Acceleration yes | 93 | 67 | 13 | 13 | 72.0% |
| Definite acceleration no | 86 | 53 | 13 | 20 | 61.6% |
| Acceleration unknown | 38 | 24 | 10 | 4 | 63.2% |

Requiring acceleration kept **93/217 = 42.9% of entries** and **67/144 = 46.5% of targets**. It excluded 77 successful falling-IV opportunities: 53 in definite no and 24 in unknown. Against all plain B06, it retained 67 of 239 targets and excluded 172. Those are two different opportunity-cost denominators, not conflicting counts.

The earlier conditional yes-minus-no difference was **+10.4 pp**, with a whole-date interval approximately **−4.2 to +24.2 pp** using that study's seed. Qualifiers had a median of **eight sectors with falling IV**, versus **six** among definite nonqualifiers. The study tests an extra admission condition; it does not isolate acceleration from falling-IV breadth, slope magnitude, composition, prices, or regime.

Accuracy-first can justify taking fewer opportunities if the gain persists. Lost opportunities alone do not disqualify a filter. They must nevertheless be disclosed, and the observed accuracy gain is not yet established with high confidence.

Source: [acceleration findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_acceleration_increment_2026-09-17/FINDINGS.md).

### 3. What did the post-target study establish?

Among the 239 original targets, **237 had subsequent closes available**, and **87/237 = 36.7%** later closed below entry before the original hour ended. Two targets occurred in the last minute and had no later observations. Because early targets have longer to reverse, a separate common-duration check required fifteen subsequent minute closes: **49/222 = 22.1%** fell below entry, with seventeen targets excluded for insufficient remaining time.

IV confirmation did not demonstrate fewer later givebacks. Within broad falling IV, the fifteen-close comparison was **18/64 = 28.1%** for acceleration yes versus **7/45 = 15.6%** for definite acceleration no. Within the matched-price study it was **16/48 = 33.3%** versus **12/38 = 31.6%**. These have different conditioned denominators and must not be mixed.

**This study did not improve B06's first-movement score. It examined events after the objective had already been achieved.** Under the user's clarified objective, these are historical path descriptions only. They do not demote original winners, enter the recovery decision, or count against an otherwise useful +5-first filter. There is no new persistence or option-P&L requirement in this report.

Source: [post-target findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_post_target_2026-09-17/FINDINGS.md). The user's supplied earlier explanation and objective correction are preserved verbatim as context in evidence.json. Earlier statements about then-current dashboard deployment status are historical, not a description of the current main-thread dashboard.

### How those findings led to this test

The first two studies suggested a promising first-movement association, but some sector windows were unknown because the IV pipeline rejected available raw observations. We traced the difference between a genuinely missing quote, an uncomputable bid-side IV, and an implausible midpoint caused by a distorted bid/ask quote.

The resulting question is specific: **can existing midpoint observations recover missing classifications without turning quote artifacts into apparent falling IV or acceleration?** The answer needs both measurement diagnostics and the unchanged +5-first score. Neither smooth-looking IV nor an improved backtest percentage by itself validates a quote.

## Data, cohort, and unchanged score

- Same fifty randomly sampled additional 2026 sessions from the original eligible above-VT population; original ten exploration dates excluded. No dates were added or replaced in this recovery study.
- Dates run from **2 January to 10 August 2026**. All fifty are retained in date resampling, including **13 July**, with no B06 entries.
- **374 B06 parents on 49 active dates**. Overlapping signals are retained and are not independent observations.
- Above VT is the original **09:30 SPX open above same-date Vol Trigger** cohort rule. This recovery experiment adds no intraday VT gate.
- B06 is the completed five-minute close above the preceding six-bar high, with one attempt per distinct numerical boundary per day and decisions before 14:30.
- Entry is the next available native minute open at B06 availability. The inherited path score is **+5 before −15 within sixty native minute intervals**. Neither barrier reached is a non-success in the hit-rate denominator. Ambiguous same-minute ordering remains ambiguous under the original scorer; this sample has **zero ambiguous cases**.
- Baseline is unchanged: **239 target-first, 51 adverse-first, 84 neither**.
- Eleven ETFs: **XLC, XLY, XLP, XLE, XLF, XLV, XLI, XLB, XLRE, XLK, XLU**.
- Native minute option IV and first-order Greeks were originally collected using **ThetaData Python SDK 1.0.9**, interval **1m**, both option rights, strike_range 30, 09:30–14:29 ET, SOFR, version latest.
- Existing cache contains **1,966 raw minute-history files**, representing 983 selected date/symbol/expiry pairs and two endpoints each. No new data requests were made for recovery.
- **537/550 sector-days** have allowed expiry brackets. Thirteen missing brackets are all XLRE. Expiry availability cannot be repaired by dropping a bid-IV check.

Raw cache: /Users/dgrissen/Dev/central_trade_data/thetadata/sector_surface_b06_50d_2026-09-13-v1/

Source cohort, measurements, and frozen outcomes: /Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/

The thirteen XLRE expiry-gap dates are: 2026-01-09, 2026-01-13, 2026-01-15, 2026-01-16, 2026-04-14, 2026-05-11, 2026-05-13, 2026-05-14, 2026-05-18, 2026-06-15, 2026-06-16, 2026-07-13, 2026-07-14. These account for **3,900 sector-minutes** and remain unavailable under every version.

## Which IV is used, and exactly how it is constructed

The signal uses ThetaData **implied_vol**, the midpoint-IV field. It does not compute direction from bid_implied_vol. Originally, however, valid bid IV was a prerequisite for accepting the midpoint observation. This difference is the source of much of the missingness.

The selected coordinate is **30-calendar-day, spot-relative ATM**, where strike/spot equals one. It is **not a fixed 50-delta series**. Separate ±25-delta wing descriptors in earlier work do not define this acceleration filter.

For each selected expiry and each option right:

1. Set x = log(strike / spot). Choose the nearest valid observed strike on each side of x = 0. Do not extrapolate.
2. If w = x_high / (x_high − x_low), interpolate variance: v_ATM = w × IV_low² + (1 − w) × IV_high². An exact ATM strike supplies the value directly.
3. Use the nearest expiry below and above 30 calendar days within the allowed 8–65 DTE range, or one expiry if it is exactly 30 DTE.
4. With tenor weight q = (d_high − 30) / (d_high − d_low), interpolate total variance and divide by 30: IV_30² = [q × d_low × v_low + (1 − q) × d_high × v_high] / 30.
5. Combine calls and puts as IV_ATM = sqrt((IV_call,30² + IV_put,30²) / 2). Multiply decimal IV by 100 for IV percentage-point units.

Interpolation across strikes and expiry is distinct from filling time gaps. **No missing minute is interpolated.** Recovering a formerly invalid nearer strike can also change a previously valid ATM value. The recovery version therefore rebuilds all minutes consistently instead of splicing only the missing rows.

Provider-model conventions are inherited. No new dividend model, alternate pricing model, or independent vendor reconciliation was introduced. The experiment assesses the existing reported midpoint measure and its predictive association.

## Exact slope, acceleration, and missingness logic

At B06 time T, use samples **T−35 through T−6**, inclusive. Exclude breakout samples T−5 through T−1. Each sector needs all thirty valid samples under the selected data policy. Both halves use the same complete sector support.

For each fifteen-sample half, i = 0…14:

```text
b_half = sum((i - 7) * IV[i]) / 280
a = (b_second - b_first) / 15

falling = b_second < -1e-12
falling_and_accelerating = b_second < -1e-12 and a < -1e-12
```

Slope units are IV percentage points per minute; acceleration units are IV percentage points per minute squared. Fifteen minutes separates the half-window centers. A transition from rising IV to falling IV qualifies; the first half need not already be falling. This is a finite difference of fitted slopes, not a fitted full-surface time derivative.

Let k be known qualifying sectors and m missing sectors:

```text
yes     if k >= 6
no      if k + m < 6
unknown otherwise
```

Use fixed denominator eleven. Do not substitute a percentage of available sectors, convert unknown to no, or require all eleven sectors to be available. The same six sectors must individually meet both conditions for acceleration yes.

## Four rules fixed before this run's outcome comparison

Previously studied outcomes were already known. Fixing this protocol before the new join limits tuning within this run; it does not make the data unseen or turn this into out-of-sample validation.

### Original

Require positive finite strike, underlying, dollar bid, midpoint, dollar ask, bid IV, midpoint IV, and ask IV; ordered dollar quotes and ordered bid/mid/ask IV; matching IV/Greek endpoint observations; reported underlying age from zero through sixty seconds; allowed option rights and DTE; valid strike/expiry brackets and common underlying observation.

### Midpoint recovery

Drop only bid-IV positivity/finiteness and bid-IV ≤ midpoint-IV checks. Preserve the original positive finite dollar bid, midpoint and ask; dollar ordering; positive finite midpoint/ask IV with midpoint IV ≤ ask IV; endpoint matching; underlying age; DTE; and interpolation rules.

**A zero dollar bid remains rejected. A zero bid-IV value can be accepted.** No missing bid-IV uncertainty bound is invented. This is numerical recoverability, not independent certification that the midpoint is a good executable or fair price.

### Guarded recovery with 100% spread ceiling — primary candidate

Start with the strikes and expirations chosen by midpoint recovery. Reject the entire ATM minute if any required selected quote fails:

```text
width = (ask - bid) / provider_midpoint
width <= 1.00

previous_same_contract_quote exists exactly 60 seconds earlier
previous_bid and previous_ask are finite
previous_bid > 0 and previous_ask >= previous_bid

reject if bid < 0.50 * previous_bid AND ask >= 0.90 * previous_ask
reject if ask > 2.00 * previous_ask AND bid <= 1.10 * previous_bid
```

Equality at the spread ceiling passes. Exact halving/doubling does not trigger the strict shock inequality. The relative-spread denominator is the reported option midpoint, not the underlying price. A 100% ceiling is still a permissive dollar spread.

Previous-quote support verifies existence and positive ordered quotes, not that the previous quote itself had previously passed every guard. Thus this is a bounded one-step distortion test, not a guarantee that persistent bad quotes are detected.

Do not skip a rejected selected strike and search for a farther strike to evade these guards. Do not fill a rejected minute. A single failed constituent can invalidate the ATM minute, and a single invalid minute can invalidate a sector's full thirty-sample window.

### Guarded recovery with 50% spread ceiling — sensitivity only

Identical rules except width ≤ 0.50. No threshold sweep, optimized cutoff, or promotion based on the highest observed hit rate.

The original protocol hash is **1faf009c2b8624dd87f8ebd28d9be8cfe6902a786411348e170c6295959e3cee**. The unchanged protocol text/object is preserved in evidence.json.

## Why missing bid IV sometimes looks normal and sometimes does not

An initial diagnostic inspected all **75 sector-days with strike-bracket gaps across 47 dates**. Broad recovery rebuilt 4,904 missing ATM minutes using, among other constituent observations, **6,263 previously excluded contract-minute quotes**. Every one of these 6,263 had bid IV exactly zero; none represented acceptance of a zero dollar bid.

Of 6,174 with adjacent same-contract IV observations on both sides, median deviation from the neighboring average was **0.145 IV points**, the 95th percentile **0.88**, and **247** exceeded one point. Thus about **96.0%** were within one IV point of the neighboring average. Nevertheless **17** exceeded five points.

The median relative bid/ask spread was **94.7% of midpoint**, and **2,889** exceeded 100%. Of 6,192 with a preceding quote, **5,970 = 96.4%** had unchanged bid/ask prices; **4,544** had a changing IV despite those unchanged prices. Smoothness or an updated timestamp alone does not establish new options-price information.

Already accepted companion quotes also included wide spreads and jumps. Quality issues are not unique to the recovered subset. This is why the guards apply to every selected quote, rather than giving existing observations an automatic exemption.

The before/after diagnostic is retrospective only. Neither the next quote nor a subsequent SPX outcome enters admission. A large neighboring deviation may accompany a real repricing; a small deviation may reflect persistently poor quotes. It is a diagnostic, not ground-truth accuracy.

### Concrete quote examples

**XLRE, 6 January 2026, January 16 $41 put.** At 09:46 ET, bid/ask were $0.60/$1.15, midpoint IV 19.53%, bid IV 5.85%. At 09:47, the dollar quote was unchanged, spot moved from $40.37 to $40.32, midpoint IV was 18.06%, and bid IV became zero. The old rule discarded that node. Recovered combined 30-day ATM IV was about 15.3944% at 09:46, 15.3621% at 09:47, and 15.6297% at 09:48. The absence of a dramatic ATM spike makes it a recovery candidate; it does not prove the quote is fair.

**XLF, 28 January 2026, February 27 $52.50 call:**

| Time, ET | Bid | Ask | Provider midpoint IV |
| --- | ---: | ---: | ---: |
| 14:00 | $1.11 | $1.51 | 17.52% |
| 14:01 | $0.01 | $1.63 | 8.66% |
| 14:02 | $1.17 | $1.41 | 16.99% |

The 14:01 bid collapse creates an implausibly sharp midpoint-IV dip while the ask rises. The user reported Thinkorswim IV of **15.22%** at that time. That is a user-reported cross-check, not an independently retrieved value in this experiment. The ThetaData cache was confirmed at 8.66%; no vendor reconciliation resolved the difference. These quote inputs fail the frozen guards.

The IV endpoint's iv_error was 16.8946 while the first-order endpoint's same-row iv_error was zero. We did not treat that field as a proven midpoint-specific solver-quality flag or impose a new threshold based on it.

**XLRE, 12 February 2026, February 20 $44 put.** Bid/ask were $0.65/$0.80 at 11:11, with midpoint IV 10.25%. At 11:12, the bid stayed $0.65, the ask jumped to $2.80, and midpoint IV became 52.42%. This illustrates the opposite one-sided distortion; the guard rejects those inputs as well.

An ORATS historical one-minute comparison did not yield a successful independent validation in the preceding investigation. No ORATS value is used to approve or replace ThetaData IV here.

## Recovery and coverage results

There are **165,000 potential sector-minute observations**: 50 dates × 11 sectors × 300 minutes. Original coverage was 155,233 valid minutes; the gaps were 5,311 strike-bracket gaps, 3,900 expiry-bracket gaps, and 556 other invalid minutes. Broad recovery fixes only the strike-bracket portion addressed by these rules; 407 such gaps remain.

| Rule | Valid sector-minutes | Recovered | Previously valid lost | Previously valid changed | Complete sector/event windows | All-11-complete entries |
| --- | --- | --- | --- | --- | --- | --- |
| Original | 155,233 | 0 | 0 | 0 | 3,778 | 114 |
| Midpoint recovery | 160,137 | 4,904 | 0 | 1,024 | 3,970 | 262 |
| Guards, 100% spread ceiling | 140,162 | 810 | 15,881 | 101 | 3,423 | 76 |
| Guards, 50% spread ceiling | 108,929 | 23 | 46,327 | 0 | 2,615 | 3 |

“Changed” counts an originally valid ATM value whose recalculated value differs by more than 1e−8 IV points. It is not an additional missing or recovered observation. Recovered nearer strikes change **1,024** previously accepted midpoint values; there is no silent mix of old and new selection policies.

There are **4,114 possible sector/event windows** (374 × 11). Original complete windows numbered 3,778. Midpoint recovery adds 192 and loses none, reaching 3,970. The primary guards add 36 but lose 391, reaching 3,423. The strict sensitivity adds five but loses 1,168, reaching 2,615.

The guard's coverage cost compounds across up to eight option constituents per ATM minute and thirty required minutes per sector window. A seemingly moderate quote restriction can therefore remove a large number of complete windows.

| ETF | Originally valid minutes | Midpoint recovered | 100% recovered | 100% previously valid lost | 50% recovered | 50% previously valid lost |
| --- | --- | --- | --- | --- | --- | --- |
| XLC | 14,545 | 404 | 0 | 4,851 | 0 | 6,208 |
| XLY | 14,950 | 0 | 0 | 2,662 | 0 | 7,567 |
| XLP | 14,776 | 174 | 0 | 827 | 0 | 3,352 |
| XLE | 14,949 | 1 | 0 | 485 | 0 | 1,186 |
| XLF | 14,731 | 219 | 0 | 270 | 0 | 794 |
| XLV | 14,950 | 0 | 0 | 454 | 0 | 3,484 |
| XLI | 14,950 | 0 | 0 | 88 | 0 | 4,330 |
| XLB | 14,894 | 56 | 0 | 871 | 0 | 5,863 |
| XLRE | 7,465 | 3,289 | 748 | 3,302 | 22 | 7,158 |
| XLK | 14,950 | 0 | 0 | 65 | 0 | 1,482 |
| XLU | 14,073 | 761 | 62 | 2,006 | 1 | 4,903 |

Zero recovered observations for an ETF under the guards does not imply that its raw data never existed. It means the complete ATM observation did not survive the selected constituent guards. XLRE and XLU account for all 810 recovered minutes under the primary guards. Sector composition and missingness therefore change with the policy.

## Target outcomes and opportunity cost

| Rule / selection | Signals | Active dates | +5 first | −15 first | Neither | +5-first rate |
| --- | --- | --- | --- | --- | --- | --- |
| Plain B06 | 374 | 49 | 239 | 51 | 84 | 63.9% |
| Original | 93 | 35 | 67 | 13 | 13 | 72.0% |
| Midpoint recovery | 112 | 39 | 78 | 15 | 19 | 69.6% |
| Guards, 100% spread ceiling | 69 | 32 | 49 | 9 | 11 | 71.0% |
| Guards, 50% spread ceiling | 29 | 17 | 22 | 4 | 3 | 75.9% |

These are overlapping selections of the same 374 parents, not four independent experiments. The primary guards were not chosen after seeing these percentages.

| Rule | Original qualifiers retained / targets | Original qualifiers lost / targets | New qualifiers / targets | New qualifiers' hit rate |
| --- | --- | --- | --- | --- |
| Midpoint recovery | 93 / 67 | 0 / 0 | 19 / 11 | 57.9% |
| Guards, 100% spread ceiling | 68 / 49 | 25 / 18 | 1 / 0 | 0.0% |
| Guards, 50% spread ceiling | 29 / 22 | 64 / 45 | 0 / 0 | — |

All 19 newly selected midpoint-recovery entries came from the original **unknown** group, not definite no. Their **11/19 = 57.9%** hit rate lowers the combined result from 72.0% to 69.6% while adding eleven successes. That describes this sample; it does not justify rejecting recovered observations based on their later outcomes.

For the primary guards, original qualifiers retained were **49/68 = 72.1%** winners, while excluded original qualifiers were **18/25 = 72.0%** winners. The one newly selected entry reached neither barrier. The guards improve some measurement diagnostics, but their exclusions did not improve observed target accuracy.

The 50% sensitivity retains 29 original qualifiers and adds none. It excludes 64 original qualifiers, including 45 successes; those excluded entries themselves hit **45/64 = 70.3%**. Accuracy-first makes its 75.9% worth reporting, but the limited sample and uncertainty do not establish it as the superior policy.

### Broad falling IV under each data rule

| Rule | State | Signals | Active dates | +5 first | −15 first | Neither | +5-first rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original | yes | 217 | 48 | 144 | 36 | 37 | 66.4% |
| Original | no | 95 | 36 | 59 | 13 | 23 | 62.1% |
| Original | unknown | 62 | 25 | 36 | 2 | 24 | 58.1% |
| Midpoint recovery | yes | 237 | 49 | 153 | 37 | 47 | 64.6% |
| Midpoint recovery | no | 108 | 38 | 66 | 13 | 29 | 61.1% |
| Midpoint recovery | unknown | 29 | 14 | 20 | 1 | 8 | 69.0% |
| Guards, 100% spread ceiling | yes | 166 | 45 | 110 | 25 | 31 | 66.3% |
| Guards, 100% spread ceiling | no | 74 | 32 | 41 | 12 | 21 | 55.4% |
| Guards, 100% spread ceiling | unknown | 134 | 42 | 88 | 14 | 32 | 65.7% |
| Guards, 50% spread ceiling | yes | 88 | 31 | 56 | 14 | 18 | 63.6% |
| Guards, 50% spread ceiling | no | 39 | 22 | 17 | 7 | 15 | 43.6% |
| Guards, 50% spread ceiling | unknown | 247 | 49 | 166 | 30 | 51 | 67.2% |

Broad falling alone moves from **144/217 = 66.4%** to **153/237 = 64.6%** under midpoint recovery, close to plain B06's 63.9%. Acceleration's apparent advantage therefore persists more clearly than a simple broad-falling-only advantage in the recovery comparison.

### Acceleration across all B06 entries

| Rule | State | Signals | Active dates | +5 first | −15 first | Neither | +5-first rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original | yes | 93 | 35 | 67 | 13 | 13 | 72.0% |
| Original | no | 216 | 47 | 132 | 27 | 57 | 61.1% |
| Original | unknown | 65 | 33 | 40 | 11 | 14 | 61.5% |
| Midpoint recovery | yes | 112 | 39 | 78 | 15 | 19 | 69.6% |
| Midpoint recovery | no | 238 | 47 | 146 | 31 | 61 | 61.3% |
| Midpoint recovery | unknown | 24 | 16 | 15 | 5 | 4 | 62.5% |
| Guards, 100% spread ceiling | yes | 69 | 32 | 49 | 9 | 11 | 71.0% |
| Guards, 100% spread ceiling | no | 169 | 44 | 100 | 24 | 45 | 59.2% |
| Guards, 100% spread ceiling | unknown | 136 | 43 | 90 | 18 | 28 | 66.2% |
| Guards, 50% spread ceiling | yes | 29 | 17 | 22 | 4 | 3 | 75.9% |
| Guards, 50% spread ceiling | no | 103 | 32 | 52 | 16 | 35 | 50.5% |
| Guards, 50% spread ceiling | unknown | 242 | 49 | 165 | 31 | 46 | 68.2% |

Global unknown acceleration falls **65 → 24** with midpoint recovery, but rises to **136** with the primary guards and **242** with the strict sensitivity. This is why a higher selected hit rate must be shown alongside coverage. Unknowns stay in the full B06 baseline and are not relabeled as failed signals.

### Acceleration conditional on broad falling IV

| Rule | State | Signals | Active dates | +5 first | −15 first | Neither | +5-first rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Original | yes | 93 | 35 | 67 | 13 | 13 | 72.0% |
| Original | no | 86 | 39 | 53 | 13 | 20 | 61.6% |
| Original | unknown | 38 | 29 | 24 | 10 | 4 | 63.2% |
| Midpoint recovery | yes | 112 | 39 | 78 | 15 | 19 | 69.6% |
| Midpoint recovery | no | 112 | 42 | 67 | 18 | 27 | 59.8% |
| Midpoint recovery | unknown | 13 | 10 | 8 | 4 | 1 | 61.5% |
| Guards, 100% spread ceiling | yes | 69 | 32 | 49 | 9 | 11 | 71.0% |
| Guards, 100% spread ceiling | no | 49 | 26 | 28 | 9 | 12 | 57.1% |
| Guards, 100% spread ceiling | unknown | 48 | 28 | 33 | 7 | 8 | 68.8% |
| Guards, 50% spread ceiling | yes | 29 | 17 | 22 | 4 | 3 | 75.9% |
| Guards, 50% spread ceiling | no | 17 | 10 | 7 | 4 | 6 | 41.2% |
| Guards, 50% spread ceiling | unknown | 42 | 25 | 27 | 6 | 9 | 64.3% |

In the expanded midpoint version, acceleration yes is **78/112 = 69.6%**, compared with **67/112 = 59.8%** for definite no within broad falling. That is an observed **+9.82 pp** difference, interval **−3.97 to +23.37 pp**. It preserves the earlier qualitative hint without isolating acceleration from all other context.

## Quote-quality diagnostics after applying the rules

For a selected same-contract observation with both neighboring minutes available, the retrospective deviation is:

```text
abs(IV_now - (IV_previous + IV_next) / 2)
```

All values below are in IV percentage points. These pooled contract-minute observations are measurement diagnostics, not independent trading trials. Counts differ from the earlier gap-only audit because this run evaluates the complete selected series, including previously valid minutes.

| Rule | Contract-minute observations | Have both neighbors | Deviation >1 IV point | Deviation >5 IV points | Median / 95th-percentile deviation, IV points |
| --- | --- | --- | --- | --- | --- |
| Original | 1,125,861 | 1,118,442 | 4,794 | 44 | 0.075 / 0.370 |
| Midpoint recovery | 1,163,470 | 1,155,717 | 5,514 | 80 | 0.075 / 0.370 |
| Guards, 100% spread ceiling | 1,014,862 | 1,011,137 | 3,633 | 13 | 0.075 / 0.360 |
| Guards, 50% spread ceiling | 781,088 | 777,838 | 1,788 | 5 | 0.070 / 0.335 |

The count above five IV points falls from 80 among 1,155,717 neighbor-supported midpoint observations to 13 among 1,011,137 primary-guard observations. The approximate rates are **6.9 versus 1.3 per 100,000**. This is consistent with the guards reducing extreme local jumps, but it is not a known-clean versus known-bad classification test. Much of the data is excluded at the same time, and no component ablation separated the spread rule from the shock/prior-quote rules.

Unchanged option prices remain common under every policy. An additional diagnostic counted qualifying B06 entries having at least six qualifying sectors with some selected bid/ask change in **each** fifteen-sample half:

| Rule | Acceleration-selected entries | Also meet this quote-change diagnostic |
| --- | ---: | ---: |
| Original | 93 | 57 |
| Midpoint recovery | 112 | 63 |
| Guards, 100% ceiling | 69 | 43 |
| Guards, 50% ceiling | 29 | 20 |

This was **not an added trading filter** and no target-rate result was used to select it. It does not prove that a measured IV change was new option-market information or remove the underlying-price effect. The diagnostic allows any constituent quote to change within each half; it does not certify every constituent is freshly repriced.

## January 6 at 10:15 ET: the toy example resolved under each policy

Reference minutes are **09:40–10:09**, split into **09:40–09:54** and **09:55–10:09**. The breakout bar covers **10:10–10:14**, excluded from the reference.

Original support was XLC 9/30 samples, XLRE 28/30, and XLU 0/30; the other eight ETFs had all thirty. The missing minutes were XLC 09:43–09:45, 09:49, and 09:53–10:09; XLRE 09:47–09:48; XLU the entire thirty-minute window. These were strike/validity gaps, not an expiry gap on this date.

| Rule | Available sectors | Falling sectors | Falling + accelerating sectors | Acceleration decision |
| --- | --- | --- | --- | --- |
| Original | 8 | 7 | 4 | unknown |
| Midpoint recovery | 11 | 10 | 6 | yes |
| Guards, 100% spread ceiling | 5 | 4 | 2 | unknown |
| Guards, 50% spread ceiling | 3 | 2 | 0 | unknown |

Broad midpoint recovery makes all eleven sectors available and changes the acceleration decision from unknown to yes. The original score for this particular entry is **adverse first**, unchanged. Its outcome neither invalidates recovery as a measurement policy nor licenses tuning the policy to exclude this example.

The conservative guards leave too little support to classify the basket. A numerically reconstructed observation and an observation meeting the selected confidence policy are different things.

## Uncertainty and robustness

Use **10,000 shared bootstrap draws of whole dates**, seed **20260919**, across all fifty sampled dates. Each draw resamples dates with replacement, then computes each group's target rate from its own aggregate targets and entries. Identical date draws preserve cross-group dependence. No IID-entry or independent-pair assumption is made.

Intervals are descriptive 2.5th/97.5th percentile intervals, unadjusted for prior research, multiple comparisons, regime dependence, or selection of the general hypothesis. Every reported contrast has 10,000 defined draws. Delete-one-date ranges recompute the difference after removing each date; positive ranges do not replace the wider uncertainty interval.

| Comparison | Difference, pp | 95% whole-date interval, pp | Delete-one-date range, pp |
| --- | --- | --- | --- |
| original accelerating yes minus all | 8.14 | -0.87 to 17.54 | 6.70 to 10.12 |
| original accelerating yes minus original falling yes | 5.68 | -2.30 to 14.15 | 4.28 to 7.18 |
| original within falling acceleration yes minus original within falling acceleration no | 10.42 | -4.07 to 24.41 | 8.14 to 12.53 |
| midpoint accelerating yes minus all | 5.74 | -2.76 to 14.25 | 4.64 to 7.39 |
| midpoint accelerating yes minus midpoint falling yes | 5.09 | -2.39 to 12.98 | 4.00 to 6.57 |
| midpoint within falling acceleration yes minus midpoint within falling acceleration no | 9.82 | -3.97 to 23.37 | 8.14 to 12.59 |
| midpoint accelerating yes minus original accelerating yes | -2.40 | -9.21 to 2.65 | -2.93 to 0.18 |
| guarded 100 accelerating yes minus all | 7.11 | -3.23 to 18.09 | 5.14 to 9.18 |
| guarded 100 accelerating yes minus guarded 100 falling yes | 4.75 | -3.98 to 13.83 | 3.19 to 6.06 |
| guarded 100 within falling acceleration yes minus guarded 100 within falling acceleration no | 13.87 | -4.33 to 32.13 | 9.70 to 17.57 |
| guarded 100 accelerating yes minus original accelerating yes | -1.03 | -7.32 to 5.11 | -2.75 to 0.02 |
| guarded 50 accelerating yes minus all | 11.96 | -3.09 to 27.70 | 9.69 to 15.00 |
| guarded 50 accelerating yes minus guarded 50 falling yes | 12.23 | 0.25 to 26.10 | 9.66 to 14.53 |
| guarded 50 within falling acceleration yes minus guarded 50 within falling acceleration no | 34.69 | 7.84 to 65.00 | 29.20 to 43.30 |
| guarded 50 accelerating yes minus original accelerating yes | 3.82 | -9.20 to 17.93 | 0.84 to 6.44 |

The primary guarded filter's advantage over plain B06 is **+7.11 pp**, interval **−3.23 to +18.09 pp**. Midpoint recovery's advantage is **+5.74 pp**, interval **−2.76 to +14.25 pp**. Neither establishes a positive population advantage at this level of uncertainty.

The strict sensitivity has some conditional intervals excluding zero: versus its own broad-falling group, approximately +0.25 to +26.10 pp; versus its small definite-no subgroup, +7.84 to +65.00 pp. These should not be hidden, but they do not make it the proven best rule. Its comparison against plain B06 and against the original acceleration rule still spans zero, and these are numerous exploratory contrasts on selected small cohorts.

The recovered minus original acceleration-rate difference is −2.40 pp, interval −9.21 to +2.65. It is accurate to say the observed rate falls after recovery, not that the true rate is proven worse.

Earlier interval endpoints differ slightly because the source studies used their own fixed resampling seeds. The recovery run's seed and full intervals are preserved here; the matched-price study's original intervals have not been recomputed.

## Practical interpretation: usable, recoverable, and unresolved

**Unusable under every tested version:** nonpositive dollar bids, invalid ordered quotes, invalid required midpoint/ask IV, endpoint/underlying inconsistencies, missing required expiry brackets, and an incomplete thirty-minute window after the chosen rules. These remain unavailable; no fabricated minute or missing uncertainty bound is introduced.

**Recoverable for expanded research:** positive ordered dollar quotes with usable midpoint/ask IV where bid IV is the veto. This recovers most missing strike-bracket observations and gives the 69.6% selected hit rate. Wide or distorted quotes can still pass, so this label does not imply validated fair-value IV.

**Accepted by the primary conservative candidate:** recoverable/otherwise valid observations that also meet the frozen 100% width, prior-quote, and one-sided-distortion rules. This yields 71.0% but sharply reduces coverage. Passing these guards is evidence of passing specified checks, not a guarantee of correct IV.

**Unresolved policy choice:** this test does not establish one definitive deployment threshold. Preserve broad-recovery and conservative-guard views separately. Do not blend their favorable cells, grandfather suspicious originally valid quotes, or change rules until a favorable hit rate appears.

The useful result is an initial-target association that survives measured sensitivity to data handling. A “sustained rally” requirement is outside the user's objective. Additional historical dates with frozen measurement rules would address sampling confidence; independent quote/vendor checks would address measurement confidence. More dates alone do not repair a systematic quote problem. Neither next step was executed here.

## Reproduction, checks, and evidence provenance

The original calculation was in memory and completed in approximately **246 seconds**. It processed 537 available sector-days using two local Python worker threads; these are not independent review agents. No new persona review or independent-agent audit was performed for this recovery run.

Checks completed:

- Original ATM series reproduced on all 537 panels to absolute tolerance 1e−10, with identical missingness.
- Original sector availability, half slopes, acceleration, basket counts, and 93/67 and 217/144 selections reproduced before reporting changed-policy outcomes.
- All 374 frozen outcomes retained: 239/51/84, zero ambiguous.
- Ten synthetic guard checks covered the two real distortion examples, proportional price changes, zero bid, missing previous minute, and exact spread/shock boundaries.
- Two real-data causal prefix checks: XLRE January 6 through 10:15 ET and XLF January 28 through 14:01 ET. Recomputing with all later observations removed left all earlier midpoint/guard values unchanged.
- Features and basket classifications hashed before the new outcome join. Feature hash: **f9ecb370d4fadadd633bf18bfaf11141d43429eb9d4a181145548aebd719f0f5**. Basket hash: **eed2a1cf07f36f427c4ce1cada622950f97045558de75f3ff48eac244dd8511a**.
- All **1,966 raw input hashes** matched the frozen input manifests and remained unchanged at completion. Seven control-file hashes remained unchanged during the run.
- The recorded verification field files_written = 0 describes that empirical run. Saving this document and evidence afterward is a separately authorized documentation action.

[evidence.json](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/evidence.json) contains the exact experiment source, fixed protocol, full emitted results and stdout, earlier gap-only diagnostic source/output, supplied historical context, documentation-environment versions, source paths/hashes captured at documentation, and all fifty sampled dates. Source control hashes captured during documentation are labeled separately from the earlier run's before/after verification; they are not backdated.

The code reads local source artifacts and cached data. Several upstream research folders and the central raw cache are outside the scope of this documentation commit; a fresh checkout of this commit alone is **not** a standalone copy of the full dataset. No upstream untracked research, raw cache, dashboard modifications, or hypothesis-index changes were swept into this commit.

To rerun the archived experiment with the existing local dependencies, this command prints results and does not intentionally write study artifacts:

```sh
PYTHONDONTWRITEBYTECODE=1 /Users/dgrissen/Dev/virtualenvs/gamma_chaser/bin/python -B - <<'PY'
import json
from pathlib import Path
payload = json.loads(Path("/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_recovery_findings_2026-09-19/evidence.json").read_text())
scope = {"PROTOCOL": payload["protocol"]}
exec(compile(payload["experiment_source"], "archived_iv_recovery_experiment", "exec"), scope)
PY
```

The archived source is a record of the completed experiment, not a new production research engine. Reproduction requires the same available local source files, pandas/NumPy dependencies, and raw cache. The documented environment is Python 3.13.1, NumPy 2.4.5, pandas 3.0.3.

Primary local references: [original protocol](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/PROTOCOL.md), [dataset provenance](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/DATASET.md), [original findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/FINDINGS.md), [surface implementation](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/surface.py), [breadth implementation](/Users/dgrissen/Dev/delta_bomb/outputs/b06_sector_surface_50d_2026-09-13/breadth.py), [matched-price findings](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_matched_price_2026-09-17/FINDINGS.md), [acceleration decomposition](/Users/dgrissen/Dev/delta_bomb/outputs/b06_iv_acceleration_increment_2026-09-17/FINDINGS.md), and [post-target study](/Users/dgrissen/Dev/delta_bomb/outputs/b06_post_target_2026-09-17/FINDINGS.md).
