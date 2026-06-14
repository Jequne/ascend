import logging
import random
from typing import Sequence, List, Tuple
from curl_cffi import AsyncSession

from .models.auth import AxiomAgentData


logger = logging.getLogger(__name__)


class AgentSelector:
    def __init__(self) -> None:
        self._agents_and_sessions: list[Tuple[AsyncSession, AxiomAgentData]] = []

    def add_agents(self, agents: Sequence[AxiomAgentData]) -> None:
        for agent in agents:
            session = AsyncSession()
            agent_and_session = (session, agent)

            self._agents_and_sessions.append(agent_and_session)

    def require_agents(self) -> None:
        if not self._agents_and_sessions:
            raise Exception("🟨 No agents configured. Use add_agents() first")

    def random_agent(self) -> Tuple[AsyncSession, AxiomAgentData]:
        self.require_agents()
        return random.choice(self._agents_and_sessions)

    def random_websocket_agent(self) -> Tuple[AsyncSession, AxiomAgentData]:
        self.require_agents()

        has_any_proxy = any(
            agent_and_session[1].proxy for agent_and_session in self._agents_and_sessions
            )
        socks5_agents = [
            agent_and_session for agent_and_session in self._agents_and_sessions
            if agent_and_session[1].proxy and agent_and_session[1].proxy.startswith("socks5")
        ]

        if socks5_agents:
            logger.info("✅ Using agents with SOCKS5 proxy")
            return random.choice(socks5_agents)

        if has_any_proxy:
            logger.warning(
                "🟨 Proxy configured, but no SOCKS5 agents available; falling back to all agents"
            )
        else:
            logger.info("✅ No proxy configured; using all agents")

        return random.choice(self._agents_and_sessions)
    
    def get_agents_and_sessions(self) -> list[Tuple[AsyncSession, AxiomAgentData]]:
        return self._agents_and_sessions