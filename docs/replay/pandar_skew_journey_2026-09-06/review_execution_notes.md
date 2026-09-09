**Read “within 4–5 days” here as trading sessions, with the sale session counted as
day 1.** The CSV also records elapsed calendar days and whether expiry shortened the
window. Thus MSTR's day-4/day-5 exits are August 26/27 after an August 21 sale: five/six
elapsed calendar days. This does not answer a different four/five-calendar-day rule.
TSLA's September 3 entry would reach session 4 on September 9, its expiry; September 7
is a holiday. Both requested horizons are therefore outside the September 4 data cutoff.

The replay attempted a sale at just **10:01 ET on the next trading day** and required
at least **$0.20 per share, or $20 per standard contract**. NVDA, BE, SMCI and JNJ offered
$0.15, $0.05, $0.15 and $0.04 respectively at that minute, so no simulated position was
opened for those four examples. The timing and $0.20 cutoff are project assumptions
for this comparison, not Pandar requirements. A sale on the signal day or at another
minute could have a different result; this comparison did not test those alternatives.
COIN (August 20), STX and MSTR completed their second leg on the entry day; COIN
(August 21) and MRNA did so on the next session. TSLA also completed on the next
session but lacks a mature closing outcome. No entry or second-leg time was chosen
after comparing profitable alternatives.

**Buying the nearer call cost more than it added at the common exit in all five mature
completions.** The comparison holds the original short sale and exit deadline fixed:

| Signal | Conversion net, D4 / D5 | Simply cover the short, D4 / D5 |
| --- | --- | --- |
| COIN 08-20 | +$11.40 / +$6.40 | +$194.70 / +$188.70 |
| COIN 08-21 | +$9.40 / +$10.40, zero-bid-long marks | +$17.70 / +$18.70 |
| STX 08-24 | +$2.40 / +$2.40, zero-bid-long marks | +$203.70 / +$203.70 |
| MSTR 08-20 | +$10.40 / +$36.40 | +$65.70 / +$42.70 |
| MRNA 08-24 | +$30.40 / +$30.40, zero-bid-long marks | +$60.70 / +$60.70 |

Covering the short at the same late deadline leaves more upside exposure during the
intervening period than completing the spread earlier. The P&L advantage is not a
risk-adjusted dominance claim or a recommendation to remain short without protection.

COIN 08-21, STX and MRNA had no executable long-call bid at the closing reference. The
calculation covers their short at the ask, values the remaining long at zero and
reserves all four fees. It is a conservative marked result, **not proof that both legs
were sold/bought to close**. An extra one cent of adverse slippage on each action turns
STX's +$2.40 mark into **−$1.60**. The two fully quoted closing examples remain positive
under that sensitivity. A one-minute NBBO snapshot is still a hypothetical fill, not
an executed order; it does not capture every intraminute price or quote-age risk.

The new replay uses **18 ThetaData contract-history requests plus two existing cached
histories**, with no missing nearer-call minute rows in the admitted windows. Invalid
quotes (including empty opening snapshots) were not executable and could not trigger
a purchase. The [20-row ledger](review_45_session_replay.csv) keeps both horizons for
every example, including rejected entries and censored deadlines. Each horizon is a
separate counterfactual; the same position cannot be closed twice. These selected
examples do not establish a win rate, and none is earnings-cleared under the new rule.
