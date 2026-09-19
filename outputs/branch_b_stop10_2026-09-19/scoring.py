"""Same native first-touch convention with an explicitly specified adverse barrier."""
from numbers import Real
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'branch_b_150d_rerun_2026-09-19'))
from rerun_core import checked_window  # noqa: E402


def score(raw: pd.DataFrame, minute: int, adverse_points: float = 10) -> dict:
    """Observe +5 versus the adverse barrier in entry minute through minute +59."""
    if (isinstance(adverse_points, (bool, np.bool_)) or not isinstance(adverse_points, Real)
            or not np.isfinite(adverse_points) or adverse_points <= 0):
        raise ValueError('Adverse distance must be finite and positive')
    window = checked_window(raw, minute, minute+59)
    price = float(window.open.iloc[0])
    up = window.index[window.high.ge(price+5-1e-8)].tolist()
    down = window.index[window.low.le(price-adverse_points+1e-8)].tolist()
    first_up, first_down = up[0] if up else 9999, down[0] if down else 9999
    touch = min(first_up, first_down)
    outcome = ('neither' if touch == 9999 else 'ambiguous' if first_up == first_down
               else 'target_first' if first_up < first_down else 'adverse_first')
    return {'outcome': outcome, 'first_touch_min': None if touch == 9999 else touch,
            'entry_price': price, 'horizon_minutes': 60,
            'endpoint_change': float(window.close.iloc[-1]-price)}
