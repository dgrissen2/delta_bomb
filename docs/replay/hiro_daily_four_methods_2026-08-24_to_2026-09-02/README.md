# Four-method HIRO single-name scan through 2026-09-02

> Historical four-method artifact. The active screened inventory is the [Pandar-approved two-method master](../hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/README.md); this file remains unchanged below for point-in-time reproducibility.

## Outcome

The authenticated SpotGamma HIRO universe contained **398 tickers**. After excluding indices/funds and enforcing the frozen liquidity gates, the scan produced **822 surface-qualified method/date rows across 167 current tickers**. Exact historical chains confirmed **80 rows**, yielding **31 method/ticker finalists across 30 unique stocks**.

The HIRO follow-through inventory is the union of the prior capture and the current surface set: **183 tickers total**, with **179 eligible for a completed next-session window through September 2**. Pending September 2 identifications: **MDB, PDD, PFE, QBTS**.

The serial authenticated capture completed **179/179 eligible tickers**: **650 available ticker-sessions**, **282 explicitly unavailable ticker-sessions**, and **18,230,251 provider rows**.

## Frozen method definitions

| Canonical name | Path | Surface/regime gate | Exact implementation |
|---|---|---|---|
| buy-first call puke | Buy complete spread first | RR rank ≥60, call-skew rank ≤40, IV Rank ≤65, drawdown ≤-8%, 5d return <0 | Buy complete 20–35%-OTM, 30–90 DTE call spread for $0.05–$0.50; scale out into rebound |
| buy-first call standard | Buy long call first | Good/Better/Best call-cheap surface plus constructive technical/relative-strength overlay | Buy ~15-delta 30–60 DTE call; rest adjacent upper-call sale into strength |
| sell-first call grab | Sell far call first | Call-wing rank ≥85, kink ≥70, RR rank ≤10, positive 5d return, near 20d high, IV Rank 30–70, no near earnings | Sell 2–6-delta 5–19 DTE call; rest nearer-call buy; breakout stop mandatory |
| buy-first put-tail inventory | Buy complete put spread first | IV Rank ≤35, RR rank ≤50, put-skew rank ≤25 | Buy complete current/next-monthly spread 25–45% OTM, roughly $5 wide, for ≤$0.10; hold as inventory and rest scale-out offers |

## Daily surface rows / exact-chain confirmations

Each cell is `surface-qualified / exact-chain-confirmed`. Call methods begin August 28; put-tail inventory gets the requested extra week beginning August 24.

| Date | Call puke | Call standard | Call grab | Put inventory |
|---|---|---|---|---|
| 2026-08-24 | 0/0 | 0/0 | 0/0 | 89/7 |
| 2026-08-25 | 0/0 | 0/0 | 0/0 | 92/8 |
| 2026-08-26 | 0/0 | 0/0 | 0/0 | 102/7 |
| 2026-08-27 | 0/0 | 0/0 | 0/0 | 92/7 |
| 2026-08-28 | 6/2 | 4/0 | 1/0 | 107/7 |
| 2026-08-31 | 3/1 | 0/0 | 1/1 | 110/12 |
| 2026-09-01 | 6/5 | 3/1 | 0/0 | 96/6 |
| 2026-09-02 | 7/4 | 4/1 | 0/0 | 99/11 |

## Exact-chain finalists

| Date | Ticker | Method | RR rank | IV rank | Why | Exact strategy |
|---|---|---|---|---|---|---|
| 2026-08-28 | RGTI | buy-first call puke | 79.0 | 0.0 | RR 79.0≥60; call-skew 13.5≤40; IV 0.0≤65; drawdown -17.9%; 5d -13.6%. | BTO 10-16 20/25C complete spread at ≤$0.38 |
| 2026-08-31 | RDW | buy-first call puke | 92.5 | 11.9 | RR 92.5≥60; call-skew 6.0≤40; IV 11.9≤65; drawdown -22.2%; 5d -6.9%. | BTO 10-16 14/19C complete spread at ≤$0.35 |
| 2026-09-01 | NOK | buy-first call puke | 61.1 | 37.4 | RR 61.1≥60; call-skew 26.2≤40; IV 37.4≤65; drawdown -8.4%; 5d -3.6%. | BTO 10-16 13/18C complete spread at ≤$0.12 |
| 2026-09-01 | SOUN | buy-first call puke | 71.0 | 2.2 | RR 71.0≥60; call-skew 13.1≤40; IV 2.2≤65; drawdown -14.3%; 5d -1.0%. | BTO 10-16 9/14C complete spread at ≤$0.13 |
| 2026-09-01 | U | buy-first call puke | 74.2 | 4.6 | RR 74.2≥60; call-skew 15.5≤40; IV 4.6≤65; drawdown -12.8%; 5d -9.4%. | BTO 10-16 55/60C complete spread at ≤$0.24 |
| 2026-09-02 | LUNR | buy-first call puke | 76.2 | 31.3 | RR 76.2≥60; call-skew 19.4≤40; IV 31.3≤65; drawdown -26.7%; 5d -7.0%. | BTO 10-16 20/25C complete spread at ≤$0.36 |
| 2026-09-02 | QBTS | buy-first call puke | 61.5 | 0.0 | RR 61.5≥60; call-skew 29.4≤40; IV 0.0≤65; drawdown -21.8%; 5d -5.2%. | BTO 10-16 22/27C complete spread at ≤$0.28 |
| 2026-09-01 | CVS | buy-first call standard | 60.3 | 15.9 | Good call-cheap surface: RR 60.3, call-skew 15.9, IV 15.9; 63d relative return 13.6%. | BTO 10-16 110C at ≤$0.55; rest STO 115C into strength |
| 2026-09-02 | U | buy-first call standard | 60.3 | 5.1 | Good call-cheap surface: RR 60.3, call-skew 24.2, IV 5.1; 63d relative return 43.6%. | BTO 10-16 50C at ≤$0.62; rest STO 55C into strength |
| 2026-08-31 | MSTR | sell-first call grab | 3.6 | 40.3 | RR 3.6≤10; call-wing 86.1≥85; kink 73.8≥70; IV 40.3; 5d 8.4%. | STO 09-04 160C at ≥$0.23; rest BTO 157.5C at $0.13 |
| 2026-08-24 | CCJ | buy-first put-tail inventory | 21.4 | 30.0 | IV 30.0≤35; RR 21.4≤50; put-skew 19.0≤25; executable far-tail spread. | BTO 09-18 75/70P complete spread at ≤$0.05 |
| 2026-08-24 | TGT | buy-first put-tail inventory | 17.5 | 14.9 | IV 14.9≤35; RR 17.5≤50; put-skew 13.1≤25; executable far-tail spread. | BTO 09-18 125/120P complete spread at ≤$0.02 |
| 2026-08-25 | SCHW | buy-first put-tail inventory | 8.3 | 22.1 | IV 22.1≤35; RR 8.3≤50; put-skew 8.7≤25; executable far-tail spread. | BTO 09-18 77.5/75P complete spread at ≤$0.07 |
| 2026-08-26 | IREN | buy-first put-tail inventory | 13.9 | 0.0 | IV 0.0≤35; RR 13.9≤50; put-skew 12.3≤25; executable far-tail spread. | BTO 09-18 24/19P complete spread at ≤$0.10 |
| 2026-08-26 | MRNA | buy-first put-tail inventory | 12.7 | 24.1 | IV 24.1≤35; RR 12.7≤50; put-skew 11.5≤25; executable far-tail spread. | BTO 09-18 90/85P complete spread at ≤$0.09 |
| 2026-08-27 | GOOG | buy-first put-tail inventory | 11.1 | 13.0 | IV 13.0≤35; RR 11.1≤50; put-skew 9.5≤25; executable far-tail spread. | BTO 10-16 230/225P complete spread at ≤$0.06 |
| 2026-08-27 | GOOGL | buy-first put-tail inventory | 6.3 | 12.4 | IV 12.4≤35; RR 6.3≤50; put-skew 3.6≤25; executable far-tail spread. | BTO 10-16 245/240P complete spread at ≤$0.07 |
| 2026-08-27 | NBIS | buy-first put-tail inventory | 21.4 | 24.1 | IV 24.1≤35; RR 21.4≤50; put-skew 15.5≤25; executable far-tail spread. | BTO 09-18 120/115P complete spread at ≤$0.06 |
| 2026-08-28 | CVNA | buy-first put-tail inventory | 4.4 | 23.1 | IV 23.1≤35; RR 4.4≤50; put-skew 4.8≤25; executable far-tail spread. | BTO 09-18 45/40P complete spread at ≤$0.05 |
| 2026-08-28 | HOOD | buy-first put-tail inventory | 12.7 | 28.6 | IV 28.6≤35; RR 12.7≤50; put-skew 9.5≤25; executable far-tail spread. | BTO 09-18 70/65P complete spread at ≤$0.07 |
| 2026-08-31 | BE | buy-first put-tail inventory | 11.1 | 0.0 | IV 0.0≤35; RR 11.1≤50; put-skew 11.5≤25; executable far-tail spread. | BTO 09-18 120/115P complete spread at ≤$0.08 |
| 2026-08-31 | CRWV | buy-first put-tail inventory | 1.6 | 0.9 | IV 0.9≤35; RR 1.6≤50; put-skew 3.2≤25; executable far-tail spread. | BTO 09-18 62.5/60P complete spread at ≤$0.07 |
| 2026-08-31 | NVDA | buy-first put-tail inventory | 18.3 | 0.7 | IV 0.7≤35; RR 18.3≤50; put-skew 16.3≤25; executable far-tail spread. | BTO 09-18 130/125P complete spread at ≤$0.01 |
| 2026-08-31 | OKLO | buy-first put-tail inventory | 28.6 | 0.0 | IV 0.0≤35; RR 28.6≤50; put-skew 25.0≤25; executable far-tail spread. | BTO 09-18 30/25P complete spread at ≤$0.10 |
| 2026-08-31 | PLTR | buy-first put-tail inventory | 25.4 | 13.7 | IV 13.7≤35; RR 25.4≤50; put-skew 22.2≤25; executable far-tail spread. | BTO 09-18 105/100P complete spread at ≤$0.03 |
| 2026-08-31 | SHOP | buy-first put-tail inventory | 17.1 | 13.7 | IV 13.7≤35; RR 17.1≤50; put-skew 17.9≤25; executable far-tail spread. | BTO 09-18 95/90P complete spread at ≤$0.03 |
| 2026-09-02 | AMZN | buy-first put-tail inventory | 12.7 | 29.6 | IV 29.6≤35; RR 12.7≤50; put-skew 10.3≤25; executable far-tail spread. | BTO 09-18 190/185P complete spread at ≤$0.02 |
| 2026-09-02 | ANET | buy-first put-tail inventory | 17.9 | 26.1 | IV 26.1≤35; RR 17.9≤50; put-skew 9.9≤25; executable far-tail spread. | BTO 09-18 130/125P complete spread at ≤$0.04 |
| 2026-09-02 | BMNR | buy-first put-tail inventory | 25.8 | 5.3 | IV 5.3≤35; RR 25.8≤50; put-skew 21.4≤25; executable far-tail spread. | BTO 09-18 16/11P complete spread at ≤$0.05 |
| 2026-09-02 | MRVL | buy-first put-tail inventory | 13.9 | 22.5 | IV 22.5≤35; RR 13.9≤50; put-skew 15.5≤25; executable far-tail spread. | BTO 09-18 120/115P complete spread at ≤$0.02 |
| 2026-09-02 | SOFI | buy-first put-tail inventory | 34.1 | 9.5 | IV 9.5≤35; RR 34.1≤50; put-skew 25.0≤25; executable far-tail spread. | BTO 10-16 12/9P complete spread at ≤$0.04 |

## Audit notes

- ORATS ledger: **260 / 500** attempts used. Failed sandbox-only connection attempts remain counted.
- The primary chain query covered call delta 0.005–0.995. A separately cached 0.995–0.99999 gap fill was required to avoid falsely rejecting ultra-far puts.
- Put-tail earnings are annotated, not rejected: this is persistent hedge inventory, not an earnings-timing setup.
- All/Next Expiry/Retail HIRO groups are preserved separately and must not be summed because they overlap.
- Missing provider sessions are unavailable, not zero flow.
- HIRO universe SHA-256: `30c95d3307e3557bf6be88f9870976e50322edb5df113b4a02a4eb778db40a86`.

## Artifacts

- `single_name_call_screen_candidates.csv`: all surface-qualified method/date rows.
- `single_name_call_screen_chain_checks.csv`: every exact-chain selection and rejection reason.
- `single_name_call_screen_finalists.csv`: one best confirmed date per method/ticker.
- `single_name_call_screen_all.parquet`: complete eligible ticker/day feature table.
- `hiro_inventory_windows.csv`: serial-capture windows for prior-plus-current inventory.
- `hiro_inventory_pending.csv`: identifiers with no completed post-signal session yet.
- `hiro_ticker_followthrough_to_2026-09-02/summary.csv`: compact committed capture coverage.
- `hiro_ticker_followthrough_to_2026-09-02/CAPTURE_NOTES.md`: retention, integrity, and reproduction notes.
- `hiro_tickers_2026-09-03.csv`: refreshed authenticated HIRO membership snapshot.
