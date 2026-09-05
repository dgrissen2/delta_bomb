# Canonical single-name strategy names

These four labels are the project-wide names for the single-name option strategies.
Use them exactly in code, generated tables, reports, commit notes, and discussion.

| Canonical name | Short definition |
|---|---|
| **Buy-first call puke** | Buy a complete cheap far-OTM bull-call spread after a selloff as defined-risk rebound inventory. |
| **Buy-first call standard** | Buy the roughly 15-delta lower call in a constructive trend, then rest the adjacent upper-call sale into strength. |
| **Sell-first call grab** | Sell an unusually rich far front-weekly call during a one-sided grab, then try to buy the adjacent nearer call after the grab collapses. |
| **Buy-first put-tail inventory** | During calm/complacent conditions, buy complete cheap far-OTM put spreads as downside inventory and monetize later tail expansion or a crash. |

## Provenance and aliases

- **Buy-first call puke** replaces “Pandar-style puke convexity spread” and “buy-first puke.”
- **Buy-first call standard** replaces “white-paper 15-delta call leg-in” and “buy-first standard.”
- **Sell-first call grab** replaces “P1 call-wing grab sale-and-convert” and “sell-first grab” when referring to the one-sided call-grab subtype.
- **Buy-first put-tail inventory** names Pandar's penny put-spread inventory program, previously called “penny-spread inventory” or “buy the tail when nobody wants it.”

The names identify the option side, first action, and entry regime. Historical artifacts may retain old labels for point-in-time reproducibility, but all new outputs use the canonical names.

## Darrell's Pandar-only research scope

Recorded 2026-09-04: Darrell is interested **only in strategies specifically supported by Pandar's own documented process**. By default, future candidate scans, research comparisons, and strategy discussions should focus on the strict Pandar set below. Do not mix in white-paper-only, Charlie-derived, Brent-derived, or project-invented methods unless Darrell explicitly asks to broaden the scope.

### The strict two-method Pandar set

1. **Buy-first put-tail inventory** — the strongest-fidelity Pandar program. Pandar documented accumulating cheap 1:1 far-OTM put verticals, usually roughly $5 wide and under $0.10, across black-swan-reachable strikes and generally the next two monthly expirations. He accumulated during calm/complacency, recycled around volatility expansion and collapse, and rolled aging inventory. Fidelity caveat: Pandar personally often bought the long put first and sold the lower put later; the project's fixed 25–45% OTM band, complete-at-entry requirement, and universal 3×/5× exits are mechanizations, not Pandar rules.
2. **Sell-first call grab — Pandar core only** — Pandar directly documented selling unusually overpriced far-OTM front-weekly NVDA call tails, expecting the local wing to crush, and sizing the naked position so a strike touch would remain inside his margin/PNR cushion and could be held through expiry. Fidelity caveat: the project's systematic nearer-call conversion, 2–6-delta selection, 5–12 DTE window, quote/OI gates, sale-minus-$0.10 order, five-session window, and breakout override are project extensions. The clearest actual call-side conversion in the source record was performed by another trader.

### Excluded from the default Pandar-only set

- **Buy-first call puke** is a Pandar-supported tactic, not a sufficiently specified Pandar strategy. Pandar said he bought call spreads on large down days and farther-out call spreads as upside protection, but did not provide the project's DTE, OTM, construction, timing, or exit rules.
- **Buy-first call standard** is not Pandar-specific. It is the white paper's call-side mirror combined with the project's Charlie and NVDA-replay overlays.

### Interpretation rule

“Pandar-approved” must be used narrowly. Label every parameter as one of:

- **Pandar-direct** — explicitly documented by Pandar;
- **Pandar-derived** — a project rule extending Pandar's documented mechanism; or
- **not Pandar** — sourced from the white paper, Charlie/Brent frameworks, replay choices, or project engineering.

If strict fidelity means that every leg and parameter must be directly documented by Pandar, only **buy-first put-tail inventory** qualifies as a complete program; **sell-first call grab** qualifies only at its call-tail-sale-and-crush core.

The active screened inventory and session ledger live in [`replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/README.md`](replay/hiro_daily_pandar_approved_2026-08-11_to_2026-09-04/README.md). That master intentionally contains no buy-first call puke or buy-first call standard rows.
