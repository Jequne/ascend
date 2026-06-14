import asyncio
import logging
import random
from typing import Any, Optional, Tuple

import cloudscraper
from curl_cffi import AsyncSession

from ..models.auth import AxiomAgentData, AxiomCookie
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


logger = logging.getLogger(__name__)


class AuthRefreshClient:
    def __init__(self) -> None:
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def refresh_access_token(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            ) -> Optional[str]:
        session = session_and_agent[0]
        agent_data = session_and_agent[1]

        url = self._base_url + AxiomTradeApiUrls.REFRESH_TOKEN
        request_kwargs: dict[str, Any] = dict(
            url=url,
            headers=agent_data.headers.model_dump(by_alias=True),
            cookies=agent_data.cookies.get_cookies_for_request(),
            timeout=15,
        )

        if agent_data.proxy:
            logger.debug(
                "✅ %s refresh request using proxy: %s",
                agent_data.agent_name,
                agent_data.proxy,
            )
            # request_kwargs["proxies"] = {
            #     "http": agent_data.proxy,
            #     "https": agent_data.proxy,
            # }
            request_kwargs["proxy"] = agent_data.proxy

        try:
            # response = await asyncio.to_thread(
            #     self._scraper.post,
            #     **request_kwargs,
            # )

            response = await session.post(
                **request_kwargs,
                impersonate="chrome136"
            )

            self._save_cf_cookies_for_agent(axiom_agent=agent_data, session=session)

            if response.status_code == 200:
                logger.info(
                    "✅ %s access token refreshed", agent_data.agent_name
                )
                auth_access_token = response.cookies.get("auth-access-token", None)

                if auth_access_token:
                    return auth_access_token

                logger.warning(
                    "✅ access token refreshed"
                    "The response did not contain "
                    "the auth-access-token cookie. "
                    "Perhaps her name has changed at axiom trade api"
                )
                return

            logger.warning(
                "🟨 refresh auth access token response: %s",
                response.status_code,
            )
            return

        except Exception as e:
            logger.warning(
                "❌ %s access token not refreshed. Problem: %s",
                agent_data.agent_name,
                e,
            )
            return
        
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
        
