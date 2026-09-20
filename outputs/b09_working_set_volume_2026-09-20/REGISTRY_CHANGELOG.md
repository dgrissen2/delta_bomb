
## 2026-09-20 — derive — fixed SPY volume across five current Branch B cohorts

- **operator:** Codex, user-authorized cached-data volume extension after findings/memory consolidation and push
- **namespace:** `/Users/dgrissen/Dev/central_trade_data/thetadata/b09_working_set_volume_2026-09-20-v1`
- **project:** `/Users/dgrissen/Dev/delta_bomb/outputs/b09_working_set_volume_2026-09-20`
- **scope:** five fixed cohorts, 685 unique combined entries, 239 selected 2025–September 18, 2026 research dates; no spacing, causal above VT, native +5 before entry−10 within 60 bars
- **feature:** preceding five completed SPY minutes / same-clock median of exactly 60 prior source sessions; fixed RVOL>1; XNAS.ITCH Nasdaq-venue volume
- **changes:** 685 feature rows and joined outcomes; 125 summaries; coverage/context/block tables; 1,195 whole-date deletions; 93 exact unknown-entry rows
- **coverage:** 592 usable, 52 current-unavailable after June 11 cache end, 41 incomplete-history; no measured 2026 H2
- **results:** combined high 173/274=63.1%, ordinary 198/318=62.3%; difference +0.87 pp, 95% date-cluster CI −8.08 to +9.52; 198 observed winners excluded by a high-only gate; no gate adopted
- **verification:** 501 prior feature timestamps match exactly; independent direct raw five-bar checks for all 685 entries; 685 native SPX/VT paths (41,100 bar observations); 125 scalar summary and 1,195 deletion recounts; existing causal RVOL boundary test and Ruff
- **calls:** ThetaData 0; ORATS 0; Databento 0; other providers 0; no independent reviewer agents
- **dictionary_reconciled:** true; namespace dictionary, freeze and analysis/verification receipts define units, coverage, clocks, bootstrap and provenance
- **limits:** reused selected history, overlapping cohorts, prior searches, between-day dependence, incomplete 2026 coverage; no hard-gate benefit established
- **reversibility:** additive derived namespace and registry append; no raw/source changes; unrelated concurrent work preserved
