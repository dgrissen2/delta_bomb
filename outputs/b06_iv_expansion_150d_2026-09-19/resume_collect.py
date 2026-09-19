"""Resume immutable SDK requests with coordinated authentication renewal only."""
from __future__ import annotations

import threading
import time
from typing import Any, Callable

import collect


class AuthenticationStopped(Exception):
    """Stop the queue rather than consuming attempts with invalid authentication."""


class RenewableClient:
    """Renew every five minutes, waiting for this collector's active calls."""

    def __init__(self, client: Any, authenticate: Callable[[], Any] = collect.authenticate,
                 clock: Callable[[], float] = time.monotonic, ttl: float = 300.0) -> None:
        self.client = client
        self.authenticate = authenticate
        self.clock = clock
        self.ttl = ttl
        self.born = clock()
        self.condition = threading.Condition()
        self.active = 0
        self.invalid = False
        self.failed = False

    def invalidate(self) -> None:
        with self.condition:
            self.invalid = True

    def stop(self) -> None:
        with self.condition:
            self.failed = True
            self.condition.notify_all()

    def __getattr__(self, name: str) -> Callable[..., Any]:
        def query(**params: Any) -> Any:
            with self.condition:
                while self.invalid or self.clock() - self.born >= self.ttl:
                    if self.failed:
                        raise AuthenticationStopped("Authentication renewal failed")
                    if self.active:
                        self.condition.wait()
                        continue
                    try:
                        self.client = self.authenticate()
                    except Exception:
                        self.failed = True
                        self.condition.notify_all()
                        raise AuthenticationStopped("Authentication renewal failed") from None
                    self.born = self.clock()
                    self.invalid = False
                    collect.emit("session_renewed", at=collect.legacy.now())
                if self.failed:
                    raise AuthenticationStopped("Authentication recovery stopped")
                client = self.client
                self.active += 1
            try:
                return getattr(client, name)(**params)
            finally:
                with self.condition:
                    self.active -= 1
                    self.condition.notify_all()
        return query


class RenewableSDKCache(collect.SDKCache):
    """Preserve the original two-attempt ceiling, cache keys, and parameters."""

    def __init__(self, client: Any) -> None:
        self.renewable = RenewableClient(client)
        super().__init__(self.renewable)

    def get(self, method: str, params: dict[str, Any]) -> tuple[Any, Any]:
        if self.renewable.failed:
            raise AuthenticationStopped("Authentication recovery stopped")
        try:
            return super().get(method, params)
        except RuntimeError as exc:
            if "AUTHENTICATIONSTOPPED" in str(exc).upper():
                self.renewable.stop()
                raise AuthenticationStopped("Authentication renewal failed") from None
            if "UNAUTHENTICATED" not in str(exc).upper():
                raise
            key = collect.request_key(method, params)
            with self.lock:
                remaining = self.attempts.get(key, 0) < 2
                self.cache.record({"status": "auth_refresh_requested", "method": method,
                                   "key": key, "retry_within_ceiling": remaining})
            if not remaining:
                self.renewable.stop()
                raise AuthenticationStopped("Authentication failed at attempt ceiling") from None
            self.renewable.invalidate()
            try:
                return super().get(method, params)
            except RuntimeError as retry_exc:
                if any(code in str(retry_exc).upper() for code in
                       ["UNAUTHENTICATED", "AUTHENTICATIONSTOPPED"]):
                    self.renewable.stop()
                    raise AuthenticationStopped("Authentication recovery failed") from None
                raise


if __name__ == "__main__":
    collect.SDKCache = RenewableSDKCache
    collect.options()
