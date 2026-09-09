# Existing HIRO coverage for second-leg analysis

**D1 analysis is supported by existing All Trades captures for only 2 of the 6 names: PLTR on June 15 and ORCL on June 17. A complete six-name D1 comparison cannot be tested with these files.** PLTR alone also has D2 coverage. These conclusions follow from validated timestamps and call-flow windows, not file-path presence. No bullish trigger, trade proposal or frozen-rule change is introduced.

D0 is the initial-entry session in the frozen variant file; D1 and D2 are the next two exchange holding sessions, including the June 19 market holiday. All 18 requested ticker/day combinations are retained. Nine have captures and nine have no archive. The existing inventory has one source for each present pair and no alternate source for the absent pairs. No additional directory search was undertaken.

## Actual usable window coverage

15-minute and 30-minute columns count valid **one-minute information cutoffs through 15:29 ET**, allowing a next-minute action by 15:30. Only windows entirely within regular-session data count: earliest possible cutoffs are 09:45 and 10:00. Their respective maximum counts are 345 and 330. The final count uses the unchanged existing HIRO module’s 55 five-minute decisions from 10:00 through 14:30, each requiring a complete 30-minute window. These are availability counts, not trading signals.

| Ticker | Holding day | Actual session | All Trades RTH first–last ET | Valid 15m /345 | Valid 30m /330 | Existing module /55 |
| --- | --- | --- | --- | --- | --- | --- |
| PLTR | D0 | 2026-06-12 | 09:30:00–16:00:00 | 345 | 330 | 55 |
| PLTR | D1 | 2026-06-15 | 09:30:00–16:00:00 | 345 | 330 | 55 |
| PLTR | D2 | 2026-06-16 | 09:30:00–16:00:00 | 345 | 330 | 55 |
| DIS | D0 | 2026-06-15 | 09:30:20–16:00:00 | 344 | 329 | 54 |
| DIS | D1 | 2026-06-16 | —–— | 0 | 0 | 0 |
| DIS | D2 | 2026-06-17 | —–— | 0 | 0 | 0 |
| MRVL | D0 | 2026-06-16 | 09:30:00–16:00:00 | 345 | 330 | 55 |
| MRVL | D1 | 2026-06-17 | —–— | 0 | 0 | 0 |
| MRVL | D2 | 2026-06-18 | —–— | 0 | 0 | 0 |
| ORCL | D0 | 2026-06-16 | 09:32:05–16:00:00 | 343 | 328 | 54 |
| ORCL | D1 | 2026-06-17 | 09:30:55–16:00:00 | 344 | 329 | 54 |
| ORCL | D2 | 2026-06-18 | —–— | 0 | 0 | 0 |
| QCOM | D0 | 2026-06-16 | 09:30:00–16:00:00 | 345 | 330 | 55 |
| QCOM | D1 | 2026-06-17 | —–— | 0 | 0 | 0 |
| QCOM | D2 | 2026-06-18 | —–— | 0 | 0 | 0 |
| CRM | D0 | 2026-06-17 | 09:30:15–16:00:00 | 344 | 329 | 54 |
| CRM | D1 | 2026-06-18 | —–— | 0 | 0 | 0 |
| CRM | D2 | 2026-06-22 | —–— | 0 | 0 | 0 |

## D1 conclusion

- **PLTR, June 15:** all 345 valid 15-minute windows from 09:45–15:29, all 330 valid 30-minute windows from 10:00–15:29, and 55/55 existing-module windows. The existing series can support a defined call-flow/price confirmation condition over these windows.
- **ORCL, June 17:** 344 valid 15-minute windows from 09:46–15:29 and 329 valid 30-minute windows from 10:01–15:29. The source begins at 09:30:55; the nominal 09:45 and 10:00 windows are incomplete. Existing-module coverage is 54/55, first valid at 10:05. Missing opening observations cannot be classified as “no confirmation.”
- **DIS, MRVL, QCOM and CRM:** no D1 source; there is no call-flow condition to evaluate. Their absence cannot count as a known failure to confirm.
- **D2:** PLTR June 16 is complete after regular-session warmup; the other five names lack a source.

Therefore, existing data permits two D1 case studies, preserving ORCL’s opening gap. It does not permit the whole six-name comparison or meet the protocol’s 20-distinct-date requirement. Only PLTR has a fully covered D0–D2 sequence. Availability does not establish second-leg affordability, option quote freshness, historical deliverables or execution; no option outcomes were read.

## Validation and provenance

Each window was restricted to `series_group=all` and its actual Eastern session. Validation required every five-second slot, no duplicate/off-grid timestamps, finite call/put/total increments and price, positive price and row count, and `delta_total ≈ delta_call + delta_put` using the existing module tolerance. No flow or price was filled. Regular-session warmup uses no overnight data. The module’s bearish initial-entry trigger was not used as a second-leg rule.

PLTR’s file contains several actual session dates despite its June 12 directory name; the June 15 and 16 rows were selected and validated by timestamp. All captures were obtained later, so they do not prove contemporaneous feed receipt or latency. The CSV retains exact source paths, hashes, capture metadata, first/last timestamps, missing-slot counts and window boundaries.

| Ticker | Exact existing source path |
| --- | --- |
| CRM | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_live_monitor_missing_2026-06-17/2026-06-18/071852Z/normalized/CRM_series.csv` |
| DIS | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-15/2026-06-18/113204Z/normalized/DIS_series.csv` |
| MRVL | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-16/2026-06-18/133951Z/normalized/MRVL_series.csv` |
| ORCL | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-16/2026-06-18/133951Z/normalized/ORCL_series.csv` |
| ORCL | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_live_monitor_missing_2026-06-17/2026-06-18/071852Z/normalized/ORCL_series.csv` |
| PLTR | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-12/2026-06-18/100433Z/normalized/PLTR_series.csv` |
| QCOM | `/Users/dgrissen/Dev/HIRO_finder/output/hiro_date_specific_scrapes_2026-06-12_to_2026-06-16/date=2026-06-16/2026-06-18/133951Z/normalized/QCOM_series.csv` |

[Coverage CSV](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/second_leg_hiro_coverage.csv) contains all 18 rows. Holding dates: [variant frozen contracts](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/variant_frozen_contracts.csv). Source inventory: [HIRO archive coverage](/Users/dgrissen/Dev/delta_bomb/outputs/pandar_hypothesis_2026-09-07/hiro_archive_coverage.csv). Existing validator: [pandar_hypothesis_hiro.py](/Users/dgrissen/Dev/delta_bomb/scripts/pandar_hypothesis_hiro.py). No provider calls, source edits or protocol changes.

Coverage CSV SHA-256: `3075d4c4299dcb791c65125fc207664c83f36e8ba47b3052d310d69d546bcd7a`.
