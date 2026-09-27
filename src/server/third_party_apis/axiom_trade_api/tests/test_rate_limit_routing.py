import asyncio
import unittest

from third_party_apis.axiom_trade_api.agent_selector import AgentSelector
from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from third_party_apis.axiom_trade_api.request_pacer import AxiomRequestPacer
from third_party_apis.axiom_trade_api.endpoints.exceptions import (
    AxiomHTTPStatusError,
    AxiomRequestError,
)
from third_party_apis.axiom_trade_api.models.auth import AxiomAgentData


def _agent(number: int, proxy: str) -> AxiomAgentData:
    return AxiomAgentData.create_with_flat_params(
        user_agent=f"test-agent/{number}",
        auth_refresh_token=f"refresh-token-{number}",
        proxy=proxy,
        agent_name=f"agent-{number}",
    )


class AgentSelectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_reservations_are_balanced_by_proxy(self) -> None:
        selector = AgentSelector()
        selector.add_agents([
            _agent(1, "socks5://proxy-1"),
            _agent(2, "socks5://proxy-2"),
            _agent(3, "socks5://proxy-3"),
        ])

        selected = [selector.acquire_agent() for _ in range(6)]
        self.assertNotIn(None, selected)

        route_counts: dict[str, int] = {}
        for session_and_agent in selected:
            route = selector.route_key(session_and_agent)
            route_counts[route] = route_counts.get(route, 0) + 1

        self.assertEqual(set(route_counts.values()), {2})

        await self._close_selector(selector)

    async def test_agents_with_same_proxy_share_one_route_load(self) -> None:
        selector = AgentSelector()
        selector.add_agents([
            _agent(1, "socks5://shared-proxy"),
            _agent(2, "socks5://shared-proxy"),
            _agent(3, "socks5://other-proxy"),
        ])

        selected = [selector.acquire_agent() for _ in range(2)]
        routes = {
            selector.route_key(session_and_agent)
            for session_and_agent in selected
        }

        self.assertEqual(routes, {
            "socks5://shared-proxy",
            "socks5://other-proxy",
        })

        await self._close_selector(selector)

    async def test_sequential_requests_rotate_between_proxies(self) -> None:
        selector = AgentSelector()
        selector.add_agents([
            _agent(1, "socks5://proxy-1"),
            _agent(2, "socks5://proxy-2"),
            _agent(3, "socks5://proxy-3"),
        ])

        routes = []
        for _ in range(6):
            selected = selector.acquire_agent()
            routes.append(selector.route_key(selected))
            selector.release_agent(selected)

        self.assertEqual(routes, [
            "socks5://proxy-1",
            "socks5://proxy-2",
            "socks5://proxy-3",
            "socks5://proxy-1",
            "socks5://proxy-2",
            "socks5://proxy-3",
        ])

        await self._close_selector(selector)

    @staticmethod
    async def _close_selector(selector: AgentSelector) -> None:
        for session, _ in selector.get_agents_and_sessions():
            await session.close()


class AxiomTradeClientRetryTests(unittest.IsolatedAsyncioTestCase):
    async def test_shared_http_concurrency_limit_under_burst(self) -> None:
        client = AxiomTradeClient([_agent(1, "socks5://proxy-1")])
        client._request_pacer = AxiomRequestPacer(interval_seconds=0)
        in_flight = 0
        peak = 0

        async def endpoint(session_and_agent, **kwargs):
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1
            return "ok"

        try:
            results = await asyncio.gather(*[
                client._call_with_random_agent(endpoint) for _ in range(20)
            ])
        finally:
            await client.close()

        self.assertEqual(results, ["ok"] * 20)
        self.assertEqual(peak, 15)

    async def test_single_route_waits_for_retry_after_before_retry(self) -> None:
        client = AxiomTradeClient([_agent(1, "socks5://proxy-1")])
        starts: list[float] = []

        async def endpoint(session_and_agent, **kwargs):
            starts.append(asyncio.get_running_loop().time())
            if len(starts) == 1:
                raise AxiomHTTPStatusError(
                    "rate limited", status_code=429, retry_after=0.05
                )
            return "ok"

        try:
            result = await client._call_with_random_agent(endpoint)
        finally:
            await client.close()

        self.assertEqual(result, "ok")
        self.assertEqual(len(starts), 2)
        self.assertGreaterEqual(starts[1] - starts[0], 0.05)
        self.assertEqual(client._http_attempts["endpoint"], 2)
        self.assertEqual(client._http_rate_limits["endpoint"], 1)

    async def test_network_error_is_retried_through_another_proxy(self) -> None:
        client = AxiomTradeClient([
            _agent(1, "socks5://proxy-1"),
            _agent(2, "socks5://proxy-2"),
        ])
        called_routes: list[str] = []

        async def endpoint(session_and_agent, **kwargs):
            route = client._agent_selector.route_key(session_and_agent)
            called_routes.append(route)
            if len(called_routes) == 1:
                raise AxiomRequestError("proxy connection failed")
            return "ok"

        try:
            result = await client._call_with_random_agent(endpoint)
        finally:
            await client.close()

        self.assertEqual(result, "ok")
        self.assertEqual(len(called_routes), 2)
        self.assertNotEqual(called_routes[0], called_routes[1])

    async def test_429_is_retried_through_another_proxy(self) -> None:
        client = AxiomTradeClient([
            _agent(1, "socks5://proxy-1"),
            _agent(2, "socks5://proxy-2"),
        ])
        called_routes: list[str] = []

        async def endpoint(session_and_agent, **kwargs):
            route = client._agent_selector.route_key(session_and_agent)
            called_routes.append(route)
            if len(called_routes) == 1:
                raise AxiomHTTPStatusError(
                    "rate limited",
                    status_code=429,
                    retry_after=0,
                )
            return "ok"

        try:
            result = await client._call_with_random_agent(endpoint)
        finally:
            await client.close()

        self.assertEqual(result, "ok")
        self.assertEqual(len(called_routes), 2)
        self.assertNotEqual(called_routes[0], called_routes[1])


if __name__ == "__main__":
    unittest.main()
