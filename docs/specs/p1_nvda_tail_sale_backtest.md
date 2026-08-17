# Spec — P1 "Tail-sale with buyback" backtest, NVDA, 2023 → present

Version **0.2** · 2026-08-17 · owner: delta_bomb · status: for annotation
(v0.1 + Charlie review §14 + Codex panel §16 dispositions applied; change log in §17)

## 0. What this is and what decision it informs

P1 is a **mechanised variant of the tail-sale-with-buyback book reconstructed from PandarBear's PMTraders thread**
(`docs/sources/discord_transcript_clean.txt`; report §5f). The white paper is *not* the source for P1 — it describes an
SPX intraday legging device. What is being tested:

> When the far wing of NVDA's front expiry is unusually rich, sell one far-OTM option there, sized at book level to be
> held to expiry. Rest a buy on the strike one notch nearer at (sale − c). If it fills, keep the premium difference and
> hold the resulting long vertical carried at a credit; if it never fills, hold the short to expiry.

Decision informed (CIO memo, report §10): **promote to paper-trading, hold research-only, or stop — decided
separately per side (put/call) and per archetype (grab / post-shock smile), never on the combined book.**
Out of scope: SPX legging, P2 penny-spread inventory, the report's §5e 15Δ buy-first structure, portfolio-margin
optimisation, exit-timing optimisation.

## 1. Universe, window, timing

- Underlying: **NVDA only.**
- Signal history: ORATS daily surface 2018-01-02 → 2026-08-14. Thresholds are pre-registered (§8) and checked on
  2018–2022 (surface only). Trades simulated **2023-01-03 → 2026-08-14** (option-quote history starts 2023).
- **Timing (no look-ahead):** the signal is computed from the ORATS close of session *t*; the trade is entered at the
  **open of session t+1** (EOD proxy: t+1 opening bid; where 1-min data exist, the 09:31 NBBO). All buyback checks and
  marks start at t+1.
- **Split (2024-06-10, 10:1):** all results in **constant share exposure** — the unit is 100 post-split shares. One
  pre-split contract = 10 units; pre-split strikes/premiums ÷ 10; fees charged per executed *leg per unit*. ORATS
  `clsPx` is already split-adjusted; ThetaData quotes are as-traded and normalised in the loader.

## 2. Data

| Need | Source (`~/Dev/central_trade_data`) | Notes |
|---|---|---|
| Daily surface (screen) | `orats/delta_bomb_refresh_2026-08-17/NVDA_cores.parquet`, `NVDA_ivrank.parquet`, `NVDA_dailies.parquet` | corrupt tick 2025-04-04 (`iv30d`=381) filtered |
| Earnings dates | `orats/earnings/earnings_long.parquet` (`ticker==NVDA`) | exclusion rule §5 |
| Option EOD quotes + greeks (entry, buyback, marks, contract-level confirmation) | **to acquire:** ThetaData `option/history/eod` **and** `option/history/greeks/eod` for NVDA, every expiration with 1–35 DTE, 2023-01-03 → 2026-08-14 (open/high/low/close trade, close bid/ask, delta, IV; all strikes/rights); one call per (endpoint, expiration) ≈ 380 calls | store `thetadata/nvda_p1_eod_2026-08-17-v1/{eod,greeks}/NVDA_<exp>.parquet` + manifest; dictionary + changelog entries |
| Intraday fill truth-check | existing `thetadata/nvda_delta_bomb_1m_2026-08-17-v1/greeks/` (73 sessions, 2026-05-04 → 08-14; 171 expiry-session files) **plus to acquire:** 1-min greeks for the **10 largest 2023–2025 tail episodes** (~30 sessions, front expiry) | §7 |
| Known Pandar callouts (fidelity set) | transcript dates: 2024-12-19, 2024-12-20 (SMH), 2025-01-27, 2025-01-31 (calls), 2025-02-07, 2025-02-21, 2025-03-27 (1-DTE), 2025-05-15, 2025-05-20 (calls) | §9.0 |

ORATS fields: `iv10d`, `dlt5Iv10d` (5Δ **call**), `dlt95Iv10d` (5Δ put), `dlt5Iv30d`, `dlt95Iv30d`, `iv30d`,
`exErnIv30d`, `exErnDlt25Iv30d`, `exErnDlt75Iv30d`, `ivRank1y`, `clsPx`. Convention: `dltXX` = IV at XX call delta.

## 3. Definitions

```
call_wing_10 = dlt5Iv10d  - iv10d          put_wing_10 = dlt95Iv10d - iv10d
call_kink    = dlt5Iv10d  - dlt5Iv30d      put_kink    = dlt95Iv10d - dlt95Iv30d
RR25         = exErnDlt75Iv30d - exErnDlt25Iv30d      (25Δ put IV − 25Δ call IV; high = puts rich vs calls)
pct252(x)    = share of the prior 252 sessions with x below today's value ×100 (min 126 obs)
episode      = a run of signal days on one side separated by < 5 sessions (unit for clustering, §8/§9)
```

## 4. Trigger (at close of *t*, per side), with archetype tag

**Screen (ORATS):**
- Sell-put candidate: `pct252(put_wing_10) ≥ P_thr` and `pct252(put_kink) ≥ K_thr`.
- Sell-call candidate: `pct252(call_wing_10) ≥ P_thr` and `pct252(call_kink) ≥ K_thr`.
- Pre-registered `P_thr = 85`, `K_thr = 70` (§8).

**Contract-level confirmation (ThetaData EOD greeks, same close):** the *selected* option's IV minus the same-expiry
ATM IV must be ≥ its own 252-session 85th percentile (computed on the EOD store for that DTE band). No confirmation →
no trade (logged as "screen-only").

**Archetype tag (stored, drives the split):**
- **(a) grab** — one-sided: that side's wing ≥ P_thr, the *other* wing's pct < 70, that side of RR extreme
  (calls: `pct252(RR25) ≤ 10`; puts: `≥ 90`), and spot moved that way over the prior 5 sessions.
- **(b) post-shock smile** — both wings ≥ P_thr and `pct252(iv10d) ≥ 80`.
- **(c) other** — fires the screen but neither (a) nor (b). Reported, not promoted.

**Cool-down:** at most one *unpaired* short per side per expiry. A completed spread does **not** block a new sale on
that side/expiry (inventory building). Variant "single-cycle" (one trade per side per expiry, full stop) also run.

**Regime tags stored:** `ivRank1y`, `pct252(RR25)`, `clsPx` vs 50-day SMA, drawdown from 20-day high.

## 5. Instrument

- Expiry: nearest listed with **5 ≤ DTE ≤ 12** at *t+1*; if none, nearest ≤ 19. **Skip** if an NVDA `earnDate` falls
  in [t+1, expiry]; on the call side also skip if t+1 is the session before a print.
- Strike: the far option on the signalled side whose EOD **|Δ| is nearest 0.04** (must be in [0.02, 0.06]) — one rule,
  no moneyness fallback; **skip if greeks are missing**. Require **bid ≥ 0.20** and ask − bid ≤ 0.10 at entry.
  Record %OTM, Δ, IV, dollar premium.
- Buyback strike: **one listed strike nearer** the money. Record realised width (2.5 / 5 / other) and report per width;
  the headline uses width-normalised P&L (P&L ÷ width × 5).
- Sensitivity (§8): moneyness rule 25–40% OTM; |Δ| 0.03 / 0.06; DTE 8–19.

## 6. Entry, buyback, exits, counterfactuals

- **Entry (t+1 open):** STO 1 unit at the bid. Fees: $0.65 per executed leg per unit (ToS) and $0.00, both reported.
- **Resting buyback, live from the same minute:** BTO 1 unit of the nearer strike, limit `L = sale − c`,
  `c = min(0.10, 0.5 × sale)` (baseline; `c = min(0.05, …)` in the grid). L ≥ 0.10 by the bid ≥ 0.20 rule.
- **Fill test:** primary = first session ≥ t+1 whose EOD **low trade ≤ L** (fill at L); bound = close ask ≤ L. Both
  P&Ls reported; the decision must hold under both. Assumption stated: 1 unit fills if touched.
- **After a fill:** book = long nearer / short farther, carried at credit `sale − L`. Baseline holds to expiry.
  Record daily bid-side value (sell nearer at bid, buy farther at ask), its max, first session ≥ 1.00 / 2.00 / 3.00
  (scale-out variant: sell at 2.00; reported, not optimised).
- **Same-time buy-to-close comparator (mandatory):** at the fill session, also record the far short's own ask. Report
  cash retained by *closing the short* vs *buying the nearer strike*; the difference is the cost of keeping the vertical,
  set against the vertical's later payoff.
- **If never filled:** hold to expiry; daily mark at ask; terminal = intrinsic on `clsPx` at expiry (physical delivery
  and pin/after-hours risk noted as unmodelled).
- **Breakout stop (named variant, Charlie #4):** after entry, if that side's wing pct has *risen* vs entry and spot has
  moved ≥ 5% toward the strike at a close → BTC the short (or BTO one strike farther = synthetic spread) and stop.
  Report with/without; the difference = the price of the tell.
- **Counterfactuals (mandatory, same dates/instrument):** (i) naked-to-expiry, no buyback; (ii) immediate vertical at
  entry (sell far, buy nearer at the same open); (iii) **unconditional**: same instrument sold on *every* eligible
  session; (iv) matched non-signal sessions (same DTE/Δ, nearest non-signal day). Edge of the screen = P1 − (iii);
  value of the buyback = P1 − (i) and P1 − same-time BTC.

## 7. Fill truth-check

Recompute every buyback (and entry) fill with 1-min NBBO wherever the 1-min store covers the trade — the 2026 window
plus the acquired 2023–25 episode set — and report **per regime**: share of trades whose fill status differs
(naked ↔ spread), days-to-fill, P&L difference. Not a scalar caveat: the promotion decision (§9) is evaluated under
the primary EOD rule, the conservative EOD rule, and, where available, the 1-min truth; all three must agree on sign
per side × archetype.

## 8. Thresholds and sensitivity

- `P_thr = 85`, `K_thr = 70`, `c = min(0.10, 0.5×sale)`, |Δ| 0.04, DTE 5–12 are **pre-registered** as the primary
  hypothesis (from report §8b/8c). They are checked, not fitted, on 2018–2022 (surface only): report signal counts and
  ex-post 5-session P&L of a synthetic 4Δ short (from the surface) per episode; if the pre-registered pair is not in
  the top quartile of the grid there, say so — do not move it.
- Sensitivity grid (test window, reported only): `P_thr ∈ {75, 85, 90}`, `K_thr ∈ {50, 70, 85}`, `c ∈ {0.05, 0.10}`
  caps, |Δ| ∈ {0.03, 0.04, 0.06}, DTE ∈ {5–12, 8–19}, moneyness rule, fees on/off. **Observations are episodes**, not
  days.

## 9. Metrics and pass criteria (per side × archetype; combined book reported, never used to pass)

**9.0 Fidelity set:** does the trigger fire on the known Pandar callout dates (§2)? Report hits/misses with the
surface values that day. Misses are findings, not failures.

Metrics: signals/month, trades/month after exclusions; fill rate within 5 sessions (both fill rules); premium
collected; unfilled trades — count, days held, terminal, worst, MTM path; P&L per unit — mean, median, worst month,
worst rolling-12; hit rate; free-spread payoff (ITM count and size; max bid-side value distribution) *and* the
same-time BTC comparator; counterfactuals (i)–(iv); breakout-stop delta; regime split (2023 trend / 2024-H1 grind /
2024-H2–2025 chop incl. 2024-08-05, 2025-01-27, Apr-2025 / 2026 grind + May blow-off); fees on/off.

**Portfolio-level (enters pass/fail):** concurrent positions on both sides across expiries; book **gap stress**:
overnight ±15% and ±25% through strikes on the whole book at each session; expected shortfall (5%) of monthly P&L;
margin proxy = broker-style naked-option requirement summed across the book; **forced-liquidation flag** if margin
> 80% of a $250k / $1M NLV. Sizing rule restated at book level: units chosen so the ±25% gap loss on the whole
book ≤ 10% NLV.

**Pass (→ paper-trading), per side × archetype:** (i) mean P&L per unit > 0 with an episode-level block-bootstrap
90% CI excluding 0; (ii) ES(5%) of monthly P&L ≤ 1.5 × median monthly income; (iii) sign agrees under both EOD fill
rules and the 1-min truth-check where available; (iv) survives leave-one-shock-out (each of the three shocks removed);
(v) book gap stress never trips the forced-liquidation flag at the stated size; (vi) P1 − unconditional (iii) > 0
with CI excluding 0 (the screen adds something).
**Hold research-only:** positive mean but any of (i)–(vi) fails. **Stop:** mean ≤ 0 at $0.00 fees, or unfilled-tail
loss > total income, on that side × archetype.

## 10. Deliverables

`scripts/p1_fetch_eod.py` (acquisition, manifest, dictionary/changelog), `scripts/p1_backtest.py`
(signals → trades → counterfactuals → metrics), `docs/replay/p1_trades.csv`, `docs/replay/p1_summary.md`, report §11.
One command reproduces every number.

## 11. Stated limitations (not modelled)

Dealer gamma / call-OI stacking (the amplifier for archetype (a)); assignment, pin and after-hours stock risk;
quote size / queue position (fill assumed if touched, 1 unit); ~3.6 test years in one name cannot estimate the ruin
probability of repeated 4Δ naked shorts — the gap stress and ES bounds are the substitute, and the pass criteria are
per side × archetype so a call-side tail cannot hide behind put income.

## 12. Open questions for annotation

1. Contract-level confirmation (§4) — is a 252-session percentile of "selected option IV − same-expiry ATM IV"
   computable robustly from EOD greeks across the split and strike-listing changes, or should the confirmation be a
   simpler *dollar* test (premium ≥ 3× its 60-session median for that Δ/DTE)?
2. `c = min(0.10, 0.5 × sale)` — right cap? Pandar's examples ("buy back at a profit", 0.62 → 0.40) suggest the credit
   kept is often larger and the buyback price is what's rested; alternative: rest at 0.6 × sale.
3. Archetype (c) "other" — drop, or promote as its own bucket if it turns out to be most of the signals?
4. Book-level sizing rule (±25% gap ≤ 10% NLV) — too loose / too tight for a 4Δ front-weekly short on NVDA?
5. Should the fidelity set (9.0) be a hard gate (must fire on ≥ 6 of 9 callouts) rather than a report?

---

## 13. (reserved)

## 14. Review — Charlie McElligott (2026-08-17)

Bottom line: the object is right — the SELL side of Pandar's book, buyback as the profit-take, no paper toys. Changes
required before code:

1. **Fill proxy.** Buybacks fill on the gap (§5b/5d: 09:31–10:25). Use ThetaData EOD **low** ≤ L as the fill test,
   close-ask as the conservative bound; report both; §7 1-min check decides which is truth.
2. **Split the two sell archetypes at the trigger.** (a) spot-up/vol-up grab: wing pct ≥ 85 AND that side's
   RR extreme (calls: RR25 pct ≤ 10; puts: ≥ 90) AND spot moving that way; (b) post-shock smile: both wings ≥ 85,
   `iv10d` pct ≥ 80. Tag every trade a/b; split every metric. (a) fails as a breakout, (b) as a second leg.
3. **2023 = squeeze stress test.** Report the sell-call tail there as the headline risk, not averaged. Add a gap
   scenario (overnight ±15% through the strike, per contract, at the 10%-of-NLV rule) to §10.
4. **Breakout stop as a named variant:** after entry, if wing pct rises further AND spot has moved ≥ 5% toward the
   strike → cover / synthetic-spread. Report with/without.
5. **Instrument:** keep |Δ| 0.04 / 5–12 DTE; record moneyness and dollar premium; add a 25–40% OTM moneyness variant
   to §8's grid.
6. **Threshold objective:** fit on ex-post 5-session P&L of the short (premium − mark), not wing-crush alone.
7. **Counterfactual (mandatory):** same signals held naked to expiry, no buyback.
8. **Earnings:** also exclude the session before the print on the call side.
9. **Not modelable here, say so:** dealer gamma / call-OI stacking (the amplifier for (a)).

Disposition: incorporate 1–8 into v0.2 (fill rule, archetype tags, stress section, breakout variant, moneyness grid,
P&L objective, counterfactual, earnings rule); 9 becomes a stated limitation.

Disposition: 1–8 applied in v0.2 (§4–§9); 9 is §11.

## 15. In plain terms — what review points #2 and #4 mean

### 15a. For the CIO

**#2 — "split the two archetypes."** The screen says "the far wing is unusually expensive, sell it." But there are two
different reasons a far wing gets expensive, and they fail in opposite ways:

- **(a) The grab.** The stock is ripping and the crowd is paying up for far *calls* only (or, mirror image, dumping and
  paying up for far *puts* only). One side of the smile is lifted; the other is not. If we sell that side and it keeps
  going, the loss is a *breakout*: the stock runs at our strike and the option we sold at 60¢ is worth $3–5.
- **(b) The post-shock smile.** Something just happened (DeepSeek, a tariff headline); *both* far wings are expensive
  because everyone is paying for lottery tickets in both directions and overall vol is very high. If we sell the far
  call here and it fails, it isn't a breakout — it's a *second leg down* (our sold call is fine; it's the naked put we
  might also have sold that hurts, or the portfolio around it).

Same order ticket, different disaster. If we throw both kinds of trade into one P&L column, the many quiet
post-shock sales (b) will produce a healthy-looking average that hides the few (a) trades that blow up in a melt-up.
So: stamp each trade "a" or "b" at entry using the surface (a = that side's wing high AND that side of the
risk-reversal at its extreme AND spot moving that way; b = both wings high AND overall front vol high), and report
every statistic for a and b separately. Decision consequence: we might promote (b) and shelve (a), or size them
differently — we cannot know unless they're separated.

**#4 — "the breakout stop."** Pandar's protection was *sizing*: sell few enough that if the stock reaches the strike
you can hold to expiry. Fine for a $1M PM account; brutal in a 2023-type melt-up. The variant adds a *tell*: after
we sell, if the wing keeps getting *more* expensive AND the stock has already moved 5% toward our strike, that's no
longer a grab that will fade — it's a trend — so we cover (or buy a further-out option to cap it). We run the
backtest both ways. The difference between the two P&Ls is the *price of the tell*: what we give up in premium
(covering grabs that would have faded) versus what we save in the ones that didn't. If the tell costs more than it
saves, we drop it and keep sizing as the only defence; if it saves more, it becomes part of the rule.

### 15b. From first principles

Look at what you actually sold: a ticket that pays only if NVDA is above, say, 300 in two weeks. You sold it for 62¢
because on that day people were unusually eager to own it. Now ask *why* they were eager — because there are two very
different reasons, and the reason tells you what can go wrong.

Reason one: the stock has been screaming higher for a week and buyers are chasing *up* — they want the far calls and
they don't care about the far puts. That is a crowd leaning one way. It usually tires; the ticket goes back to 11¢
and you keep 50¢. But sometimes the crowd is right and the stock keeps running, straight at your 300 line — then the
ticket you sold for 62¢ becomes worth $3, $5, more. Reason two: something scary just happened, prices are jumping
around, and people are buying far tickets in *both* directions — up and down — because they simply don't know. That
crowd isn't leaning; it's flinching. Your far-call ticket almost always dies quietly here, because a scared market
rarely runs 27% higher in two weeks; the danger from a flinching market is the *other* direction. Same 62¢ ticket,
sold into two different crowds, with two different ways of losing. If you pour both into one jar and average, the
many quiet flinch-sales make the jar look calm, and the rare leaning-crowd sale that ran you over is invisible in
the average — until it isn't. So we label each sale by which crowd we sold to, and we look at the two jars
separately. That is all #2 says.

#4 is about what to do when the leaning crowd turns out to be right. The stock keeps going and the far tickets get
*more* expensive, not less — that combination is the market telling you "this isn't a mood, it's a move." Pandar's
answer was to sell so few tickets that being run over doesn't matter. Ours can be the same, plus one rule: if the
tickets are still getting pricier and the stock has already covered a third of the distance to your line, buy the
ticket back (or buy the next one out to cap it) and stop arguing. Then measure it. Some grabs you cover would have
faded — that's the cost of the rule; some wouldn't — that's its benefit. The backtest reports both numbers so the
rule earns its place or doesn't. The simplification: "5% toward the strike" and "wing still rising" are one
reasonable definition of "this is a move"; the test may show a different line is better, and if no line beats
"just size small," that's a real answer too.

## 16. Codex adversarial review (2026-08-17) — panel FAIL, 14 findings — dispositions

Full output: `docs/specs/p1_codex_strategy_review_2026-08-17.md` (generic + Charlie McElligott + Senior Quant lenses; the
panel was given the white paper as context, not the Discord transcript, so its "fidelity" finding is partly an artefact
of what it was shown — the reconstruction lives in `docs/sources/discord_transcript_clean.txt` and report §5f).

| # | Finding (severity) | Applied in v0.2 |
|---|---|---|
| 1 | Look-ahead: close-of-day surface used for a 15:55 entry (CRITICAL) | §1: entry at t+1 open; all fills/marks from t+1. |
| 2 | Fidelity to Pandar not established by supplied context (HIGH) | §0 scoping; §9.0 fidelity set of known callouts. |
| 3 | Trigger is a surface point, not the traded contract (HIGH) | §4 contract-level confirmation from EOD greeks. |
| 4 | One trigger pools flow archetypes (HIGH) | §4 archetype tags a/b/c; §9 per side × archetype. |
| 5 | Fitting on wing-crush; overfitting; clustered signals (HIGH) | §8 pre-registered thresholds, episode clustering, grid as sensitivity only. |
| 6 | Instrument not invariant; negative buy limits; variable width (HIGH) | §5 one Δ rule, bid ≥ 0.20, `c = min(0.10, 0.5×sale)`, width recorded/normalised. |
| 7 | Fill model biased: live only t+1; close-ask; queue/size (HIGH) | §6 order live from entry minute; EOD low primary / close-ask bound; assumptions stated. |
| 8 | 2026 sample can't validate 2023–25 fills; "171 sessions" wrong (HIGH) | §2/§7: wording fixed; 2023–25 episode 1-min set acquired; per-regime truth-check enters pass/fail. |
| 9 | "Free spread" ignores opportunity cost vs same-time BTC (HIGH) | §6 mandatory same-time buy-to-close comparator. |
| 10 | Cooldown blocks inventory building (HIGH) | §4 cooldown on unpaired shorts only; single-cycle variant. |
| 11 | Naked-call / portfolio tail risk uncontrolled (CRITICAL) | §9 book-level gap stress, ES, margin proxy, forced-liquidation flag; sizing restated at book level; enters pass/fail. |
| 12 | Split normalisation mixes exposure units (CRITICAL) | §1 constant share exposure (100 post-split shares); fees per leg per unit. |
| 13 | Pass gates arbitrary/underdefined (CRITICAL) | §9 pre-registered per side × archetype: bootstrap CI, ES bound, fill-rule agreement, leave-one-shock-out, gap stress, screen-vs-unconditional. |
| 14 | Cannot isolate signal skill vs short-vol carry (HIGH) | §6 counterfactuals (i)–(iv) mandatory; §9 (vi). |

## 17. Change log

- **v0.2 (2026-08-17):** entry moved to t+1 open (no look-ahead); constant share-exposure units across the split;
  contract-level confirmation of the trigger; archetype tags (grab / smile / other) with per-side × archetype
  decisions; single Δ instrument rule, bid ≥ 0.20, `c = min(0.10, 0.5×sale)`; buyback live from entry, EOD low as
  primary fill test with close-ask bound and per-regime 1-min truth-check (2026 + 2023–25 episodes); same-time BTC
  comparator; cooldown on unpaired shorts only + single-cycle variant; breakout-stop variant; four counterfactuals;
  pre-registered thresholds with episode clustering; book-level gap stress / ES / margin in pass-fail; fidelity set;
  stated limitations; open questions for annotation.
- **v0.1 (2026-08-17):** initial draft; Charlie review (§14); plain-language §15; Codex panel (§16).
