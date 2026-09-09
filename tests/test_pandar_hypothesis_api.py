"""Budget and batching guards for the authorized historical data program."""

import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from scripts.pandar_hypothesis_api import BudgetExceeded, SharedBudget, ticker_batches


def test_batches_deduplicate_and_never_exceed_ten():
    batches = list(ticker_batches([str(n) for n in range(23)] + ["2"]))
    assert [len(batch) for batch in batches] == [10, 10, 3]
    assert len(set(sum(batches, []))) == 23


def test_concurrent_budget_counts_failed_attempts_before_io(tmp_path):
    path = tmp_path / "budget.json"

    def reserve(_):
        budget = SharedBudget(path, limit=7)
        try:
            return budget.reserve("orats", "hist/earnings", {"ticker": "AAPL"}, "metadata")
        except BudgetExceeded:
            return None

    with ThreadPoolExecutor(max_workers=5) as pool:
        attempts = list(pool.map(reserve, range(20)))
    assert len([item for item in attempts if item is not None]) == 7
    data = json.loads(path.read_text())
    assert data["used"] == 7
    assert len({item["id"] for item in data["attempts"]}) == 7
    assert all(item["status"] == "started" for item in data["attempts"])


def test_budget_rejects_secrets_and_inconsistent_limit(tmp_path):
    budget = SharedBudget(tmp_path / "budget.json", limit=2)
    with pytest.raises(ValueError, match="secret"):
        budget.reserve("orats", "hist/earnings", {"token": "secret"}, "metadata")
    budget.reserve("orats", "hist/earnings", {"ticker": "AAPL"}, "metadata")
    with pytest.raises(ValueError, match="limit"):
        SharedBudget(budget.path, limit=3)
