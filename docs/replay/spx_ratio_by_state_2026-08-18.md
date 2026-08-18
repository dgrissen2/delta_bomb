# Additional cut (2026-08-18): round-trip vs adverse ratio by state — SPX 1-min, 12,225 starts / 815 days, 15-min starts 10:30–14:00, X = 4 bp, 60-min window
| state | P(round trip) | P(adverse>20bp) | ratio | P(adverse>40bp) |
| prior-hour range in IM: <0.29 / 0.29–0.41 / 0.41–0.58 / >0.58 | 0.47 / 0.53 / 0.58 / 0.65 | 0.12 / 0.14 / 0.16 / 0.18 | 3.9 / 3.8 / 3.7 / 3.6 | 0.034 / 0.038 / 0.040 / 0.065 |
| SG index terciles: <0.23 / 0.23–1.54 / >1.54 | 0.60 / 0.57 / 0.49 | 0.175 / 0.145 / 0.124 | 3.4 / 3.9 / 3.9 | 0.064 / 0.041 / 0.026 |
| open vs VT (IM): <0.07 / 0.07–0.63 / 0.63–1.34 / >1.34 | 0.60 / 0.56 / 0.53 / 0.54 | 0.167 / 0.134 / 0.152 / 0.144 | 3.6 / 4.15 / 3.5 / 3.7 | 0.056 / 0.038 / 0.042 / 0.041 |
| hour 10 / 11 / 12 / 13 / 14 | 0.61 / 0.58 / 0.54 / 0.53 / 0.53 | 0.169 / 0.148 / 0.141 / 0.147 / 0.160 | 3.6 / 3.9 / 3.85 / 3.6 / 3.3 | 0.057 / 0.040 / 0.040 / 0.044 / 0.054 |
| hour × range tercile (quiet/mid/busy): P(round trip) 0.48–0.50 / 0.50–0.61 / 0.62–0.65; P(adv>20) 0.10–0.13 / 0.145–0.185 / 0.16–0.19 |
Read: the 15-pt ratio is ~3.3–4.2 in every state; the 30-pt tail is where states separate (SG index >1.5: 0.026 vs <0.23: 0.064; quiet vs busy 0.034 vs 0.065).
Prior VT study (vt_breakdown_recovery, 104 VT-loss days): depth below VT at 10:30 predicts recovery ρ −0.60; reclaimed-by-10:30 days recover +0.33 IM median; put-skew steepening into the flush ρ +0.51; ATM IV above its 09:35 value ρ −0.37.
spy_chaser trend work: OOF AUC 0.52–0.61 at 09:35–09:45, 0.78–0.86 by noon; ride/trailing rules ≈0 net (10–12 pt pullbacks ≈ 2.5u whipsaw); alligator entries at 60% of range with 33 bp left, −2% capture; chop brief: pre-entry ER(10) ρ≈0, ≥6 flips best mean; touch/revert on 5-min: median revert 6.8 pt vs breach 7.1 pt (no tell), 2 pokes/day, first touches pre-2pm whip (median 4 episodes, 25% commit), 25–34% of first touches in the last hour.
