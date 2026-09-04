"""Task 13 tests: cache determinism, hash guard, refusal, validity, boundary scan, sanity."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from hiro_engine_v2.chains import (ChainError, ChainStore, friday_expiry_for,
                                real_cache_sanity)


@pytest.fixture(scope="module")
def store(config):
    return ChainStore()


def test_friday_expiry_convention():
    assert str(friday_expiry_for("2026-08-12")) == "2026-09-11"   # exactly 30 DTE
    assert str(friday_expiry_for("2026-08-17")) == "2026-09-18"   # 32 vs 25 -> 32
    assert str(friday_expiry_for("2026-08-21")) == "2026-09-18"   # 28


def test_cache_determinism_and_pin(config, store):
    cd1 = store.load("2026-08-18")
    assert len(cd1.frame) > 50000 and cd1.expiry == "2026-09-18"
    assert store.frozen_manifest_hash(config.control_days) == \
        str(config.get("chains", "frozen_manifest_hash"))
    store.verify_frozen(config)                       # must not raise


def test_hash_guard_detects_change(config, store, monkeypatch):
    monkeypatch.setattr(ChainStore, "frozen_manifest_hash", lambda self, days: "0" * 64)
    with pytest.raises(ChainError, match="frozen chain cache changed"):
        store.verify_frozen(config)


def test_missing_date_refused(store):
    with pytest.raises(ChainError, match="R13.1"):
        store.load("2031-01-02")


def test_quote_validity_rules(store):
    from hiro_engine_v2.models import QuoteSnap
    assert QuoteSnap(7500, 1.0, 1.0, valid=True).mid == 1.0        # locked ok by rule
    cd = store.load("2026-08-18")
    q = cd.quote(700, 7420.0)
    assert q is not None and q.valid and q.ask >= q.bid > 0


def test_real_cache_sanity_all_frozen_days(config, store):
    for d in config.control_days:
        assert real_cache_sanity(store.load(d)) == [], d


def test_option_client_import_boundary():
    """Design: chains.py is the ONLY production module using option endpoints
    (spike scripts are the named diagnostic exception)."""
    pkg = Path(__file__).resolve().parents[1]
    pat = re.compile(r"option_(history|snapshot|at_time|list)_")
    offenders = []
    for f in pkg.glob("*.py"):
        if f.name in ("chains.py",) or f.name.startswith("spike_"):
            continue
        if pat.search(f.read_text()):
            offenders.append(f.name)
    assert offenders == [], f"option-client usage outside chains.py: {offenders}"
