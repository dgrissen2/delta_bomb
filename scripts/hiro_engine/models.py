"""Data model (design.md): immutable rows and state objects. No logic here."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Optional


@dataclass(frozen=True)
class Bar:
    """SPX 1-min bar. min = minutes since midnight ET (570 = 09:30)."""
    min: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class SpyBar:
    min: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Levels:
    """SG daily levels (R2.3). valid iff row date == session date AND cw - vt > 0."""
    date: str
    vt: Optional[float]
    cw: Optional[float]
    sg_index: Optional[float]
    im: Optional[float]        # implied move in SPX points; None => R3.4 returns CHOP
    valid: bool


@dataclass(frozen=True)
class CalendarDay:
    date: str
    is_event_day: bool
    reason: str


@dataclass(frozen=True)
class Vetoes:
    vt_broken: bool = False
    levels_invalid: bool = False
    flow_veto: bool = False


@dataclass(frozen=True)
class FeatureRow:
    """One completed bar's derived quantities (R3). Immutable; vetoes/health are
    attached by Session (task 5b) — FeatureEngine never populates them."""
    min: int
    bar: Bar
    open_0930: float
    # R3.1 HIRO lines ($B)
    L: float
    Lc: float
    Lp: float
    N: float
    r5: Optional[float]
    r15: Optional[float]
    r30: Optional[float]
    r15n: Optional[float]
    # R3.2 run machine
    run: float
    dur: float
    rate: float
    dC: float
    dP: float
    dN: float
    weak_side: float
    share: Optional[float]
    drawdown: float
    run_broke: bool
    # R3.3 price
    pull30: Optional[float]
    bounce30: Optional[float]
    mid30: Optional[float]
    ref_low_bar: Optional[int]      # bar min of the 30-bar close low (Branch A BH anchor)
    bh_level: Optional[float]       # highest HIGH from ref_low_bar through this bar (R7.2 A)
    range60: Optional[float]
    range60_pct: Optional[float]
    warmup: bool
    ema5: float
    ema9: float
    ema20: float
    vwap: Optional[float]           # SPY volume VWAP (R2.6); None => DEGRADED_VWAP
    spy_close: Optional[float]
    vwap_share10: Optional[float]   # share of last 10 SPY bars closing above VWAP
    # R3.4 context (retained values; None until first read)
    context_1030: Optional[str]
    context_1300: Optional[str]
    # R3.5 episodes (id increments per new episode of that branch; None = no active episode)
    episode_a: Optional[int]
    episode_b: Optional[int]
    episode_a_start: Optional[int]  # first minute of the active A episode (R11.1)
    episode_b_start: Optional[int]
    a_conditions: bool              # R6.1 (i)-(iv) all true this bar
    b_armed: bool                   # R6.2 arm set true this bar (pre-gates)
    b_gates: bool                   # R6.2 gates true this bar
    late_state: bool                # R6.3 suppression state
    hiro_fresh: bool                # False while HIRO is down (R10.1)
    # attached by Session:
    vetoes: Vetoes = field(default=Vetoes())
    health: str = "OK"              # OK|HIRO_DOWN|SPX_STALLED|DEGRADED_VWAP
    option_mid_move: Optional[float] = None   # live+chain: |mid - entry mid| against the leg (R7.3)


@dataclass(frozen=True)
class PendingEntry:
    branch: str                     # "A" | "B"
    side: str                       # "long_first" | "sell_first"
    signal_min: int
    episode: int
    expiry: Optional[str] = None
    strike_hint: Optional[str] = None
    chain_quote_ts: Optional[str] = None
    bh_level: Optional[float] = None    # Branch A scratch anchor, fixed at signal time (R7.2)
    entry_L: Optional[float] = None     # Branch B flow anchor = L at the SIGNAL bar (research L0)


@dataclass
class SimTrade:
    """The one open simulated trade. Every field persists in ENTRY/EXIT events."""
    id: int
    branch: str
    side: str
    signal_min: int
    entry_min: int
    s0: float
    expiry: Optional[str]
    leg_strikes: Optional[str]
    entry_option_mid: Optional[float]
    resting_limit_ref: Optional[float]
    target: float                   # S0 +/- fill_touch_pts
    bh_level: Optional[float]       # Branch A scratch anchor (R7.2)
    entry_L: Optional[float]        # Branch B scratch anchor (R7.2)
    cap_source: str                 # "chain" | "proxy"
    cap_value: float
    state: str = "open"             # open | closed
    exit_type: Optional[str] = None
    exit_ref: Optional[float] = None
    resolution_debit: Optional[float] = None
    minutes: Optional[int] = None   # minutes-to-fill for fills
    adverse: float = 0.0
    episode: Optional[int] = None


@dataclass(frozen=True)
class TierPolicy:
    """R13.1 — immutable per run. `full` and `price` are the only two instances."""
    name: str
    branch_b_enabled: bool
    price_a_conditions: bool        # True => Branch A uses (i),(iii),(iv) only
    r43_enabled: bool               # flow veto
    r72_enabled: bool               # flow-shutoff scratch (BH scratch always retained)
    requires_hiro: bool             # False => missing HIRO is NOT an outage (price tier)
    tier_stamp: str


TIER_FULL = TierPolicy("full", branch_b_enabled=True, price_a_conditions=False,
                       r43_enabled=True, r72_enabled=True, requires_hiro=True,
                       tier_stamp="full")
TIER_PRICE = TierPolicy("price", branch_b_enabled=False, price_a_conditions=True,
                        r43_enabled=False, r72_enabled=False, requires_hiro=False,
                        tier_stamp="price")
TIERS = {"full": TIER_FULL, "price": TIER_PRICE}


@dataclass
class EngineState:
    """Mutated only by Executor (design: one owner)."""
    open_trade: Optional[SimTrade] = None
    pending_entry: Optional[PendingEntry] = None
    pending_exit: Optional[str] = None          # exit type awaiting next-bar-open pricing
    entries_today: int = 0
    next_trade_id: int = 1
    entered_episode_a: Optional[int] = None
    entered_episode_b: Optional[int] = None
    last_heartbeat_min: Optional[int] = None


EVENT_FIELDS = [
    "ts", "mode", "tier", "session_date", "config_hash", "schema_v",
    "event_type", "rule_id", "branch", "side", "s0", "expiry", "leg_strikes",
    "strike_quote_ts", "run", "rate", "dC", "dP", "share", "r15",
    "pull30", "bounce30", "context", "health",
    "outcome_type", "outcome_minutes", "exit_ref", "cap_source", "resolution_debit",
    "adverse", "trade_id", "entry_min", "signal_min", "entry_option_mid",
    "resting_limit_ref", "target", "bh_level", "entry_L", "cap_value", "episode",
    "notes",
]


@dataclass
class Event:
    """One event == one CSV row == one console line (R8.1). schema_v=1, explicit columns."""
    ts: str = ""
    mode: str = ""
    tier: str = ""
    session_date: str = ""
    config_hash: str = ""
    schema_v: int = 1
    event_type: str = ""
    rule_id: str = ""
    branch: str = ""
    side: str = ""
    s0: Optional[float] = None
    expiry: Optional[str] = None
    leg_strikes: Optional[str] = None
    strike_quote_ts: Optional[str] = None
    run: Optional[float] = None
    rate: Optional[float] = None
    dC: Optional[float] = None
    dP: Optional[float] = None
    share: Optional[float] = None
    r15: Optional[float] = None
    pull30: Optional[float] = None
    bounce30: Optional[float] = None
    context: Optional[str] = None
    health: str = "OK"
    outcome_type: Optional[str] = None
    outcome_minutes: Optional[float] = None
    exit_ref: Optional[float] = None
    cap_source: Optional[str] = None
    resolution_debit: Optional[float] = None
    adverse: Optional[float] = None
    trade_id: Optional[int] = None
    entry_min: Optional[int] = None
    signal_min: Optional[int] = None
    entry_option_mid: Optional[float] = None
    resting_limit_ref: Optional[float] = None
    target: Optional[float] = None
    bh_level: Optional[float] = None
    entry_L: Optional[float] = None
    cap_value: Optional[float] = None
    episode: Optional[int] = None
    notes: str = ""


assert [f.name for f in fields(Event)] == EVENT_FIELDS, "Event schema drifted from EVENT_FIELDS"


@dataclass(frozen=True)
class SessionRow:
    date: str
    disposition: str                # countable | shakedown | partial | event_standdown
    outage_min: int
    mode: str
    config_hash: str
