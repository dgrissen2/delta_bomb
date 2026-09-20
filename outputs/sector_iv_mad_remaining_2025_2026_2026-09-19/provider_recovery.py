"""One cooled, exclusive third attempt after a provider INTERNAL error."""
from __future__ import annotations

import threading
import time
from typing import Any, Callable


class ProviderRecovery:
    """Keep normal retries; serialize one final INTERNAL-only provider probe."""

    def __init__(self, base: Any, *, key_fn: Callable, previous_errors: dict[str,str],
                 sleep: Callable[[float],None] = time.sleep, delay: float = 30.) -> None:
        self.base = base
        self.key_fn = key_fn
        self.previous_errors = previous_errors
        self.sleep, self.delay = sleep, delay
        self.condition = threading.Condition()
        self.active = 0
        self.exclusive = False

    @property
    def cache(self) -> Any:
        return self.base.cache

    def get(self, method: str, params: dict) -> tuple:
        key = self.key_fn(method,params)
        with self.condition:
            while self.exclusive:
                self.condition.wait()
            self.active += 1
        try:
            return self.base.get(method,params)
        except RuntimeError as exc:
            failure = exc
        finally:
            with self.condition:
                self.active -= 1
                self.condition.notify_all()
        message = str(failure)
        internal = message.endswith(': INTERNAL') or (
            'attempt ceiling reached' in message and self.previous_errors.get(key)=='INTERNAL')
        if not internal or self.base.attempts.get(key) != 2:
            raise failure
        with self.condition:
            while self.exclusive:
                self.condition.wait()
            self.exclusive = True
            while self.active:
                self.condition.wait()
        try:
            if self.base.attempts.get(key) != 2:
                raise failure
            self.cache.record({'status':'retry_authorized_cooled_internal_probe','key':key,
                'method':method,'attempt':3,'delay_seconds':self.delay,
                'exclusive':True,'parameters_changed':False})
            self.sleep(self.delay)
            self.base.renewable.invalidate()
            self.base.attempts[key] = 3
            return self.cache.get(method,params,getattr(self.base.renewable,method))
        finally:
            with self.condition:
                self.exclusive = False
                self.condition.notify_all()
