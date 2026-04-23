from curl_cffi import AsyncSession
from typing import List, Literal, Optional
import logging
import random
import asyncio

from .models.auth import AxiomAgentData
from .auth.auth_manager import AuthManager
from .endpoints.ws import AxiomTradeWebsocket
from .endpoints.endpoints import AxiomTradeEndpoints
from .models.endpoints.pair_chart_v2 import PairChartV2Params, PairChartV2Response
from .models.endpoints.dev_tokens_v3 import DevTokensV3Response
from .models.endpoints.token_info import TokenInfoResponse
from .models.endpoints.pair_info import PairInfoResponse


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="%d.%m.%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)


class AxiomTradeClient:
    def __init__(self, session: AsyncSession = None):
        self._session = session or AsyncSession()
        self._auth_manager = AuthManager()
        self._agents: List[AxiomAgentData] = []
        self._wsocket = AxiomTradeWebsocket(self._session, self._auth_manager)
        self._endpoints = AxiomTradeEndpoints(self._session, self._auth_manager)
        self._ws_task = None

    def add_agents(self, agents: List[AxiomAgentData]) -> None:
        self._agents.extend(agents)

    def _ensure_agents_configured(self) -> None:
        """Check that agents are added"""
        if not self._agents:
            raise Exception("🟨 No agents configured. Use add_agents() first")

    def _get_agents_with_socks5(self) -> List[AxiomAgentData]:
        """Get agents with SOCKS5 proxy, fallback to any agents if not available"""
        self._ensure_agents_configured()
        
        agents = [a for a in self._agents 
                  if a.proxy and a.proxy.startswith("socks5")]
        
        if agents:
            logger.info("✅ Using agents with SOCKS5 proxy")
            return agents
        
        logger.warning("🟨 No SOCKS5 agents available, falling back to all agents")
        return list(self._agents)

    def connect_websocket(
            self,
            rooms: List[Literal["new_pairs", "sol_price"]] = \
                ["new_pairs", "sol_price"]
            ) -> None:
        """Connect to WebSocket and run stream in background"""
        agents = self._get_agents_with_socks5()
        random_agent = random.choice(agents)
        
        self._ws_task = asyncio.create_task(
            self._wsocket.start(agent_data=random_agent, rooms=rooms)
        )
    
    def on_sol_price(self, callback) -> None:
        """Register callback for SOL price updates"""
        self._wsocket.register_callback("sol_price", callback)

    async def pair_chart_v2(
            self,
            pair_address: str,
            open_trading: int,
            last_transaction_time: int
            ) -> Optional[PairChartV2Response]:
        """Get chart data for a pair"""
        self._ensure_agents_configured()
        
        random_agent = random.choice(self._agents)
        pair_chart_v2_params = PairChartV2Params(
            pair_address=pair_address,
            open_trading=open_trading,
            last_transaction_time=last_transaction_time
        )
        
        return await self._endpoints.pair_chart_v2(
            agent_data=random_agent, 
            pair_chart_v2_params=pair_chart_v2_params
            )
    
    async def dev_tokens_v3(
            self,
            dev_address: str
    ) -> Optional[DevTokensV3Response]:
        self._ensure_agents_configured()

        random_agent = random.choice(self._agents)
        return await self._endpoints.dev_tokens_v3(
            agent_data=random_agent,
            dev_address=dev_address
        )
    
    async def token_info(
            self,
            pair_address: str
    ) -> Optional[TokenInfoResponse]:
        self._ensure_agents_configured()

        random_agent = random.choice(self._agents)
        return await self._endpoints.token_info(
            agent_data=random_agent,
            pair_address=pair_address
        )
    
    async def pair_info(
            self,
            pair_address: str
    ) -> Optional[PairInfoResponse]:
        self._ensure_agents_configured()

        random_agent = random.choice(self._agents)
        return await self._endpoints.pair_info(
            agent_data=random_agent,
            pair_address=pair_address
        )
    
    async def close(self) -> None:
        """Close all connections"""
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        await self._session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    



    
