import logging
import random
from typing import List

from .models.auth import AxiomAgentData


logger = logging.getLogger(__name__)


class AgentSelector:
    def __init__(self):
        self._agents: List[AxiomAgentData] = []

    def add_agents(self, agents: List[AxiomAgentData]) -> None:
        self._agents.extend(agents)

    def require_agents(self) -> None:
        if not self._agents:
            raise Exception("🟨 No agents configured. Use add_agents() first")

    def random_agent(self) -> AxiomAgentData:
        self.require_agents()
        return random.choice(self._agents)

    def random_websocket_agent(self) -> AxiomAgentData:
        self.require_agents()

        has_any_proxy = any(agent.proxy for agent in self._agents)
        socks5_agents = [
            agent for agent in self._agents
            if agent.proxy and agent.proxy.startswith("socks5")
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

        return random.choice(self._agents)