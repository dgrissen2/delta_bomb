"""hiro_watch/regime.py — vt_break / vt_deep / sgi_low tags from the engine's own sources."""
from __future__ import annotations

import pandas as pd

from hiro_watch import regime as R


class _Cfg:
    def __init__(self, levels, spx_dir):
        self._p = {"levels_csv": levels, "spx_dir": spx_dir}

    def path_of(self, k):
        return self._p[k]


def _fixture(tmp_path, sgi, vt, o, c):
    lv = tmp_path / "levels.csv"
    lv.write_text("Date,sg_index,Net Delta,Call Wall,Put Wall,Vol Trigger,pivot,pivot_updated\n"
                  f"2026-09-09,{sgi},,7800.0,7500.0,{vt},,\n")
    spx = tmp_path / "spx"; spx.mkdir(exist_ok=True)
    pd.DataFrame({"min": [570, 960], "open": [o, c], "high": [max(o, c)] * 2, "low": [min(o, c)] * 2,
                  "close": [o, c]}).to_parquet(spx / "2026-09-09.parquet")
    return _Cfg(lv, spx)


def test_break_deep_and_low_index(tmp_path):
    assert R.tags("2026-09-09", _fixture(tmp_path, 2.0, 7700.0, 7705.0, 7675.0)) == ["vt_break"]      # opened above, closed 25 below
    assert R.tags("2026-09-09", _fixture(tmp_path, 2.0, 7700.0, 7705.0, 7690.0)) == []                # 10 below: not a break
    assert R.tags("2026-09-09", _fixture(tmp_path, 2.0, 7700.0, 7650.0, 7690.0)) == ["vt_deep"]       # opened 50 below
    assert R.tags("2026-09-09", _fixture(tmp_path, -2.0, 7700.0, 7720.0, 7730.0)) == ["sgi_low"]
    assert R.tags("2026-09-09", _fixture(tmp_path, -2.0, 7700.0, 7650.0, 7640.0)) == ["vt_deep", "sgi_low"]


def test_no_levels_row_means_no_tags(tmp_path):
    cfg = _fixture(tmp_path, 2.0, 7700.0, 7650.0, 7640.0)
    assert R.tags("2026-09-10", cfg) == []
