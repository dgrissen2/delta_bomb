"""ONE summarizer shared by backtest and sweep (R13.3) + leaderboard (R13.4)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config
from .control import build_control_frame, clock_matched, midpoint_matched

BOOT_DRAWS = 2000
BOOT_SEED = 42
MIN_TRADES, MIN_DAYS = 15, 4          # R13.4 grey-out thresholds


def bootstrap_fill_ci(entries: pd.DataFrame) -> tuple[float, float]:
    """Day-clustered bootstrap 90% CI on the fill rate: resample days with
    replacement, 2,000 draws, numpy default_rng(42)."""
    e = entries[entries.exit_type != "censored"]
    days = sorted(e.date.unique())
    if not days or not len(e):
        return float("nan"), float("nan")
    rng = np.random.default_rng(BOOT_SEED)
    by_day = {d: e[e.date == d] for d in days}
    rates = []
    for _ in range(BOOT_DRAWS):
        pick = rng.choice(days, size=len(days), replace=True)
        n = f = 0
        for d in pick:
            g = by_day[d]
            n += len(g)
            f += int((g.exit_type == "fill").sum())
        rates.append(f / n if n else np.nan)
    rates = np.asarray(rates, float)
    rates = rates[~np.isnan(rates)]
    if not len(rates):
        return float("nan"), float("nan")
    return float(np.quantile(rates, 0.05)), float(np.quantile(rates, 0.95))


def summarize(cfg: Config, entries: pd.DataFrame, qualify: pd.DataFrame,
              days: list[str], variant: str = "frozen") -> dict:
    """R13.3 summary contract for one variant. Own-dataset matched controls:
    R11.4 form for sell-first entries, R11.5 form for long-first."""
    noncens = entries[entries.exit_type != "censored"] if len(entries) else entries
    out = dict(variant=variant,
               trades=len(entries),
               episodes=int(len(qualify)) if qualify is not None else None,
               days=len(days),
               fills=int((entries.exit_type == "fill").sum()) if len(entries) else 0,
               fill_rate=(float((noncens.exit_type == "fill").mean())
                          if len(noncens) else float("nan")),
               censored=int((entries.exit_type == "censored").sum()) if len(entries) else 0)
    ci = bootstrap_fill_ci(entries) if len(entries) else (float("nan"),) * 2
    out["fill_ci90_lo"], out["fill_ci90_hi"] = ci
    sf = entries[entries.side == "sell_first"] if len(entries) else entries
    lf = entries[entries.side == "long_first"] if len(entries) else entries
    # v3 controls exist only where chain data exists: the frozen set uses the
    # pinned frame; other ranges report no control (never a touch-based one)
    if len(entries) and set(days) <= set(cfg.control_days):
        from .control import clock_matched_v3, load_control_frame, midpoint_matched_v3
        frame = load_control_frame(cfg)
        out["control_sell_first"] = (clock_matched_v3(cfg, sf.signal_min, frame)
                                     if len(sf) else float("nan"))
        out["control_long_first"] = (midpoint_matched_v3(cfg, lf.signal_min, frame)
                                     if len(lf) else float("nan"))
    else:
        out["control_sell_first"] = out["control_long_first"] = float("nan")
    # $ economics under fill_mode=limit (spot_touch runs keep SPX-pt semantics)
    if len(entries) and "pnl_usd" in entries.columns and entries.pnl_usd.notna().any():
        out["realized_pnl_usd"] = float(entries.pnl_usd.sum())
    else:
        out["realized_pnl_usd"] = float("nan")
    return out


def print_summary(s: dict) -> None:
    print(f"[{s['variant']}] trades={s['trades']} episodes={s['episodes']} "
          f"days={s['days']} fills={s['fills']} "
          f"fill_rate={s['fill_rate']:.3f} CI90=({s['fill_ci90_lo']:.3f},{s['fill_ci90_hi']:.3f}) "
          f"censored={s['censored']} | controls: sell {s['control_sell_first']:.3f} "
          f"long {s['control_long_first']:.3f} | realized ${s.get('realized_pnl_usd', float('nan')):,.0f}"
          .replace("nan", "—").replace("$—", "n/a (spot_touch)"))


def leaderboard(rows: list[dict]) -> pd.DataFrame:
    """R13.4: print cells examined; grey out (<15 trades or <4 days) and exclude
    them from ranking."""
    df = pd.DataFrame(rows)
    df["eligible"] = (df.trades >= MIN_TRADES) & (df.days >= MIN_DAYS)
    ranked = df[df.eligible].sort_values("fill_rate", ascending=False)
    greyed = df[~df.eligible]
    print(f"\nleaderboard — {len(df)} cells examined, "
          f"{len(greyed)} greyed out (<{MIN_TRADES} trades or <{MIN_DAYS} days)")
    cols = ["variant", "trades", "days", "fills", "fill_rate",
            "fill_ci90_lo", "fill_ci90_hi", "censored"]
    if len(ranked):
        print(ranked[cols].round(3).to_string(index=False))
    for r in greyed.itertuples():
        print(f"  [greyed] {r.variant}: trades={r.trades} days={r.days} (excluded from ranking)")
    return df
