# Charlie / Brent: diagnose the reversal and constrain the B01–B10 rerun

User asks why results were likely worse after adding dates, and asks both personas
to help rerun B01–B10 on the expanded data. Independent analytical persona lenses,
not statements by the real people. Use only cached study evidence; no web, APIs,
HIRO reconstruction, invented positioning or new outcome-based thresholds.

## Recorded facts

The same original B06 plus sector-IV rules were applied to the original 50 dates
and 100 additional dates. The new set contains 66 dates from 2025 and 34 from
2026. The original 50 are all from 2026 and have been used for multiple earlier
research questions. No added dates were replaced based on IV coverage/outcomes.
Selection requires same-day preopen VT corroboration and valid native SPX data;
the selected dates do not include March–July 2025. This is not a certified holdout.

Primary score: +5 before −15 from next observed minute open, within 60 minutes.
Post-target behavior is irrelevant. Same-minute touches are ambiguous, not wins.

| Rule | Original targets/N | Added targets/N |
|---|---:|---:|
| B06 | 239/374 | 371/666 |
| Original IV validity | 67/93 | 104/208 |
| Allow missing bid-IV recovery | 78/112 | 118/228 |
| Recovery + 100% relative spread guard | 49/69 | 84/159 |
| Recovery + 50% relative spread guard | 22/29 | 50/99 |

All IV rows require falling and downward-accelerating 30-calendar-DTE spot-ATM IV
in at least 6 of 11 sector ETFs. This is an ATM proxy, not the full fixed-delta
surface. Two 15-sample slopes cover the 30 minutes before the breakout candle;
acceleration = (second slope − first slope)/15. The denominator stays 11 and
missing sectors can make status unknown. Provider midpoint implied_vol supplies
the measurement; bid IV is a validity criterion in the original variant.

All 150 days opened above VT, but 54 crossed it and 80 entries occurred below VT.
Independent reconstruction matched all 1,040 B06 identities/outcomes, 44,812
available-panel IV feature records and all 4,160 baskets. Restricting to above VT
at entry gives old/new B06 214/340 vs342/620 and original IV58/80 vs95/191.
Requiring continuously above VT from open through entry gives B06 167/265 vs263/497
and original IV39/58 vs76/151; the guarded100 version is34/50 vs64/118.

Original plain-B06 outcomes: 63.9% target,13.6% adverse,22.5% neither.
Added2025:52.0%,10.9%,37.1%; added2026:62.9%,10.7%,26.3%.
Median observed09:30–10:04 range:27.1points original50,21.7 added2025,24.9 added2026.
Original policy's 93 qualifiers occupied35 dates; its208 new qualifiers86 dates.
Original paired-date uplift intervals included zero; dependent signals and the
previous search history limit inference. Conservative quote-envelope uncertainty
previously failed to resolve qualifying acceleration signs beyond zero.

## Requested output

Give your own ranked likely explanations, distinguishing measured facts from
hypotheses. Identify what would falsify each explanation using existing data.
Then review the draft PROTOCOL.md: what must remain fixed, which diagnostics can
explain the shift without turning into a parameter search, and what comparisons
would mislead? Do not turn this into an option-trade profitability study or require
new data. Keep the response concrete and bounded (up to900 words). You may read
the explicitly listed source/protocol files and central CSVs named in the draft;
do not inspect other persona outputs or delegate further agents.
