import logging
import asyncio
from typing import Optional, Dict, Tuple
from curl_cffi import AsyncSession


from ..models.auth import AxiomAgentData
from .refresh_client import AuthRefreshClient
from .token_state import AuthTokenStateService


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self) -> None:
        self._refresh_client = AuthRefreshClient()
        self._token_state_service = AuthTokenStateService()
        self._agent_locks: Dict[str, asyncio.Lock] = {}

    def _get_agent_lock(self, auth_refresh_token: str) -> asyncio.Lock:
        lock = self._agent_locks.get(auth_refresh_token)
        if lock is None:
            lock = asyncio.Lock()
            self._agent_locks[auth_refresh_token] = lock
        return lock

    async def _refresh_auth_access_token(
            self, 
            session_and_agent: Tuple[AsyncSession, AxiomAgentData]
            ) -> Optional[str]:
        return await self._refresh_client.refresh_access_token(session_and_agent)
            
    def _save_access_token_age(
            self, 
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            auth_access_token: Optional[str]
            ) -> None:
        self._token_state_service.save_access_token(
            agent_data=session_and_agent[1],
            auth_access_token=auth_access_token,
        )

    async def _is_auth_access_token_valid(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            token_alive_gap: int = 120
            ) -> bool:
        return self._token_state_service.is_auth_access_token_valid(
            agent_data=session_and_agent[1],
            token_alive_gap=token_alive_gap,
        )
        
    async def ensure_validation(
            self, 
            session_and_agent: Tuple[AsyncSession, AxiomAgentData]
            ) -> bool:
        auth_refresh_token = session_and_agent[1].cookies.auth_refresh_token.cookie
        agent_lock = self._get_agent_lock(auth_refresh_token)

        async with agent_lock:
            is_access_token_valid = \
                await self._is_auth_access_token_valid(session_and_agent)
            
            if is_access_token_valid:
                return True
            
            auth_access_token = \
                await self._refresh_auth_access_token(session_and_agent)
            
            self._save_access_token_age(session_and_agent, auth_access_token)
            return await self._is_auth_access_token_valid(session_and_agent)
            


    
            
            
    
        
    

            
    
            
        