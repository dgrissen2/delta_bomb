"""Checks for SDK session renewal without making network calls."""
from concurrent.futures import ThreadPoolExecutor
import threading
import unittest
from unittest.mock import Mock, patch

from resume_collect import RenewableClient, RenewableSDKCache, AuthenticationStopped
import collect


class TransportTests(unittest.TestCase):
    def test_expiry_and_explicit_invalidation_refresh(self) -> None:
        class Client:
            def query(self, **params: object) -> dict[str, object]:
                return params
        clock = [0.0]
        refreshes = []
        client = RenewableClient(Client(), lambda: refreshes.append(1) or Client(),
                                 lambda: clock[0], ttl=300)
        self.assertEqual(client.query(value=1), {"value": 1})
        self.assertEqual(refreshes, [])
        clock[0] = 301
        self.assertEqual(client.query(value=2), {"value": 2})
        client.invalidate()
        client.query(value=3)
        self.assertEqual(len(refreshes), 2)
        client.stop()
        with self.assertRaises(AuthenticationStopped):
            client.query(value=4)

    def test_refresh_waits_for_active_request(self) -> None:
        entered, release = threading.Event(), threading.Event()
        refreshes = []

        class Client:
            def query(self, blocking: bool = False) -> str:
                if blocking:
                    entered.set()
                    if not release.wait(timeout=2):
                        raise RuntimeError("Test request not released")
                return "ok"

        def authenticate() -> Client:
            self.assertTrue(release.is_set())
            refreshes.append(1)
            return Client()

        client = RenewableClient(Client(), authenticate)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(client.query, blocking=True)
            self.assertTrue(entered.wait(timeout=2))
            client.invalidate()
            second = pool.submit(client.query)
            self.assertEqual(refreshes, [])
            release.set()
            self.assertEqual(first.result(timeout=2), "ok")
            self.assertEqual(second.result(timeout=2), "ok")
        self.assertEqual(refreshes, [1])

    def test_failed_authentication_stops_further_calls(self) -> None:
        def authenticate() -> None:
            raise RuntimeError("test auth failure")

        client = RenewableClient(object(), authenticate)
        client.invalidate()
        with self.assertRaises(AuthenticationStopped):
            client.query()
        with self.assertRaises(AuthenticationStopped):
            client.query()

    def test_cache_wrapped_auth_stop_remains_fatal(self) -> None:
        cache = object.__new__(RenewableSDKCache)
        cache.renewable = RenewableClient(object())
        with patch.object(collect.SDKCache, "get", Mock(side_effect=RuntimeError(
                "Theta option_history: AuthenticationStopped"))) as request:
            with self.assertRaises(AuthenticationStopped):
                cache.get("option_history", {})
            with self.assertRaises(AuthenticationStopped):
                cache.get("option_history", {})
            self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
