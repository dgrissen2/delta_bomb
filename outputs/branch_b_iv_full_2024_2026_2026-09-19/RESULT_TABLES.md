# Full 2024–2026 IV comparison: result tables

Score: **+5 before −10 in sixty native minutes**. All entries pass strict causal above-VT admission. Primary population: 411 research dates; ten development dates are separate. Timeouts/ambiguous bars count in N. No post-target penalty.

All results are descriptive on previously examined data. The rule inventory is broad, and the 95% whole-date intervals are not adjusted for multiple comparisons. Unknown does not mean that an IV condition failed. N is entries, not independent days.

Complete numerical outputs: `/Users/dgrissen/Dev/central_trade_data/thetadata/branch_b_iv_full_2024_2026_2026-09-19-v1`. See comparison.csv for every rule, family, half-year and thinning mode; unions.csv for every prespecified union.

## Unfiltered price baselines

| variant      |    n |   targets |   rate |   days |   adverse_first |   neither |   ambiguous |
|:-------------|-----:|----------:|-------:|-------:|----------------:|----------:|------------:|
| b01          | 1569 |       813 |   51.8 |    350 |             366 |       388 |           2 |
| thrust       |   92 |        59 |   64.1 |     68 |              25 |         8 |           0 |
| staircase    |  317 |       180 |   56.8 |    191 |              65 |        72 |           0 |
| t            | 1330 |       664 |   49.9 |    311 |             305 |       360 |           1 |
| b05          | 2790 |      1477 |   52.9 |    325 |             701 |       611 |           1 |
| b06_breakout | 2382 |      1208 |   50.7 |    311 |             485 |       689 |           0 |
| b06_retest   |  563 |       292 |   51.9 |    248 |             111 |       160 |           0 |
| b07          |  769 |       393 |   51.1 |    283 |             181 |       195 |           0 |
| b08_price    |  287 |       142 |   49.5 |    201 |              71 |        74 |           0 |
| b08_rsi      |   36 |        19 |   52.8 |     36 |              12 |         5 |           0 |
| b09          | 5560 |      2890 |   52.0 |    315 |            1150 |      1518 |           2 |
| b10_breakout |  260 |       145 |   55.8 |    260 |              68 |        45 |           2 |
| b10_retest   |   61 |        37 |   60.7 |     61 |              14 |        10 |           0 |

## b06_breakout: fixed principal rules

| rule                           |    n |   targets |   rate |   days |   retained_baseline_targets |   unknown_n |   measured_baseline_rate |   ci_low |   ci_high | ci_status            |
|:-------------------------------|-----:|----------:|-------:|-------:|----------------------------:|------------:|-------------------------:|---------:|----------:|:---------------------|
| original_falling_6             | 1454 |       729 |   50.1 |    298 |                       729.0 |         378 |                     49.4 |     46.5 |      53.6 | whole_date_bootstrap |
| original_accelerating_6        |  632 |       315 |   49.8 |    252 |                       315.0 |         365 |                     49.8 |     45.1 |      54.4 | whole_date_bootstrap |
| original_weighted_falling      | 1465 |       741 |   50.6 |    292 |                       741.0 |         185 |                     50.2 |     47.0 |      54.0 | whole_date_bootstrap |
| original_weighted_accelerating |  867 |       425 |   49.0 |    275 |                       425.0 |         183 |                     50.3 |     44.7 |      53.2 | whole_date_bootstrap |
| midpoint_falling_6             | 1523 |       766 |   50.3 |    303 |                       766.0 |         266 |                     49.7 |     46.7 |      53.6 | whole_date_bootstrap |
| midpoint_accelerating_6        |  678 |       341 |   50.3 |    258 |                       341.0 |         261 |                     50.2 |     45.6 |      54.7 | whole_date_bootstrap |
| guarded_100_falling_6          |  953 |       481 |   50.5 |    248 |                       481.0 |        1166 |                     50.4 |     46.1 |      54.7 | whole_date_bootstrap |
| guarded_100_accelerating_6     |  388 |       204 |   52.6 |    184 |                       204.0 |        1189 |                     50.9 |     46.7 |      58.3 | whole_date_bootstrap |
| guarded_50_falling_6           |  574 |       284 |   49.5 |    182 |                       284.0 |        1665 |                     49.2 |     44.4 |      54.4 | whole_date_bootstrap |
| guarded_50_accelerating_6      |  231 |       114 |   49.4 |    121 |                       114.0 |        1695 |                     49.8 |     42.1 |      56.5 | whole_date_bootstrap |
| balanced_falling_6             | 1516 |       769 |   50.7 |    300 |                       769.0 |         286 |                     49.8 |     47.2 |      54.1 | whole_date_bootstrap |
| balanced_accelerating_6        |  655 |       328 |   50.1 |    257 |                       328.0 |         276 |                     50.0 |     45.4 |      54.6 | whole_date_bootstrap |
| paired_price_iv_6              |  801 |       409 |   51.1 |    242 |                       409.0 |         281 |                     49.7 |     46.5 |      55.4 | whole_date_bootstrap |
| price_only_6                   | 1695 |       877 |   51.7 |    298 |                       877.0 |         112 |                     50.8 |     48.3 |      55.0 | whole_date_bootstrap |
| original_falling_and_breakout5 |  906 |       442 |   48.8 |    269 |                       442.0 |         425 |                     49.9 |     44.7 |      52.7 | whole_date_bootstrap |

## thrust: fixed principal rules

| rule                           |   n |   targets |   rate |   days |   retained_baseline_targets |   unknown_n |   measured_baseline_rate |   ci_low |   ci_high | ci_status            |
|:-------------------------------|----:|----------:|-------:|-------:|----------------------------:|------------:|-------------------------:|---------:|----------:|:---------------------|
| original_falling_6             |  52 |        32 |   61.5 |     42 |                        32.0 |          18 |                     60.8 |     47.5 |      74.5 | whole_date_bootstrap |
| original_accelerating_6        |  22 |        15 |   68.2 |     21 |                        15.0 |          15 |                     63.6 |     45.8 |      87.5 | whole_date_bootstrap |
| original_weighted_falling      |  55 |        33 |   60.0 |     42 |                        33.0 |          10 |                     61.0 |     46.0 |      73.4 | whole_date_bootstrap |
| original_weighted_accelerating |  35 |        19 |   54.3 |     28 |                        19.0 |          12 |                     61.2 |     37.1 |      70.0 | whole_date_bootstrap |
| midpoint_falling_6             |  55 |        35 |   63.6 |     45 |                        35.0 |          13 |                     62.0 |     50.0 |      76.1 | whole_date_bootstrap |
| midpoint_accelerating_6        |  24 |        15 |   62.5 |     22 |                        15.0 |          11 |                     64.2 |     41.2 |      81.5 | whole_date_bootstrap |
| guarded_100_falling_6          |  31 |        21 |   67.7 |     28 |                        21.0 |          48 |                     63.6 |     50.0 |      82.9 | whole_date_bootstrap |
| guarded_100_accelerating_6     |  12 |         8 |   66.7 |     11 |                         8.0 |          50 |                     64.3 |     33.3 |      92.3 | whole_date_bootstrap |
| guarded_50_falling_6           |  11 |         8 |   72.7 |     10 |                         8.0 |          74 |                     72.2 |     40.0 |     100.0 | whole_date_bootstrap |
| guarded_50_accelerating_6      |   6 |         4 |   66.7 |      6 |                         4.0 |          73 |                     63.2 |     20.0 |     100.0 | whole_date_bootstrap |
| balanced_falling_6             |  57 |        36 |   63.2 |     46 |                        36.0 |          12 |                     62.5 |     50.0 |      75.5 | whole_date_bootstrap |
| balanced_accelerating_6        |  25 |        17 |   68.0 |     23 |                        17.0 |           9 |                     65.1 |     48.1 |      85.7 | whole_date_bootstrap |
| paired_price_iv_6              |  26 |        16 |   61.5 |     21 |                        16.0 |          15 |                     62.3 |     40.0 |      82.8 | whole_date_bootstrap |
| price_only_6                   |  55 |        36 |   65.5 |     46 |                        36.0 |           6 |                     62.8 |     51.2 |      79.5 | whole_date_bootstrap |
| original_falling_and_breakout5 |  43 |        27 |   62.8 |     37 |                        27.0 |          13 |                     63.3 |     48.4 |      76.7 | whole_date_bootstrap |

## staircase: fixed principal rules

| rule                           |   n |   targets |   rate |   days |   retained_baseline_targets |   unknown_n |   measured_baseline_rate |   ci_low |   ci_high | ci_status            |
|:-------------------------------|----:|----------:|-------:|-------:|----------------------------:|------------:|-------------------------:|---------:|----------:|:---------------------|
| original_falling_6             | 211 |       116 |   55.0 |    150 |                       116.0 |          50 |                     54.7 |     48.4 |      61.1 | whole_date_bootstrap |
| original_accelerating_6        |  95 |        56 |   58.9 |     81 |                        56.0 |          51 |                     52.6 |     49.5 |      68.1 | whole_date_bootstrap |
| original_weighted_falling      | 206 |       117 |   56.8 |    146 |                       117.0 |          32 |                     55.1 |     50.0 |      63.3 | whole_date_bootstrap |
| original_weighted_accelerating | 133 |        80 |   60.2 |    108 |                        80.0 |          34 |                     54.8 |     52.3 |      67.6 | whole_date_bootstrap |
| midpoint_falling_6             | 217 |       119 |   54.8 |    154 |                       119.0 |          40 |                     54.9 |     48.3 |      61.1 | whole_date_bootstrap |
| midpoint_accelerating_6        |  98 |        57 |   58.2 |     82 |                        57.0 |          41 |                     53.3 |     48.7 |      67.0 | whole_date_bootstrap |
| guarded_100_falling_6          | 145 |        85 |   58.6 |    102 |                        85.0 |         146 |                     59.1 |     50.8 |      66.0 | whole_date_bootstrap |
| guarded_100_accelerating_6     |  52 |        33 |   63.5 |     48 |                        33.0 |         167 |                     59.3 |     50.0 |      76.2 | whole_date_bootstrap |
| guarded_50_falling_6           |  85 |        47 |   55.3 |     66 |                        47.0 |         220 |                     58.8 |     44.6 |      65.3 | whole_date_bootstrap |
| guarded_50_accelerating_6      |  30 |        20 |   66.7 |     26 |                        20.0 |         237 |                     62.5 |     50.0 |      82.1 | whole_date_bootstrap |
| balanced_falling_6             | 220 |       123 |   55.9 |    152 |                       123.0 |          38 |                     55.9 |     49.5 |      62.0 | whole_date_bootstrap |
| balanced_accelerating_6        | 100 |        60 |   60.0 |     83 |                        60.0 |          37 |                     54.3 |     51.1 |      68.7 | whole_date_bootstrap |
| paired_price_iv_6              | 117 |        67 |   57.3 |     91 |                        67.0 |          51 |                     54.9 |     48.0 |      65.8 | whole_date_bootstrap |
| price_only_6                   | 235 |       135 |   57.4 |    159 |                       135.0 |          22 |                     56.3 |     51.1 |      63.7 | whole_date_bootstrap |
| original_falling_and_breakout5 | 128 |        67 |   52.3 |    105 |                        67.0 |          55 |                     55.7 |     44.3 |      59.8 | whole_date_bootstrap |

## b09: fixed principal rules

| rule                           |    n |   targets |   rate |   days |   retained_baseline_targets |   unknown_n |   measured_baseline_rate |   ci_low |   ci_high | ci_status            |
|:-------------------------------|-----:|----------:|-------:|-------:|----------------------------:|------------:|-------------------------:|---------:|----------:|:---------------------|
| original_falling_6             | 2949 |      1534 |   52.0 |    301 |                      1534.0 |         920 |                     51.0 |     48.9 |      55.1 | whole_date_bootstrap |
| original_accelerating_6        | 1266 |       676 |   53.4 |    276 |                       676.0 |         841 |                     51.2 |     49.3 |      57.3 | whole_date_bootstrap |
| original_weighted_falling      | 2985 |      1573 |   52.7 |    293 |                      1573.0 |         490 |                     51.7 |     49.6 |      55.7 | whole_date_bootstrap |
| original_weighted_accelerating | 1714 |       911 |   53.2 |    280 |                       911.0 |         484 |                     51.7 |     49.7 |      56.6 | whole_date_bootstrap |
| midpoint_falling_6             | 3101 |      1627 |   52.5 |    302 |                      1627.0 |         644 |                     51.4 |     49.4 |      55.5 | whole_date_bootstrap |
| midpoint_accelerating_6        | 1361 |       734 |   53.9 |    281 |                       734.0 |         580 |                     51.6 |     50.1 |      57.6 | whole_date_bootstrap |
| guarded_100_falling_6          | 1823 |       965 |   52.9 |    260 |                       965.0 |        2818 |                     52.0 |     49.0 |      56.7 | whole_date_bootstrap |
| guarded_100_accelerating_6     |  690 |       378 |   54.8 |    203 |                       378.0 |        2799 |                     51.2 |     49.8 |      59.6 | whole_date_bootstrap |
| guarded_50_falling_6           | 1041 |       536 |   51.5 |    196 |                       536.0 |        4022 |                     51.6 |     46.6 |      56.3 | whole_date_bootstrap |
| guarded_50_accelerating_6      |  382 |       204 |   53.4 |    133 |                       204.0 |        3987 |                     51.9 |     46.0 |      60.4 | whole_date_bootstrap |
| balanced_falling_6             | 3035 |      1582 |   52.1 |    304 |                      1582.0 |         765 |                     51.1 |     49.0 |      55.2 | whole_date_bootstrap |
| balanced_accelerating_6        | 1308 |       696 |   53.2 |    278 |                       696.0 |         700 |                     51.3 |     49.3 |      57.1 | whole_date_bootstrap |
| paired_price_iv_6              | 1403 |       746 |   53.2 |    259 |                       746.0 |         627 |                     51.2 |     49.3 |      57.1 | whole_date_bootstrap |
| price_only_6                   | 3338 |      1722 |   51.6 |    303 |                      1722.0 |         400 |                     51.9 |     48.5 |      54.7 | whole_date_bootstrap |
| original_falling_and_breakout5 | 1407 |       732 |   52.0 |    275 |                       732.0 |         912 |                     51.1 |     48.2 |      55.8 | whole_date_bootstrap |

## b10_breakout: fixed principal rules

| rule                           |   n |   targets |   rate |   days |   retained_baseline_targets |   unknown_n |   measured_baseline_rate |   ci_low |   ci_high | ci_status            |
|:-------------------------------|----:|----------:|-------:|-------:|----------------------------:|------------:|-------------------------:|---------:|----------:|:---------------------|
| original_falling_6             |  71 |        42 |   59.2 |     71 |                        42.0 |         163 |                     55.7 |     47.5 |      70.3 | whole_date_bootstrap |
| original_accelerating_6        |  30 |        20 |   66.7 |     30 |                        20.0 |         160 |                     58.0 |     50.0 |      83.3 | whole_date_bootstrap |
| original_weighted_falling      |  73 |        44 |   60.3 |     73 |                        44.0 |         150 |                     58.2 |     48.7 |      71.2 | whole_date_bootstrap |
| original_weighted_accelerating |  43 |        29 |   67.4 |     43 |                        29.0 |         148 |                     58.9 |     52.6 |      81.0 | whole_date_bootstrap |
| midpoint_falling_6             |  79 |        48 |   60.8 |     79 |                        48.0 |         154 |                     58.5 |     49.4 |      71.4 | whole_date_bootstrap |
| midpoint_accelerating_6        |  34 |        23 |   67.6 |     34 |                        23.0 |         149 |                     59.5 |     51.4 |      82.9 | whole_date_bootstrap |
| guarded_100_falling_6          |  38 |        21 |   55.3 |     38 |                        21.0 |         211 |                     57.1 |     38.9 |      71.0 | whole_date_bootstrap |
| guarded_100_accelerating_6     |  17 |        13 |   76.5 |     17 |                        13.0 |         211 |                     59.2 |     53.8 |      94.7 | whole_date_bootstrap |
| guarded_50_falling_6           |  22 |        15 |   68.2 |     22 |                        15.0 |         232 |                     67.9 |     47.6 |      87.0 | whole_date_bootstrap |
| guarded_50_accelerating_6      |  10 |         7 |   70.0 |     10 |                         7.0 |         233 |                     59.3 |     37.5 |     100.0 | whole_date_bootstrap |
| balanced_falling_6             |  85 |        51 |   60.0 |     85 |                        51.0 |         142 |                     55.9 |     49.4 |      70.6 | whole_date_bootstrap |
| balanced_accelerating_6        |  35 |        22 |   62.9 |     35 |                        22.0 |         134 |                     57.1 |     46.3 |      78.4 | whole_date_bootstrap |
| paired_price_iv_6              |  32 |        20 |   62.5 |     32 |                        20.0 |         146 |                     57.9 |     45.4 |      79.3 | whole_date_bootstrap |
| price_only_6                   |  85 |        50 |   58.8 |     85 |                        50.0 |         132 |                     57.8 |     48.1 |      69.0 | whole_date_bootstrap |
| original_falling_and_breakout5 |  52 |        30 |   57.7 |     52 |                        30.0 |         117 |                     55.2 |     44.0 |      71.1 | whole_date_bootstrap |

## Half-year repeatability: B06

Each cell shows target-first count / N, hit rate, and distinct trading dates. Half-year estimates are descriptive; intervals are pooled only. Small date counts cannot establish repeatability. Empty cells are unavailable, not zero success.

| rule                           | 2024_H1                  | 2024_H2                  | 2025_H1                  | 2025_H2                  | 2026_H1                  | 2026_H2                |
|:-------------------------------|:-------------------------|:-------------------------|:-------------------------|:-------------------------|:-------------------------|:-----------------------|
| balanced_accelerating_6        | 63/146 (43.2%; 55 days)  | 69/143 (48.3%; 53 days)  | 58/109 (53.2%; 42 days)  | 72/152 (47.4%; 59 days)  | 54/84 (64.3%; 40 days)   | 12/21 (57.1%; 8 days)  |
| balanced_falling_6             | 159/335 (47.5%; 69 days) | 161/317 (50.8%; 63 days) | 136/258 (52.7%; 46 days) | 155/341 (45.5%; 64 days) | 124/214 (57.9%; 48 days) | 34/51 (66.7%; 10 days) |
| baseline                       | 260/555 (46.8%; 72 days) | 263/525 (50.1%; 67 days) | 201/385 (52.2%; 47 days) | 216/467 (46.3%; 66 days) | 207/362 (57.2%; 49 days) | 61/88 (69.3%; 10 days) |
| guarded_100_accelerating_6     | 36/91 (39.6%; 39 days)   | 26/56 (46.4%; 29 days)   | 31/52 (59.6%; 28 days)   | 58/105 (55.2%; 47 days)  | 41/63 (65.1%; 33 days)   | 12/21 (57.1%; 8 days)  |
| guarded_100_falling_6          | 90/202 (44.6%; 50 days)  | 71/140 (50.7%; 40 days)  | 83/160 (51.9%; 43 days)  | 119/257 (46.3%; 62 days) | 93/156 (59.6%; 43 days)  | 25/38 (65.8%; 10 days) |
| guarded_50_accelerating_6      | 28/70 (40.0%; 25 days)   | 22/40 (55.0%; 23 days)   | 14/27 (51.9%; 17 days)   | 27/56 (48.2%; 34 days)   | 18/31 (58.1%; 19 days)   | 5/7 (71.4%; 3 days)    |
| guarded_50_falling_6           | 73/146 (50.0%; 35 days)  | 45/90 (50.0%; 28 days)   | 37/70 (52.9%; 29 days)   | 65/155 (41.9%; 53 days)  | 52/95 (54.7%; 30 days)   | 12/18 (66.7%; 7 days)  |
| midpoint_accelerating_6        | 64/149 (43.0%; 56 days)  | 69/141 (48.9%; 52 days)  | 56/108 (51.9%; 41 days)  | 76/157 (48.4%; 59 days)  | 61/99 (61.6%; 42 days)   | 15/24 (62.5%; 8 days)  |
| midpoint_falling_6             | 156/333 (46.8%; 70 days) | 160/313 (51.1%; 63 days) | 132/254 (52.0%; 46 days) | 153/342 (44.7%; 65 days) | 127/226 (56.2%; 49 days) | 38/55 (69.1%; 10 days) |
| original_accelerating_6        | 62/144 (43.1%; 55 days)  | 66/139 (47.5%; 53 days)  | 56/106 (52.8%; 41 days)  | 67/143 (46.9%; 57 days)  | 52/81 (64.2%; 39 days)   | 12/19 (63.2%; 7 days)  |
| original_falling_6             | 151/325 (46.5%; 69 days) | 156/306 (51.0%; 62 days) | 128/249 (51.4%; 46 days) | 142/323 (44.0%; 64 days) | 121/205 (59.0%; 47 days) | 31/46 (67.4%; 10 days) |
| original_falling_and_breakout5 | 88/202 (43.6%; 64 days)  | 95/190 (50.0%; 53 days)  | 79/152 (52.0%; 42 days)  | 102/224 (45.5%; 60 days) | 63/115 (54.8%; 41 days)  | 15/23 (65.2%; 9 days)  |
| original_weighted_accelerating | 88/194 (45.4%; 63 days)  | 99/194 (51.0%; 60 days)  | 68/132 (51.5%; 43 days)  | 70/167 (41.9%; 55 days)  | 80/144 (55.6%; 45 days)  | 20/36 (55.6%; 9 days)  |
| original_weighted_falling      | 160/337 (47.5%; 69 days) | 172/335 (51.3%; 62 days) | 131/241 (54.4%; 45 days) | 126/282 (44.7%; 58 days) | 122/219 (55.7%; 48 days) | 30/51 (58.8%; 10 days) |
| paired_price_iv_6              | 101/193 (52.3%; 51 days) | 90/177 (50.8%; 52 days)  | 84/160 (52.5%; 42 days)  | 80/178 (44.9%; 53 days)  | 46/78 (59.0%; 34 days)   | 8/15 (53.3%; 10 days)  |
| price_only_6                   | 202/399 (50.6%; 68 days) | 193/369 (52.3%; 63 days) | 157/296 (53.0%; 46 days) | 159/342 (46.5%; 63 days) | 128/231 (55.4%; 48 days) | 38/58 (65.5%; 10 days) |

## Prespecified ways to expand N beyond thrust

A union includes thrust plus IV-qualified entries from the named family. Same date/minute is counted once. Extra columns measure executions outside thrust. The all-entry union retains every thrust entry; first/spaced modes may choose a different entry.

| union                                             |    n |   targets |   rate |   extra_n |   extra_targets |   extra_rate |
|:--------------------------------------------------|-----:|----------:|-------:|----------:|----------------:|-------------:|
| thrust_plus_b06__original_falling_6               | 1503 |       762 |   50.7 |      1411 |             703 |         49.8 |
| thrust_plus_b09__original_falling_6               | 3031 |      1588 |   52.4 |      2939 |            1529 |         52.0 |
| thrust_plus_b10__original_falling_6               |  155 |        95 |   61.3 |        63 |              36 |         57.1 |
| thrust_plus_all_three__original_falling_6         | 4243 |      2195 |   51.7 |      4151 |            2136 |         51.5 |
| thrust_plus_b06__original_falling_8               |  647 |       349 |   53.9 |       555 |             290 |         52.3 |
| thrust_plus_b09__original_falling_8               | 1126 |       605 |   53.7 |      1034 |             546 |         52.8 |
| thrust_plus_b10__original_falling_8               |  111 |        71 |   64.0 |        19 |              12 |         63.2 |
| thrust_plus_all_three__original_falling_8         | 1599 |       855 |   53.5 |      1507 |             796 |         52.8 |
| thrust_plus_b06__original_accelerating_6          |  709 |       364 |   51.3 |       617 |             305 |         49.4 |
| thrust_plus_b09__original_accelerating_6          | 1355 |       733 |   54.1 |      1263 |             674 |         53.4 |
| thrust_plus_b10__original_accelerating_6          |  117 |        75 |   64.1 |        25 |              16 |         64.0 |
| thrust_plus_all_three__original_accelerating_6    | 1887 |       997 |   52.8 |      1795 |             938 |         52.3 |
| thrust_plus_b06__original_accelerating_8          |  229 |       131 |   57.2 |       137 |              72 |         52.6 |
| thrust_plus_b09__original_accelerating_8          |  305 |       182 |   59.7 |       213 |             123 |         57.7 |
| thrust_plus_b10__original_accelerating_8          |   96 |        61 |   63.5 |         4 |               2 |         50.0 |
| thrust_plus_all_three__original_accelerating_8    |  423 |       243 |   57.4 |       331 |             184 |         55.6 |
| thrust_plus_b06__midpoint_falling_6               | 1569 |       796 |   50.7 |      1477 |             737 |         49.9 |
| thrust_plus_b09__midpoint_falling_6               | 3182 |      1680 |   52.8 |      3090 |            1621 |         52.5 |
| thrust_plus_b10__midpoint_falling_6               |  161 |        99 |   61.5 |        69 |              40 |         58.0 |
| thrust_plus_all_three__midpoint_falling_6         | 4452 |      2316 |   52.0 |      4360 |            2257 |         51.8 |
| thrust_plus_b06__midpoint_falling_8               |  697 |       372 |   53.4 |       605 |             313 |         51.7 |
| thrust_plus_b09__midpoint_falling_8               | 1215 |       659 |   54.2 |      1123 |             600 |         53.4 |
| thrust_plus_b10__midpoint_falling_8               |  114 |        72 |   63.2 |        22 |              13 |         59.1 |
| thrust_plus_all_three__midpoint_falling_8         | 1733 |       926 |   53.4 |      1641 |             867 |         52.8 |
| thrust_plus_b06__midpoint_accelerating_6          |  753 |       390 |   51.8 |       661 |             331 |         50.1 |
| thrust_plus_b09__midpoint_accelerating_6          | 1449 |       791 |   54.6 |      1357 |             732 |         53.9 |
| thrust_plus_b10__midpoint_accelerating_6          |  120 |        77 |   64.2 |        28 |              18 |         64.3 |
| thrust_plus_all_three__midpoint_accelerating_6    | 2022 |      1078 |   53.3 |      1930 |            1019 |         52.8 |
| thrust_plus_b06__midpoint_accelerating_8          |  247 |       140 |   56.7 |       155 |              81 |         52.3 |
| thrust_plus_b09__midpoint_accelerating_8          |  332 |       200 |   60.2 |       240 |             141 |         58.8 |
| thrust_plus_b10__midpoint_accelerating_8          |   97 |        62 |   63.9 |         5 |               3 |         60.0 |
| thrust_plus_all_three__midpoint_accelerating_8    |  468 |       270 |   57.7 |       376 |             211 |         56.1 |
| thrust_plus_b06__guarded_100_falling_6            | 1018 |       522 |   51.3 |       926 |             463 |         50.0 |
| thrust_plus_b09__guarded_100_falling_6            | 1911 |      1021 |   53.4 |      1819 |             962 |         52.9 |
| thrust_plus_b10__guarded_100_falling_6            |  125 |        75 |   60.0 |        33 |              16 |         48.5 |
| thrust_plus_all_three__guarded_100_falling_6      | 2711 |      1425 |   52.6 |      2619 |            1366 |         52.2 |
| thrust_plus_b06__guarded_100_falling_8            |  404 |       217 |   53.7 |       312 |             158 |         50.6 |
| thrust_plus_b09__guarded_100_falling_8            |  586 |       343 |   58.5 |       494 |             284 |         57.5 |
| thrust_plus_b10__guarded_100_falling_8            |  100 |        63 |   63.0 |         8 |               4 |         50.0 |
| thrust_plus_all_three__guarded_100_falling_8      |  865 |       487 |   56.3 |       773 |             428 |         55.4 |
| thrust_plus_b06__guarded_100_accelerating_6       |  471 |       257 |   54.6 |       379 |             198 |         52.2 |
| thrust_plus_b09__guarded_100_accelerating_6       |  781 |       437 |   56.0 |       689 |             378 |         54.9 |
| thrust_plus_b10__guarded_100_accelerating_6       |  106 |        69 |   65.1 |        14 |              10 |         71.4 |
| thrust_plus_all_three__guarded_100_accelerating_6 | 1121 |       617 |   55.0 |      1029 |             558 |         54.2 |
| thrust_plus_b06__guarded_100_accelerating_8       |  175 |        98 |   56.0 |        83 |              39 |         47.0 |
| thrust_plus_b09__guarded_100_accelerating_8       |  197 |       128 |   65.0 |       105 |              69 |         65.7 |
| thrust_plus_b10__guarded_100_accelerating_8       |   95 |        60 |   63.2 |         3 |               1 |         33.3 |
| thrust_plus_all_three__guarded_100_accelerating_8 |  275 |       165 |   60.0 |       183 |             106 |         57.9 |
| thrust_plus_b06__guarded_50_falling_6             |  655 |       335 |   51.1 |       563 |             276 |         49.0 |
| thrust_plus_b09__guarded_50_falling_6             | 1132 |       595 |   52.6 |      1040 |             536 |         51.5 |
| thrust_plus_b10__guarded_50_falling_6             |  111 |        71 |   64.0 |        19 |              12 |         63.2 |
| thrust_plus_all_three__guarded_50_falling_6       | 1628 |       841 |   51.7 |      1536 |             782 |         50.9 |
| thrust_plus_b06__guarded_50_falling_8             |  252 |       135 |   53.6 |       160 |              76 |         47.5 |
| thrust_plus_b09__guarded_50_falling_8             |  360 |       207 |   57.5 |       268 |             148 |         55.2 |
| thrust_plus_b10__guarded_50_falling_8             |  100 |        63 |   63.0 |         8 |               4 |         50.0 |
| thrust_plus_all_three__guarded_50_falling_8       |  504 |       278 |   55.2 |       412 |             219 |         53.2 |
| thrust_plus_b06__guarded_50_accelerating_6        |  317 |       169 |   53.3 |       225 |             110 |         48.9 |
| thrust_plus_b09__guarded_50_accelerating_6        |  473 |       263 |   55.6 |       381 |             204 |         53.5 |
| thrust_plus_b10__guarded_50_accelerating_6        |  100 |        64 |   64.0 |         8 |               5 |         62.5 |
| thrust_plus_all_three__guarded_50_accelerating_6  |  677 |       365 |   53.9 |       585 |             306 |         52.3 |
| thrust_plus_b06__guarded_50_accelerating_8        |  144 |        84 |   58.3 |        52 |              25 |         48.1 |
| thrust_plus_b09__guarded_50_accelerating_8        |  158 |       103 |   65.2 |        66 |              44 |         66.7 |
| thrust_plus_b10__guarded_50_accelerating_8        |   94 |        60 |   63.8 |         2 |               1 |         50.0 |
| thrust_plus_all_three__guarded_50_accelerating_8  |  207 |       126 |   60.9 |       115 |              67 |         58.3 |
| thrust_plus_b06__balanced_falling_6               | 1561 |       798 |   51.1 |      1469 |             739 |         50.3 |
| thrust_plus_b09__balanced_falling_6               | 3116 |      1635 |   52.5 |      3024 |            1576 |         52.1 |
| thrust_plus_b10__balanced_falling_6               |  167 |       102 |   61.1 |        75 |              43 |         57.3 |
| thrust_plus_all_three__balanced_falling_6         | 4379 |      2273 |   51.9 |      4287 |            2214 |         51.6 |
| thrust_plus_b06__balanced_falling_8               |  684 |       368 |   53.8 |       592 |             309 |         52.2 |
| thrust_plus_b09__balanced_falling_8               | 1174 |       634 |   54.0 |      1082 |             575 |         53.1 |
| thrust_plus_b10__balanced_falling_8               |  118 |        74 |   62.7 |        26 |              15 |         57.7 |
| thrust_plus_all_three__balanced_falling_8         | 1679 |       896 |   53.4 |      1587 |             837 |         52.7 |
| thrust_plus_b06__balanced_accelerating_6          |  730 |       375 |   51.4 |       638 |             316 |         49.5 |
| thrust_plus_b09__balanced_accelerating_6          | 1397 |       753 |   53.9 |      1305 |             694 |         53.2 |
| thrust_plus_b10__balanced_accelerating_6          |  121 |        76 |   62.8 |        29 |              17 |         58.6 |
| thrust_plus_all_three__balanced_accelerating_6    | 1948 |      1026 |   52.7 |      1856 |             967 |         52.1 |
| thrust_plus_b06__balanced_accelerating_8          |  239 |       136 |   56.9 |       147 |              77 |         52.4 |
| thrust_plus_b09__balanced_accelerating_8          |  321 |       191 |   59.5 |       229 |             132 |         57.6 |
| thrust_plus_b10__balanced_accelerating_8          |   96 |        61 |   63.5 |         4 |               2 |         50.0 |
| thrust_plus_all_three__balanced_accelerating_8    |  448 |       256 |   57.1 |       356 |             197 |         55.3 |
| thrust_plus_b06__paired_price_iv_6                |  868 |       453 |   52.2 |       776 |             394 |         50.8 |
| thrust_plus_b09__paired_price_iv_6                | 1490 |       803 |   53.9 |      1398 |             744 |         53.2 |
| thrust_plus_b10__paired_price_iv_6                |  118 |        74 |   62.7 |        26 |              15 |         57.7 |
| thrust_plus_all_three__paired_price_iv_6          | 2154 |      1139 |   52.9 |      2062 |            1080 |         52.4 |
| thrust_plus_b06__paired_price_iv_8                |  329 |       180 |   54.7 |       237 |             121 |         51.1 |
| thrust_plus_b09__paired_price_iv_8                |  539 |       296 |   54.9 |       447 |             237 |         53.0 |
| thrust_plus_b10__paired_price_iv_8                |   97 |        63 |   64.9 |         5 |               4 |         80.0 |
| thrust_plus_all_three__paired_price_iv_8          |  737 |       399 |   54.1 |       645 |             340 |         52.7 |

## IV versus comparable sector prices

| rule                    | scope       |   pairs |   yes_targets |   no_targets |   yes_rate |   no_rate |   unmatched | status   |
|:------------------------|:------------|--------:|--------------:|-------------:|-----------:|----------:|------------:|:---------|
| original_accelerating_6 | global      |     509 |           256 |          247 |       50.3 |      48.5 |        1364 | matched  |
| original_accelerating_6 | within_half |     497 |           252 |          247 |       50.7 |      49.7 |        1388 | matched  |
| original_falling_6      | global      |     432 |           208 |          201 |       48.1 |      46.5 |        1518 | matched  |
| original_falling_6      | within_half |     421 |           223 |          194 |       53.0 |      46.1 |        1540 | matched  |
| midpoint_accelerating_6 | global      |     550 |           277 |          272 |       50.4 |      49.5 |        1282 | matched  |
| midpoint_accelerating_6 | within_half |     533 |           270 |          264 |       50.7 |      49.5 |        1316 | matched  |
| paired_price_iv_6       | global      |     296 |           153 |          144 |       51.7 |      48.6 |        1790 | matched  |
| paired_price_iv_6       | within_half |     286 |           150 |          134 |       52.4 |      46.9 |        1810 | matched  |

Same rising-sector count and at most ten basis points difference in median signed sector return; one-to-one maximum-cardinality matching without replacement. Within-half matching prevents cross-half pairing. This controls observed price features only.

## T+15 confirmation: new entry and fresh sixty-minute score

| period   | rule                    |   vt_excluded_parents |    n |   targets |   days |   rate |   adverse_first |   neither |   ambiguous |
|:---------|:------------------------|----------------------:|-----:|----------:|-------:|-------:|----------------:|----------:|------------:|
| pooled   | all_delayed_b06         |                     1 | 2381 |      1201 |    310 |   50.4 |             486 |       693 |           1 |
| pooled   | pre_paired_yes          |                     1 |  801 |       399 |    242 |   49.8 |             173 |       229 |           0 |
| pooled   | pre_and_post_paired_yes |                     1 |  156 |        83 |     87 |   53.2 |              38 |        35 |           0 |
| pooled   | pre_yes_post_no         |                     1 |  584 |       287 |    226 |   49.1 |             124 |       173 |           0 |
| pooled   | pre_yes_post_unknown    |                     1 |   61 |        29 |     47 |   47.5 |              11 |        21 |           0 |

These are new entries at T+15, gated against VT again. They cannot improve the original entry retrospectively. The earlier pilot used a remaining 45-minute horizon; this run uses the requested fresh sixty minutes and is labeled accordingly.

## Every rule in the registry

| rule                                 | category           | label                                                        |   threshold | union   |
|:-------------------------------------|:-------------------|:-------------------------------------------------------------|------------:|:--------|
| original_falling_6                   | primary            | original: falling, ≥6 sectors                                |         6   | True    |
| original_falling_8                   | primary            | original: falling, ≥8 sectors                                |         8   | True    |
| original_accelerating_6              | primary            | original: accelerating, ≥6 sectors                           |         6   | True    |
| original_accelerating_8              | primary            | original: accelerating, ≥8 sectors                           |         8   | True    |
| original_weighted_falling            | weighted           | original_weighted_falling                                    |         0.5 | False   |
| original_weighted_accelerating       | weighted           | original_weighted_accelerating                               |         0.5 | False   |
| midpoint_falling_6                   | primary            | midpoint: falling, ≥6 sectors                                |         6   | True    |
| midpoint_falling_8                   | primary            | midpoint: falling, ≥8 sectors                                |         8   | True    |
| midpoint_accelerating_6              | primary            | midpoint: accelerating, ≥6 sectors                           |         6   | True    |
| midpoint_accelerating_8              | primary            | midpoint: accelerating, ≥8 sectors                           |         8   | True    |
| midpoint_weighted_falling            | weighted           | midpoint_weighted_falling                                    |         0.5 | False   |
| midpoint_weighted_accelerating       | weighted           | midpoint_weighted_accelerating                               |         0.5 | False   |
| guarded_100_falling_6                | primary            | guarded_100: falling, ≥6 sectors                             |         6   | True    |
| guarded_100_falling_8                | primary            | guarded_100: falling, ≥8 sectors                             |         8   | True    |
| guarded_100_accelerating_6           | primary            | guarded_100: accelerating, ≥6 sectors                        |         6   | True    |
| guarded_100_accelerating_8           | primary            | guarded_100: accelerating, ≥8 sectors                        |         8   | True    |
| guarded_100_weighted_falling         | weighted           | guarded_100_weighted_falling                                 |         0.5 | False   |
| guarded_100_weighted_accelerating    | weighted           | guarded_100_weighted_accelerating                            |         0.5 | False   |
| guarded_50_falling_6                 | primary            | guarded_50: falling, ≥6 sectors                              |         6   | True    |
| guarded_50_falling_8                 | primary            | guarded_50: falling, ≥8 sectors                              |         8   | True    |
| guarded_50_accelerating_6            | primary            | guarded_50: accelerating, ≥6 sectors                         |         6   | True    |
| guarded_50_accelerating_8            | primary            | guarded_50: accelerating, ≥8 sectors                         |         8   | True    |
| guarded_50_weighted_falling          | weighted           | guarded_50_weighted_falling                                  |         0.5 | False   |
| guarded_50_weighted_accelerating     | weighted           | guarded_50_weighted_accelerating                             |         0.5 | False   |
| balanced_falling_6                   | primary            | balanced: falling, ≥6 sectors                                |         6   | True    |
| balanced_falling_8                   | primary            | balanced: falling, ≥8 sectors                                |         8   | True    |
| balanced_accelerating_6              | primary            | balanced: accelerating, ≥6 sectors                           |         6   | True    |
| balanced_accelerating_8              | primary            | balanced: accelerating, ≥8 sectors                           |         8   | True    |
| balanced_weighted_falling            | weighted           | balanced_weighted_falling                                    |         0.5 | False   |
| balanced_weighted_accelerating       | weighted           | balanced_weighted_accelerating                               |         0.5 | False   |
| atm_full_falling_6                   | surface_diagnostic | atm: full_falling, ≥6                                        |         6   | False   |
| atm_full_falling_8                   | surface_diagnostic | atm: full_falling, ≥8                                        |         8   | False   |
| atm_full_rising_6                    | surface_diagnostic | atm: full_rising, ≥6                                         |         6   | False   |
| atm_full_rising_8                    | surface_diagnostic | atm: full_rising, ≥8                                         |         8   | False   |
| atm_second_half_falling_6            | surface_diagnostic | atm: second_half_falling, ≥6                                 |         6   | False   |
| atm_second_half_falling_8            | surface_diagnostic | atm: second_half_falling, ≥8                                 |         8   | False   |
| atm_second_half_rising_6             | surface_diagnostic | atm: second_half_rising, ≥6                                  |         6   | False   |
| atm_second_half_rising_8             | surface_diagnostic | atm: second_half_rising, ≥8                                  |         8   | False   |
| atm_falling_accelerating_6           | surface_diagnostic | atm: falling_accelerating, ≥6                                |         6   | False   |
| atm_falling_accelerating_8           | surface_diagnostic | atm: falling_accelerating, ≥8                                |         8   | False   |
| atm_falling_slowing_6                | surface_diagnostic | atm: falling_slowing, ≥6                                     |         6   | False   |
| atm_falling_slowing_8                | surface_diagnostic | atm: falling_slowing, ≥8                                     |         8   | False   |
| atm_rising_accelerating_6            | surface_diagnostic | atm: rising_accelerating, ≥6                                 |         6   | False   |
| atm_rising_accelerating_8            | surface_diagnostic | atm: rising_accelerating, ≥8                                 |         8   | False   |
| atm_rising_slowing_6                 | surface_diagnostic | atm: rising_slowing, ≥6                                      |         6   | False   |
| atm_rising_slowing_8                 | surface_diagnostic | atm: rising_slowing, ≥8                                      |         8   | False   |
| put_richness_full_falling_6          | surface_diagnostic | put_richness: full_falling, ≥6                               |         6   | False   |
| put_richness_full_falling_8          | surface_diagnostic | put_richness: full_falling, ≥8                               |         8   | False   |
| put_richness_full_rising_6           | surface_diagnostic | put_richness: full_rising, ≥6                                |         6   | False   |
| put_richness_full_rising_8           | surface_diagnostic | put_richness: full_rising, ≥8                                |         8   | False   |
| put_richness_second_half_falling_6   | surface_diagnostic | put_richness: second_half_falling, ≥6                        |         6   | False   |
| put_richness_second_half_falling_8   | surface_diagnostic | put_richness: second_half_falling, ≥8                        |         8   | False   |
| put_richness_second_half_rising_6    | surface_diagnostic | put_richness: second_half_rising, ≥6                         |         6   | False   |
| put_richness_second_half_rising_8    | surface_diagnostic | put_richness: second_half_rising, ≥8                         |         8   | False   |
| put_richness_falling_accelerating_6  | surface_diagnostic | put_richness: falling_accelerating, ≥6                       |         6   | False   |
| put_richness_falling_accelerating_8  | surface_diagnostic | put_richness: falling_accelerating, ≥8                       |         8   | False   |
| put_richness_falling_slowing_6       | surface_diagnostic | put_richness: falling_slowing, ≥6                            |         6   | False   |
| put_richness_falling_slowing_8       | surface_diagnostic | put_richness: falling_slowing, ≥8                            |         8   | False   |
| put_richness_rising_accelerating_6   | surface_diagnostic | put_richness: rising_accelerating, ≥6                        |         6   | False   |
| put_richness_rising_accelerating_8   | surface_diagnostic | put_richness: rising_accelerating, ≥8                        |         8   | False   |
| put_richness_rising_slowing_6        | surface_diagnostic | put_richness: rising_slowing, ≥6                             |         6   | False   |
| put_richness_rising_slowing_8        | surface_diagnostic | put_richness: rising_slowing, ≥8                             |         8   | False   |
| call_richness_full_falling_6         | surface_diagnostic | call_richness: full_falling, ≥6                              |         6   | False   |
| call_richness_full_falling_8         | surface_diagnostic | call_richness: full_falling, ≥8                              |         8   | False   |
| call_richness_full_rising_6          | surface_diagnostic | call_richness: full_rising, ≥6                               |         6   | False   |
| call_richness_full_rising_8          | surface_diagnostic | call_richness: full_rising, ≥8                               |         8   | False   |
| call_richness_second_half_falling_6  | surface_diagnostic | call_richness: second_half_falling, ≥6                       |         6   | False   |
| call_richness_second_half_falling_8  | surface_diagnostic | call_richness: second_half_falling, ≥8                       |         8   | False   |
| call_richness_second_half_rising_6   | surface_diagnostic | call_richness: second_half_rising, ≥6                        |         6   | False   |
| call_richness_second_half_rising_8   | surface_diagnostic | call_richness: second_half_rising, ≥8                        |         8   | False   |
| call_richness_falling_accelerating_6 | surface_diagnostic | call_richness: falling_accelerating, ≥6                      |         6   | False   |
| call_richness_falling_accelerating_8 | surface_diagnostic | call_richness: falling_accelerating, ≥8                      |         8   | False   |
| call_richness_falling_slowing_6      | surface_diagnostic | call_richness: falling_slowing, ≥6                           |         6   | False   |
| call_richness_falling_slowing_8      | surface_diagnostic | call_richness: falling_slowing, ≥8                           |         8   | False   |
| call_richness_rising_accelerating_6  | surface_diagnostic | call_richness: rising_accelerating, ≥6                       |         6   | False   |
| call_richness_rising_accelerating_8  | surface_diagnostic | call_richness: rising_accelerating, ≥8                       |         8   | False   |
| call_richness_rising_slowing_6       | surface_diagnostic | call_richness: rising_slowing, ≥6                            |         6   | False   |
| call_richness_rising_slowing_8       | surface_diagnostic | call_richness: rising_slowing, ≥8                            |         8   | False   |
| risk_reversal_full_falling_6         | surface_diagnostic | risk_reversal: full_falling, ≥6                              |         6   | False   |
| risk_reversal_full_falling_8         | surface_diagnostic | risk_reversal: full_falling, ≥8                              |         8   | False   |
| risk_reversal_full_rising_6          | surface_diagnostic | risk_reversal: full_rising, ≥6                               |         6   | False   |
| risk_reversal_full_rising_8          | surface_diagnostic | risk_reversal: full_rising, ≥8                               |         8   | False   |
| risk_reversal_second_half_falling_6  | surface_diagnostic | risk_reversal: second_half_falling, ≥6                       |         6   | False   |
| risk_reversal_second_half_falling_8  | surface_diagnostic | risk_reversal: second_half_falling, ≥8                       |         8   | False   |
| risk_reversal_second_half_rising_6   | surface_diagnostic | risk_reversal: second_half_rising, ≥6                        |         6   | False   |
| risk_reversal_second_half_rising_8   | surface_diagnostic | risk_reversal: second_half_rising, ≥8                        |         8   | False   |
| risk_reversal_falling_accelerating_6 | surface_diagnostic | risk_reversal: falling_accelerating, ≥6                      |         6   | False   |
| risk_reversal_falling_accelerating_8 | surface_diagnostic | risk_reversal: falling_accelerating, ≥8                      |         8   | False   |
| risk_reversal_falling_slowing_6      | surface_diagnostic | risk_reversal: falling_slowing, ≥6                           |         6   | False   |
| risk_reversal_falling_slowing_8      | surface_diagnostic | risk_reversal: falling_slowing, ≥8                           |         8   | False   |
| risk_reversal_rising_accelerating_6  | surface_diagnostic | risk_reversal: rising_accelerating, ≥6                       |         6   | False   |
| risk_reversal_rising_accelerating_8  | surface_diagnostic | risk_reversal: rising_accelerating, ≥8                       |         8   | False   |
| risk_reversal_rising_slowing_6       | surface_diagnostic | risk_reversal: rising_slowing, ≥6                            |         6   | False   |
| risk_reversal_rising_slowing_8       | surface_diagnostic | risk_reversal: rising_slowing, ≥8                            |         8   | False   |
| quote_resolved_falling_6             | quote_diagnostic   | Quote resolved falling, ≥6                                   |         6   | False   |
| quote_resolved_falling_8             | quote_diagnostic   | Quote resolved falling, ≥8                                   |         8   | False   |
| quote_resolved_accelerating_6        | quote_diagnostic   | Quote resolved accelerating, ≥6                              |         6   | False   |
| quote_resolved_accelerating_8        | quote_diagnostic   | Quote resolved accelerating, ≥8                              |         8   | False   |
| paired_price_iv_6                    | primary            | Price rising AND IV endpoint falling, ≥6                     |         6   | True    |
| price_only_6                         | price_control      | Price rising, ≥6                                             |         6   | False   |
| paired_price_iv_8                    | primary            | Price rising AND IV endpoint falling, ≥8                     |         8   | True    |
| price_only_8                         | price_control      | Price rising, ≥8                                             |         8   | False   |
| post15_paired_6                      | delayed_only       | Paired price/IV at T+15; new entry required                  |         6   | False   |
| breakout5_falling_6                  | confirmation       | Breakout five-minute IV falling                              |         6   | False   |
| original_falling_and_breakout5       | confirmation       | Reference falling plus contemporaneous breakout confirmation |         6   | False   |

MAD magnitude, alternate monthly-only/short-tenor constructions and constituent-level surface strategies are not tested here. They are recorded in IDEA_INVENTORY.md.

# Additional review disclosures

These tables are an additive presentation of the unchanged verified results. Structural missingness, unknown-cohort performance and the eight-sector candidates remain visible. All counts below are primary recipe entries; different families can share an execution, so do not sum them as unique trades.

## Signals before a full same-session reference can exist

741 primary recipe entries occur before 10:05 ET. Their T−35 reference begins before 09:30; no amount of quote recovery fixes this structural gap. All other unresolved conditions and rejected issuer snapshots are separated in unknown_reason_summary.csv. Native expiry gaps are additionally recorded per entry in entry_missingness_context.parquet.

| variant      |   n |   targets |   rate |   days |
|:-------------|----:|----------:|-------:|-------:|
| b01          | 350 |       203 |   58.0 |    350 |
| b08_price    |   5 |         4 |   80.0 |      5 |
| b08_rsi      |   1 |         1 |  100.0 |      1 |
| b09          | 167 |        89 |   53.3 |    151 |
| b10_breakout | 120 |        64 |   53.3 |    120 |
| b10_retest   |  11 |         6 |   54.5 |     11 |
| staircase    |   8 |         6 |   75.0 |      8 |
| t            |  76 |        37 |   48.7 |     76 |
| thrust       |   3 |         3 |  100.0 |      3 |

## b06_breakout: yes, no, unknown and comparable coverage

| rule                       | state    |    n |   targets |   rate |   days |
|:---------------------------|:---------|-----:|----------:|-------:|-------:|
| original_falling_6         | yes      | 1454 |       729 |   50.1 |    298 |
| original_falling_6         | no       |  550 |       261 |   47.5 |    236 |
| original_falling_6         | unknown  |  378 |       218 |   57.7 |    153 |
| original_falling_6         | measured | 2004 |       990 |   49.4 |    304 |
| original_falling_6         | baseline | 2382 |      1208 |   50.7 |    311 |
| original_accelerating_6    | yes      |  632 |       315 |   49.8 |    252 |
| original_accelerating_6    | no       | 1385 |       690 |   49.8 |    295 |
| original_accelerating_6    | unknown  |  365 |       203 |   55.6 |    163 |
| original_accelerating_6    | measured | 2017 |      1005 |   49.8 |    304 |
| original_accelerating_6    | baseline | 2382 |      1208 |   50.7 |    311 |
| midpoint_accelerating_6    | yes      |  678 |       341 |   50.3 |    258 |
| midpoint_accelerating_6    | no       | 1443 |       724 |   50.2 |    297 |
| midpoint_accelerating_6    | unknown  |  261 |       143 |   54.8 |    119 |
| midpoint_accelerating_6    | measured | 2121 |      1065 |   50.2 |    305 |
| midpoint_accelerating_6    | baseline | 2382 |      1208 |   50.7 |    311 |
| guarded_100_accelerating_6 | yes      |  388 |       204 |   52.6 |    184 |
| guarded_100_accelerating_6 | no       |  805 |       403 |   50.1 |    245 |
| guarded_100_accelerating_6 | unknown  | 1189 |       601 |   50.5 |    266 |
| guarded_100_accelerating_6 | measured | 1193 |       607 |   50.9 |    264 |
| guarded_100_accelerating_6 | baseline | 2382 |      1208 |   50.7 |    311 |

95% whole-date intervals; differences are percentage points. No multiple-comparison adjustment. No interval here proves that an N-expanding union has higher accuracy than thrust.

| rule                       |   low |   high |   delta_no_low |   delta_no_high |   delta_all_low |   delta_all_high |
|:---------------------------|------:|-------:|---------------:|----------------:|----------------:|-----------------:|
| original_falling_6         |  46.5 |   53.6 |           -2.3 |             7.7 |            -2.3 |              1.1 |
| original_accelerating_6    |  45.1 |   54.4 |           -4.9 |             4.9 |            -4.5 |              2.7 |
| midpoint_accelerating_6    |  45.6 |   54.7 |           -4.7 |             4.7 |            -3.8 |              2.9 |
| guarded_100_accelerating_6 |  46.7 |   58.3 |           -3.9 |             9.1 |            -3.0 |              7.0 |

## b07: yes, no, unknown and comparable coverage

| rule                             | state    |   n |   targets |   rate |   days |
|:---------------------------------|:---------|----:|----------:|-------:|-------:|
| original_accelerating_6          | yes      | 157 |        96 |   61.1 |    121 |
| original_accelerating_6          | no       | 539 |       254 |   47.1 |    242 |
| original_accelerating_6          | unknown  |  73 |        43 |   58.9 |     58 |
| original_accelerating_6          | measured | 696 |       350 |   50.3 |    267 |
| original_accelerating_6          | baseline | 769 |       393 |   51.1 |    283 |
| midpoint_accelerating_6          | yes      | 163 |       100 |   61.3 |    125 |
| midpoint_accelerating_6          | no       | 554 |       266 |   48.0 |    247 |
| midpoint_accelerating_6          | unknown  |  52 |        27 |   51.9 |     42 |
| midpoint_accelerating_6          | measured | 717 |       366 |   51.0 |    271 |
| midpoint_accelerating_6          | baseline | 769 |       393 |   51.1 |    283 |
| guarded_50_weighted_accelerating | yes      | 104 |        68 |   65.4 |     77 |
| guarded_50_weighted_accelerating | no       | 302 |       147 |   48.7 |    171 |
| guarded_50_weighted_accelerating | unknown  | 363 |       178 |   49.0 |    189 |
| guarded_50_weighted_accelerating | measured | 406 |       215 |   53.0 |    192 |
| guarded_50_weighted_accelerating | baseline | 769 |       393 |   51.1 |    283 |

95% whole-date intervals; differences are percentage points. No multiple-comparison adjustment. No interval here proves that an N-expanding union has higher accuracy than thrust.

| rule                             |   low |   high |   delta_no_low |   delta_no_high |   delta_all_low |   delta_all_high |
|:---------------------------------|------:|-------:|---------------:|----------------:|----------------:|-----------------:|
| original_accelerating_6          |  53.1 |   69.1 |            5.5 |            22.4 |             3.4 |             16.7 |
| midpoint_accelerating_6          |  53.5 |   69.1 |            5.0 |            21.5 |             3.8 |             16.6 |
| guarded_50_weighted_accelerating |  55.0 |   75.2 |            4.9 |            27.7 |             4.8 |             23.4 |

## b09: yes, no, unknown and comparable coverage

| rule                       | state    |    n |   targets |   rate |   days |
|:---------------------------|:---------|-----:|----------:|-------:|-------:|
| original_accelerating_8    | yes      |  213 |       123 |   57.7 |    127 |
| original_accelerating_8    | no       | 4959 |      2560 |   51.6 |    311 |
| original_accelerating_8    | unknown  |  388 |       207 |   53.4 |    205 |
| original_accelerating_8    | measured | 5172 |      2683 |   51.9 |    311 |
| original_accelerating_8    | baseline | 5560 |      2890 |   52.0 |    315 |
| midpoint_accelerating_8    | yes      |  240 |       141 |   58.8 |    135 |
| midpoint_accelerating_8    | no       | 5017 |      2584 |   51.5 |    311 |
| midpoint_accelerating_8    | unknown  |  303 |       165 |   54.5 |    186 |
| midpoint_accelerating_8    | measured | 5257 |      2725 |   51.8 |    311 |
| midpoint_accelerating_8    | baseline | 5560 |      2890 |   52.0 |    315 |
| guarded_100_accelerating_8 | yes      |  105 |        69 |   65.7 |     69 |
| guarded_100_accelerating_8 | no       | 3983 |      2040 |   51.2 |    301 |
| guarded_100_accelerating_8 | unknown  | 1472 |       781 |   53.1 |    281 |
| guarded_100_accelerating_8 | measured | 4088 |      2109 |   51.6 |    301 |
| guarded_100_accelerating_8 | baseline | 5560 |      2890 |   52.0 |    315 |
| guarded_50_accelerating_8  | yes      |   66 |        44 |   66.7 |     39 |
| guarded_50_accelerating_8  | no       | 2758 |      1367 |   49.6 |    273 |
| guarded_50_accelerating_8  | unknown  | 2736 |      1479 |   54.1 |    297 |
| guarded_50_accelerating_8  | measured | 2824 |      1411 |   50.0 |    273 |
| guarded_50_accelerating_8  | baseline | 5560 |      2890 |   52.0 |    315 |

95% whole-date intervals; differences are percentage points. No multiple-comparison adjustment. No interval here proves that an N-expanding union has higher accuracy than thrust.

| rule                       |   low |   high |   delta_no_low |   delta_no_high |   delta_all_low |   delta_all_high |
|:---------------------------|------:|-------:|---------------:|----------------:|----------------:|-----------------:|
| original_accelerating_8    |  49.3 |   65.6 |           -1.6 |            13.7 |            -1.7 |             13.2 |
| midpoint_accelerating_8    |  51.0 |   65.8 |            0.1 |            14.2 |            -0.1 |             13.4 |
| guarded_100_accelerating_8 |  54.0 |   75.9 |            3.3 |            24.5 |             2.6 |             23.7 |
| guarded_50_accelerating_8  |  51.5 |   78.9 |            2.7 |            29.4 |             0.0 |             26.9 |

## b10_breakout: yes, no, unknown and comparable coverage

| rule                       | state    |   n |   targets |   rate |   days |
|:---------------------------|:---------|----:|----------:|-------:|-------:|
| original_accelerating_6    | yes      |  30 |        20 |   66.7 |     30 |
| original_accelerating_6    | no       |  70 |        38 |   54.3 |     70 |
| original_accelerating_6    | unknown  | 160 |        87 |   54.4 |    160 |
| original_accelerating_6    | measured | 100 |        58 |   58.0 |    100 |
| original_accelerating_6    | baseline | 260 |       145 |   55.8 |    260 |
| midpoint_accelerating_6    | yes      |  34 |        23 |   67.6 |     34 |
| midpoint_accelerating_6    | no       |  77 |        43 |   55.8 |     77 |
| midpoint_accelerating_6    | unknown  | 149 |        79 |   53.0 |    149 |
| midpoint_accelerating_6    | measured | 111 |        66 |   59.5 |    111 |
| midpoint_accelerating_6    | baseline | 260 |       145 |   55.8 |    260 |
| guarded_100_accelerating_6 | yes      |  17 |        13 |   76.5 |     17 |
| guarded_100_accelerating_6 | no       |  32 |        16 |   50.0 |     32 |
| guarded_100_accelerating_6 | unknown  | 211 |       116 |   55.0 |    211 |
| guarded_100_accelerating_6 | measured |  49 |        29 |   59.2 |     49 |
| guarded_100_accelerating_6 | baseline | 260 |       145 |   55.8 |    260 |

95% whole-date intervals; differences are percentage points. No multiple-comparison adjustment. No interval here proves that an N-expanding union has higher accuracy than thrust.

| rule                       |   low |   high |   delta_no_low |   delta_no_high |   delta_all_low |   delta_all_high |
|:---------------------------|------:|-------:|---------------:|----------------:|----------------:|-----------------:|
| original_accelerating_6    |  50.0 |   83.3 |           -8.8 |            32.5 |            -6.2 |             26.4 |
| midpoint_accelerating_6    |  51.4 |   82.9 |           -8.0 |            30.6 |            -3.9 |             26.4 |
| guarded_100_accelerating_6 |  53.8 |   94.7 |           -1.1 |            52.4 |            -0.5 |             39.8 |

## Evaluated rules with no qualifying entries

All four quote_resolved falling/acceleration rules (six/eight sectors) had zero qualifying entries. Their NaN success percentages mean N=0 after an evaluated condition; this is not a failed data download. The conservative quote-envelope rule did not resolve a broad sign in these observations. This is not a proof that it could never qualify on any possible future data.

## Execution and identity notes

The main per-family headline tables use all entries, where retained winners are a literal subset. For first/spaced modes, the retention columns count shared winning date/minute identities; filtering can replace the chosen minute. They do not count a differently timed successful trade as retained.

Use matched_pairs_canonical.parquet and canonical_pair_id for future joins. Original pair_id restarts within each rule/scope/stratum; the current analysis already uses those groups and joins outcomes by event identity. All 3,524 canonical pair identifiers are unique.

Fifty validated reused issuer bodies have no recorded HTTP status. issuer_http_provenance.csv preserves that distinction; parse validation still governs all accepted weights. All 421 as-of dates are strictly prior.
