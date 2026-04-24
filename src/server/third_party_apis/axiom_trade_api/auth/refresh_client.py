import asyncio
import logging
import random
from typing import Optional

import cloudscraper

from ..models.auth import AxiomAgentData
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


logger = logging.getLogger(__name__)


class AuthRefreshClient:
    def __init__(self):
        self._scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            }
        )
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def refresh_access_token(
            self,
            agent_data: AxiomAgentData,
            ) -> Optional[str]:
        url = self._base_url + AxiomTradeApiUrls.REFRESH_TOKEN
        request_kwargs = dict(
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
            request_kwargs["proxies"] = {
                "http": agent_data.proxy,
                "https": agent_data.proxy,
            }

        try:
            response = await asyncio.to_thread(
                self._scraper.post,
                **request_kwargs,
            )
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