# Numerical correction: exact date-balanced weighted median

An independent XLF replay found a floating-point boundary error in the inherited
weighted-median helper. On January 2, 2025, block 10:30–11:29, all sixty contributing
dates have sixty observations: 3,600 equally weighted values. The approved left
inverse-CDF median must select sorted observation1,800 (one-based). The inherited
cumulative sum selected observation1,801 because cumulative floating-point error
exceeded its1e−14 tie tolerance. The stored median was −3.0285827853062408e−6;
the correct lower middle observation is −3.234715040832438e−6. The MAD also differs.

This is an implementation correction to the SAME declared date weights and lower
median convention, not a policy change or a new calibrated threshold. Do not
loosen the comparison tolerance to make the independent check pass.

Use exact integer observation weights. If a contributing date has n observations,
let L be the least common multiple of all contributing-date counts. Every
observation on that date has weight L/n. Every date therefore has total weight L.
Select the first sorted value whose cumulative integer mass is at least half the
total mass (ceil(total/2)). Use int64 when the total fits, otherwise Python's
arbitrary-precision integers. Apply the same weights to absolute deviations to
calculate MAD; keep scale=1.4826*MAD and the existing score definitions.

Preserve original sources, windows and first-pass baseline/score outputs. Write
authoritative corrected baselines/scores under calibration_exact/{symbol}/.
Recompute all three ETFs. Quantify which medians, MAD scales and scores changed,
and compare the XLRE pilot rather than assuming its normalization is unchanged.
Verify independent weighted medians using rational empirical-CDF masses, all
sixty-prior-session ledgers, and current score arithmetic. No new market-data
requests, expiry changes, quote changes or strategy outcomes are involved.
