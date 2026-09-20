"""Pause collection on a gateway outage; preserve native request provenance."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import threading
from typing import Any, Callable

import pipeline as p


class GatewayPause:
    """Stop queued downloads when a native endpoint reports a 502 or 503."""

    def __init__(self, base: Any, record: Callable[[dict], None]) -> None:
        self.base = base
        self.blocked = threading.Event()
        original = base.client
        owner = self

        class DiagnosticClient:
            def __getattr__(self, method: str) -> Callable:
                def query(**params: Any) -> Any:
                    try:
                        return getattr(original, method)(**params)
                    except Exception as exc:
                        detail = exc.details() if hasattr(exc, 'details') else ''
                        status = next((code for code in [502, 503]
                                       if f'HTTP status code {code}' in detail), None)
                        if status is not None:
                            owner.blocked.set()
                            record({'status': 'gateway_outage', 'method': method,
                                    'params': json.loads(json.dumps(params, default=str)),
                                    'http_status': status})
                        raise
                return query

        base.client = DiagnosticClient()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.base, name)

    def get(self, method: str, params: dict) -> tuple:
        if self.blocked.is_set():
            raise RuntimeError('Provider gateway outage; collection paused')
        try:
            return self.base.get(method, params)
        except Exception:
            if self.blocked.is_set():
                raise RuntimeError('Provider gateway outage; collection paused') from None
            raise


def freeze_service_policy() -> dict:
    """One exceptional post-outage attempt for the already exhausted XLV keys."""
    path = p.DATA / 'service_outage_amendment.json'
    inputs = {str(source): p.digest(source) for source in
              [Path(__file__), p.OUT/'test_service_resume.py', p.OUT/'SERVICE_OUTAGE.md']}
    if path.exists():
        result = json.loads(path.read_text())
        assert result['inputs'] == inputs
        return result
    logs = [json.loads(line) for line in (p.DATA/'requests.jsonl').read_text().splitlines()]
    starts = {r['key']: r for r in logs if r['status'] == 'started'}
    counts = Counter(r['key'] for r in logs if r['status'] == 'started')
    successes = {r['key'] for r in logs if r['status'] == 'ok'}
    keys = sorted(key for key, row in starts.items() if counts[key] == 3
                  and key not in successes and row['params']['symbol'] == 'XLV'
                  and row['at'] >= '2026-09-19T18:37:00')
    result = {'scientific_policy_change': False, 'inputs': inputs,
              'reason': 'Consecutive gateway failures; direct native diagnostic returned HTTP 502',
              'exceptional_fourth_attempt_keys': keys,
              'condition': 'Two uncached required XLI native endpoints succeed first',
              'normal_policy': 'Existing two attempts plus cooled INTERNAL-only third probe',
              'queue_policy': 'Pause on observed HTTP 502/503; no automatic outage retry loop'}
    p.write_json(path, result)
    return result


def recover_service_keys(base: Any, policy: dict) -> None:
    """Attempt only the frozen incident keys once after both native endpoints work."""
    collect = p.legacy.sys.modules['collect']
    logs = [json.loads(line) for line in (p.DATA/'requests.jsonl').read_text().splitlines()]
    starts = {r['key']: r for r in logs if r['status'] == 'started'}
    ok = {r['key'] for r in logs if r['status'] == 'ok'}
    pending = set(policy['exceptional_fourth_attempt_keys']) - ok
    if not pending:
        return
    selections = json.loads((p.DATA/'selections.json').read_text())
    selected = next(row for row in selections if row['symbol'] == 'XLI')
    params = p.input_params('XLI', selected['date'], selected['expirations'][1])
    # These are needed inputs, retained in the normal immutable cache, not duplicate probes.
    for method in p.legacy.METHODS:
        frame, _ = base.get(method, params)
        if frame.empty:
            raise ValueError('Empty response cannot establish service recovery')
    for key in sorted(pending):
        if base.attempts[key] != 3:
            raise RuntimeError(f'Exceptional fourth attempt already consumed: {key}')
        row = starts[key]
        args = row['params']
        params = p.input_params(args['symbol'], args['date'], args['expiration'])
        assert collect.request_key(row['method'], params) == key
        base.cache.record({'status': 'retry_authorized_post_gateway_recovery', 'key': key,
                           'method': row['method'], 'attempt': 4, 'parameters_changed': False})
        base.attempts[key] = 4
        base.cache.get(row['method'], params, getattr(base.client, row['method']))
        p.emit('service_key_recovered', key=key, symbol=args['symbol'], date=args['date'])


def main() -> None:
    from resume_complete import main as complete

    policy = freeze_service_policy()
    original_start = p.start_cache

    def start() -> GatewayPause:
        raw = original_start()
        safe = GatewayPause(raw, raw.cache.record)
        recover_service_keys(safe, policy)
        return safe

    p.start_cache = start
    complete()


if __name__ == '__main__':
    main()
