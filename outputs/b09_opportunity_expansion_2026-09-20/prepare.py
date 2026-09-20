"""Freeze expansion memberships and volume features before joining outcomes."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from study import (
    DATA,
    OLD,
    OUT,
    PRIOR,
    REGISTRY,
    ROOT,
    SPY,
    SYMBOLS,
    digest,
    either,
    persistence,
    rvol,
    write_json,
)


def checked(path: Path, expected: str, hashes: dict) -> None:
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"Changed source: {path}")
    hashes[str(path)] = actual


def persistence_features(
    events: pd.DataFrame, hashes: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join exact historic endpoints, retaining per-instrument proof of admission."""
    sources = json.loads(REGISTRY.read_text())
    assert sorted(s["symbol"] for s in sources) == SYMBOLS
    registry_hash = json.loads((PRIOR / "freeze.json").read_text())["input_hashes"][
        str(REGISTRY)
    ]
    checked(REGISTRY, registry_hash, hashes)
    specs = []
    for source in sources:
        p = Path(
            next(p for p in source["files"] if p.endswith("/scored_windows.parquet"))
        )
        specs.append((source["symbol"], p, source["files"][str(p)]))
    spx = ROOT / "spx_iv_mad_2024_2026_2026-09-20-v1/calibration_exact/SPXW"
    sp = spx / "scored_windows.parquet"
    specs.append(
        (
            "SPXW",
            sp,
            json.loads((spx / "summary.json").read_text())["output_hashes"][str(sp)],
        )
    )
    request = pd.concat(
        [
            events[["entry_id", "date", "known_min"]].assign(
                offset=o, end_min=events.known_min - 5 + o
            )
            for o in range(5)
        ],
        ignore_index=True,
    )
    columns = [
        "date",
        "end_min",
        "start_min",
        "block",
        "signed_score",
        "b1",
        "b2",
        "acceleration",
        "scale",
        "source_minutes",
        "available",
        "score_status",
    ]
    ledgers, cubes = [], {}
    for symbol, path, expected in specs:
        checked(path, expected, hashes)
        score = pd.read_parquet(path, columns=columns)
        assert not score.duplicated(["date", "end_min"]).any()
        joined = request.merge(
            score, on=["date", "end_min"], how="left", validate="many_to_one"
        )
        joined["symbol"] = symbol
        good = joined[joined.signed_score.notna()].drop_duplicates(["date", "end_min"])
        assert (
            np.isfinite(good[["signed_score", "b1", "b2", "acceleration", "scale"]])
            .all()
            .all()
        )
        np.testing.assert_allclose(good.signed_score, -good.acceleration / good.scale)
        np.testing.assert_allclose(
            good.acceleration, (good.b2 - good.b1) / 15, atol=1e-14
        )
        assert good.scale.gt(0).all() and good.available.all()
        assert good.block.eq((good.end_min - 570) // 60).all()
        for r in good.itertuples():
            times = json.loads(r.source_minutes)
            assert r.start_min == r.end_min - 29
            assert len(times) == len(set(times)) and all(
                r.start_min <= t <= r.end_min for t in times
            )
        cubes[symbol] = {
            c: joined.pivot(index="entry_id", columns="offset", values=c)
            .reindex(events.entry_id)
            .to_numpy()
            for c in ["signed_score", "b2"]
        }
        ledgers.append(joined)
    m = np.stack([cubes[s]["signed_score"] for s in SYMBOLS], axis=2)
    b = np.stack([cubes[s]["b2"] for s in SYMBOLS], axis=2)
    sector, sw = persistence(m, b, 4)
    index, iw = persistence(
        cubes["SPXW"]["signed_score"][:, :, None], cubes["SPXW"]["b2"][:, :, None], 1
    )
    result = events[["entry_id", "date", "known_min", "half", "block"]].copy()
    result["sector_persist_state"], result["spx_persist_state"] = sector, index
    result["persistence_state"] = either(sector, index)
    result["sector_witness_min"] = np.where(sw >= 0, events.known_min - 5 + sw, -1)
    result["spx_witness_min"] = np.where(iw >= 0, events.known_min - 5 + iw, -1)
    return result, pd.concat(ledgers, ignore_index=True)


def volume_features(
    events: pd.DataFrame, dates: pd.DataFrame, hashes: dict
) -> pd.DataFrame:
    """Build one relative-volume feature and strictly pre-entry SPX diagnostics."""
    hashes[str(SPY)] = digest(SPY)
    raw = pd.read_parquet(SPY, columns=["date", "min", "volume"])
    raw["date"] = raw.date.astype(str)
    assert not raw.duplicated(["date", "min"]).any()
    calendar = sorted(raw.date.unique())
    raw = raw[raw["min"].between(570, 959)].copy()
    raw["volume"] = raw.volume.where(np.isfinite(raw.volume) & raw.volume.ge(0))
    matrix = raw.pivot(index="date", columns="min", values="volume").reindex(
        index=calendar, columns=range(570, 960)
    )
    windows = matrix.T.rolling(5, min_periods=5).sum().T
    rows = []
    for day in dates.itertuples():
        path = Path(day.source_path)
        checked(path, day.source_sha256, hashes)
        price = pd.read_parquet(path).set_index("min")
        for e in events[events.date.eq(day.date)].itertuples():
            value, median, status = rvol(windows, e.date, e.known_min)
            pos = calendar.index(e.date) if e.date in calendar else -1
            history = calendar[pos - 60 : pos] if pos >= 60 else []
            current = windows.loc[e.date, e.known_min - 1] if pos >= 0 else np.nan
            native = price.loc[e.known_min - 30 : e.known_min - 1]
            assert len(native) == 30
            points = np.r_[native.open.iloc[0], native.close.to_numpy()]
            assert price.loc[e.known_min, "open"] > day.vol_trigger
            assert price.loc[570 : e.known_min - 1, "low"].min() > day.vol_trigger
            rows.append(
                dict(
                    entry_id=e.entry_id,
                    date=e.date,
                    known_min=e.known_min,
                    rvol=value,
                    reference_median=median,
                    current_volume=current,
                    status=status,
                    history_dates=json.dumps(history),
                    history_start=history[0] if history else "",
                    history_end=history[-1] if history else "",
                    state="yes"
                    if value > 1
                    else "no"
                    if np.isfinite(value)
                    else "unknown",
                    return30_bps=1e4 * (points[-1] / points[0] - 1),
                    rv30_points=float(np.sqrt(np.square(np.diff(points)).sum())),
                )
            )
    return pd.DataFrame(rows)


def main() -> None:
    if (DATA / "freeze.json").exists():
        raise FileExistsError("Prepared experiment already frozen")
    DATA.mkdir(parents=True, exist_ok=True)
    hashes = {}
    frozen = json.loads((PRIOR / "freeze.json").read_text())
    for name in ["event_keys.parquet", "research_dates.csv", "memberships.parquet"]:
        p = PRIOR / name
        checked(p, frozen["output_hashes"][str(p)], hashes)
    basket = OLD / "basket_features.parquet"
    old_freeze = json.loads((OLD / "basket_freeze.json").read_text())
    checked(basket, old_freeze["output_hashes"][str(basket)], hashes)
    sf = OLD / "sector_features.parquet"
    checked(sf, old_freeze["inputs"][str(sf)], hashes)
    events = pd.read_parquet(PRIOR / "event_keys.parquet")
    dates = pd.read_csv(PRIOR / "research_dates.csv")
    members = pd.read_parquet(PRIOR / "memberships.parquet")
    assert len(dates) == 239 and events.always_above.all() and events.entry_id.is_unique
    features = events.copy()
    for rule, column in [("OR_F4_SPX", "base_state"), ("F4", "f4_state")]:
        lookup = members.loc[members.rule.eq(rule)].set_index("entry_id").state
        features[column] = features.entry_id.map(lookup)
    original = pd.read_parquet(
        basket, columns=["date", "known_min", "original_accelerating_6"]
    )
    features = features.merge(
        original, on=["date", "known_min"], validate="many_to_one"
    )
    b09 = events[events.variant.eq("b09")].copy()
    persisted, ledger = persistence_features(b09, hashes)
    volumes = volume_features(b09, dates, hashes)
    features = features.merge(
        persisted.drop(columns=["date", "known_min", "half", "block"]),
        on="entry_id",
        how="left",
        validate="one_to_one",
    )
    assert (
        features.loc[features.base_state.eq("yes"), "persistence_state"].eq("yes").all()
    )
    features["baseline"] = features.variant.eq("b09") & features.base_state.eq("yes")
    features["b05_candidate"] = features.variant.eq("b05") & features.f4_state.eq("yes")
    features["b07_candidate"] = features.variant.eq(
        "b07"
    ) & features.original_accelerating_6.eq("yes")
    features["persistence_candidate"] = features.variant.eq(
        "b09"
    ) & features.persistence_state.eq("yes")
    for name, frame in [
        ("memberships.parquet", features),
        ("persistence_sources.parquet", ledger),
        ("volume_features.parquet", volumes),
    ]:
        frame.to_parquet(DATA / name, index=False)
    dates.to_csv(DATA / "research_dates.csv", index=False)
    outputs = {
        str(p): digest(p) for p in DATA.iterdir() if p.suffix in [".parquet", ".csv"]
    }
    code = {str(p): digest(p) for p in OUT.iterdir() if p.suffix in [".py", ".md"]}
    write_json(
        DATA / "freeze.json",
        {
            "inputs": hashes,
            "outputs": outputs,
            "code_protocol": code,
            "scope": "Three separate expansions and single RVOL comparison; outcomes not joined",
            "participation": {
                c: int(features[c].sum())
                for c in [
                    "baseline",
                    "b05_candidate",
                    "b07_candidate",
                    "persistence_candidate",
                ]
            },
            "volume_status": volumes.status.value_counts().to_dict(),
        },
    )
    print(
        "Outcome-free memberships frozen:",
        features[
            ["baseline", "b05_candidate", "b07_candidate", "persistence_candidate"]
        ]
        .sum()
        .to_dict(),
        flush=True,
    )
    print("Volume coverage:", volumes.status.value_counts().to_dict(), flush=True)


if __name__ == "__main__":
    main()
