import logging
import random
from typing import Any

from curl_cffi import AsyncSession

from ..models.auth import AxiomAgentData, AxiomCookie
from ..urls import AAllBaseUrls, AxiomTradeApiUrls
from .exceptions import AxiomRefreshTokenError


logger = logging.getLogger(__name__)


class AuthRefreshClient:
    def __init__(self) -> None:
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def refresh_access_token(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
    ) -> str:
        session, agent_data = session_and_agent

        url = self._base_url + AxiomTradeApiUrls.REFRESH_TOKEN

        request_kwargs: dict[str, Any] = {
            "url": url,
            "headers": agent_data.headers.model_dump(by_alias=True),
            "cookies": agent_data.cookies.get_cookies_for_request(),
            "timeout": 15,
        }

        if agent_data.proxy:
            logger.debug(
                "%s refresh request using proxy",
                agent_data.agent_name,
            )
            request_kwargs["proxy"] = agent_data.proxy

        try:
            response = await session.post(
                **request_kwargs,
                impersonate="chrome136",
            )
        except Exception as exc:
            raise AxiomRefreshTokenError(
                f"{agent_data.agent_name}: refresh request failed"
            ) from exc

        self._save_cf_cookies_for_agent(
            axiom_agent=agent_data,
            session=session,
        )

        if response.status_code != 200:
            raise AxiomRefreshTokenError(
                f"{agent_data.agent_name}: "
                f"refresh failed with status {response.status_code}"
            )

        auth_access_token = response.cookies.get("auth-access-token")

        if not auth_access_token:
            raise AxiomRefreshTokenError(
                f"{agent_data.agent_name}: "
                "response does not contain auth-access-token cookie"
            )

        logger.info(
            "%s access token refreshed",
            agent_data.agent_name,
        )

        return auth_access_token
        
    def _get_cookies_from_session(self, session: AsyncSession) -> dict:
        cookies = session.cookies.get_dict()
        return cookies
    
    def _save_cf_cookies_for_agent(
            self, 
            axiom_agent: AxiomAgentData,
            session: AsyncSession
            ) -> None:
        cf_cookies: dict = self._get_cookies_from_session(session)

        axiom_agent_cookies = axiom_agent.cookies
        for key, value in cf_cookies.items():
            cookie = AxiomCookie(cookie=value)
            axiom_agent_cookies.key = cookie

        logger.info(
            "✅ cf cookies for %s saved in state", 
            axiom_agent.agent_name
            )
        
