# End-of-hour price distribution for entries touching neither barrier

User request September20,2026: for the five named unspaced cohorts, describe
where SPX finishes when neither entry+5 nor entry-10 was touched in the original
60-minute window. This is the existing `outcome=neither` group, not the broader
group excluding adverse-first (which also contains target-first winners).

Use unchanged 239 research dates in2025–September18,2026 and frozen combined
685execution ledger. Standalone cohorts: baseline B09 F4-or-SPX318, B05F4 112,
B09five-endpoint persistence492, originalB07six-sector91, combined685. Their
neither counts are43,5,73,15,92, respectively. Cohorts overlap; combined is already
deduplicated by date/minute. Preserve original strict causal above-VT admission.

For each unique neither entry, require all60 native OHLC bars T throughT+59 and
verify no high touches entry+5 and no low touches entry-10. Use the last bar's
close minus entry open as the signed60-minute result. Its label isT+59(start),
and its close is atT+60 under the inherited interval convention. Do not use the
close of barT+60, infer missing bars, or require barrier touches on candle close.

Report pooled and all half-years: original N, neither N/share, active dates,
min/p10/p25/median/p75/p90/p95/max/mean, and negative/flat/positive counts. Quantiles
are existing NumPy linear sample quantiles, not confidence intervals. Float
tolerance1e-8 governs zero and inherited barrier checks. Empty groups retainN=0
and missing statistics. Final values must be strictly within(-10,+5).

Fixed distribution bins: [-10,-7.5),[-7.5,-5),[-5,-2.5),[-2.5,0),[0,2.5),[2.5,5].
Publish exact event values and sorted empirical distributions centrally. Plot
pooled histograms with a common x-axis and percentage rather than count y-axis;
identify small B05N explicitly. No new strategy, spacing, outcome or parameter test.

Verify frozen event/calendar/native-source hashes; reuse existing validated path
and quantile routines, then independently check native window endpoints, no-touch
conditions, subset identities, all distribution counts and pooled quantiles.
Cross-check the43 baseline values with the earlier B09 path-distribution output.
New namespace only; no provider calls or independent reviewer process.
