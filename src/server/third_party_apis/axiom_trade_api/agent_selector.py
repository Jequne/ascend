import logging
import random
import time
from typing import Sequence, Tuple
from curl_cffi import AsyncSession

from .models import AxiomAgentData


logger = logging.getLogger(__name__)


class AgentSelector:
    def __init__(self) -> None:
        self._agents_and_sessions: list[
            Tuple[AsyncSession, AxiomAgentData]
        ] = []
        self._in_flight: dict[int, int] = {}
        self._rate_limited_until: dict[str, float] = {}
        self._route_cursor = 0
        self._agent_cursors: dict[str, int] = {}

    def add_agents(self, agents: Sequence[AxiomAgentData]) -> None:
        for agent in agents:
            session = AsyncSession()
            agent_and_session = (session, agent)

            self._agents_and_sessions.append(agent_and_session)
            self._in_flight[id(agent)] = 0

    def require_agents(self) -> None:
        if not self._agents_and_sessions:
            raise Exception("No agents configured. Use add_agents() first")

    def random_agent(self) -> Tuple[AsyncSession, AxiomAgentData]:
        self.require_agents()
        return random.choice(self._agents_and_sessions)

    @staticmethod
    def route_key(
        session_and_agent: Tuple[AsyncSession, AxiomAgentData]
    ) -> str:
        agent = session_and_agent[1]
        # Agents without an explicit proxy still share the server's public IP.
        return agent.proxy or "__direct__"

    @property
    def route_count(self) -> int:
        self.require_agents()
        return len({
            self.route_key(session_and_agent)
            for session_and_agent in self._agents_and_sessions
        })

    def acquire_agent(
        self,
        excluded_routes: set[str] | None = None,
    ) -> Tuple[AsyncSession, AxiomAgentData] | None:
        """Reserve the least busy available proxy route and agent."""
        self.require_agents()
        excluded_routes = excluded_routes or set()
        now = time.monotonic()

        available = [
            session_and_agent
            for session_and_agent in self._agents_and_sessions
            if self.route_key(session_and_agent) not in excluded_routes
            and self._rate_limited_until.get(
                self.route_key(session_and_agent), 0.0
            ) <= now
        ]
        if not available:
            return None

        route_loads: dict[str, int] = {}
        for session_and_agent in self._agents_and_sessions:
            route = self.route_key(session_and_agent)
            route_loads[route] = route_loads.get(route, 0) + self._in_flight[
                id(session_and_agent[1])
            ]

        minimum_route_load = min(
            route_loads[self.route_key(session_and_agent)]
            for session_and_agent in available
        )
        least_busy_routes = list(dict.fromkeys(
            self.route_key(session_and_agent)
            for session_and_agent in available
            if route_loads[self.route_key(session_and_agent)]
            == minimum_route_load
        ))
        route = least_busy_routes[
            self._route_cursor % len(least_busy_routes)
        ]
        self._route_cursor += 1
        route_agents = [
            session_and_agent
            for session_and_agent in available
            if self.route_key(session_and_agent) == route
        ]
        minimum_agent_load = min(
            self._in_flight[id(session_and_agent[1])]
            for session_and_agent in route_agents
        )
        least_busy_agents = [
            session_and_agent
            for session_and_agent in route_agents
            if self._in_flight[id(session_and_agent[1])]
            == minimum_agent_load
        ]
        agent_cursor = self._agent_cursors.get(route, 0)
        selected = least_busy_agents[agent_cursor % len(least_busy_agents)]
        self._agent_cursors[route] = agent_cursor + 1
        self._in_flight[id(selected[1])] += 1
        return selected

    def release_agent(
        self,
        session_and_agent: Tuple[AsyncSession, AxiomAgentData],
    ) -> None:
        agent_key = id(session_and_agent[1])
        self._in_flight[agent_key] = max(
            0, self._in_flight.get(agent_key, 0) - 1
        )

    def mark_rate_limited(
        self,
        session_and_agent: Tuple[AsyncSession, AxiomAgentData],
        retry_after: float | None,
    ) -> None:
        route = self.route_key(session_and_agent)
        cooldown = retry_after if retry_after is not None else 0.5
        self._rate_limited_until[route] = max(
            self._rate_limited_until.get(route, 0.0),
            time.monotonic() + cooldown,
        )

    def next_available_delay(
        self,
        excluded_routes: set[str] | None = None,
    ) -> float:
        excluded_routes = excluded_routes or set()
        now = time.monotonic()
        waits = [
            max(
                0.0,
                self._rate_limited_until.get(
                    self.route_key(session_and_agent), 0.0
                ) - now,
            )
            for session_and_agent in self._agents_and_sessions
            if self.route_key(session_and_agent) not in excluded_routes
        ]
        return min(waits, default=0.0)

    def random_websocket_agent(self) -> Tuple[AsyncSession, AxiomAgentData]:
        self.require_agents()

        has_any_proxy = any(
            agent_and_session[1].proxy for agent_and_session \
                in self._agents_and_sessions
            )
        socks5_agents = [
            agent_and_session for agent_and_session in self._agents_and_sessions
            if agent_and_session[1].proxy \
                and agent_and_session[1].proxy.startswith("socks5")
        ]

        if socks5_agents:
            logger.info("Using agents with SOCKS5 proxy")
            return random.choice(socks5_agents)

        if has_any_proxy:
            logger.warning(
                "Proxy configured, but no SOCKS5 agents available; " \
                "falling back to all agents"
            )
        else:
            logger.info("No proxy configured; using all agents")

        return random.choice(self._agents_and_sessions)
    
    def get_agents_and_sessions(self) -> list[
        Tuple[AsyncSession, AxiomAgentData]
    ]:
        return self._agents_and_sessions
