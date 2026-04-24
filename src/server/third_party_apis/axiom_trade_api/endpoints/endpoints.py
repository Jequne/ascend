import logging
import asyncio
from typing import Optional, Dict, Set
from curl_cffi import AsyncSession
import random

from ..auth.auth_manager import AuthManager
from ..models.auth import AxiomAgentData
from ..models.endpoints.pair_chart_v2 import PairChartV2Params, PairChartV2Response
from ..models.endpoints.dev_tokens_v3 import DevTokensV3Response
from ..models.endpoints.token_info import TokenInfoResponse
from ..models.endpoints.pair_info import PairInfoResponse
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="%d.%m.%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)


def _response_summary(json_data: Dict) -> str:
    keys = sorted(json_data.keys())
    tokens_count = len(json_data.get("tokens", [])) if isinstance(json_data.get("tokens"), list) else None
    points_count = len(json_data.get("points", [])) if isinstance(json_data.get("points"), list) else None
    details = [f"keys={keys}"]
    if tokens_count is not None:
        details.append(f"tokens={tokens_count}")
    if points_count is not None:
        details.append(f"points={points_count}")
    return ", ".join(details)


class AxiomTradeEndpoints:
    def __init__(
            self, 
            async_http_session: AsyncSession,
            auth_manager: AuthManager
            ):
        self._async_http_session = async_http_session
        self._auth_manager = auth_manager
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def pair_chart_v2(
            self, 
            agent_data: AxiomAgentData,
            pair_chart_v2_params: PairChartV2Params
            ) -> Optional[PairChartV2Response]:
        if not await self._auth_manager.ensure_validation(agent_data):
            return
        logger.debug(
            "pair_chart_v2 params string: \n%s",
            pair_chart_v2_params.to_http_query_string()
            )
        
        url = self._base_url + AxiomTradeApiUrls.PAIR_CHART_V2 + \
            pair_chart_v2_params.to_http_query_string()
        
        try:
            response = await \
                self._async_http_session.get(
                    url=url,
                    headers=agent_data.headers.model_dump(by_alias=True),
                    cookies=agent_data.cookies.get_cookies_for_request(),
                    timeout=15,
                    impersonate="chrome124",
                    proxy=agent_data.proxy
                )
            
            if response.status_code == 200:
                json_data: Dict = response.json()
                logger.debug(
                    "✅ %s pair_chart_v2 response summary: %s",
                    agent_data.agent_name,
                    _response_summary(json_data),
                    )
                pair_chart_v2_response = PairChartV2Response(**json_data)
                return pair_chart_v2_response

            else:
                logger.warning(
                    "🟨 %s status code: %s\n",
                    agent_data.agent_name, 
                    response.status_code, 
                    )
                return
        
        except Exception as e:
            logger.warning(
                "❌ %s problem with request: %s",
                agent_data.agent_name, e
                )
            return
            
    async def dev_tokens_v3(
            self, 
            agent_data: AxiomAgentData, 
            dev_address: str
            ) -> Optional[DevTokensV3Response]:
        if not await self._auth_manager.ensure_validation(agent_data):
            return
        
        url = self._base_url + AxiomTradeApiUrls.DEV_TOKENS_V3 + dev_address

        try:
            response = await \
                self._async_http_session.get(
                    url=url,
                    headers=agent_data.headers.model_dump(by_alias=True),
                    cookies=agent_data.cookies.get_cookies_for_request(),
                    timeout=15,
                    impersonate="chrome124",
                    proxy=agent_data.proxy
                )
            
            if response.status_code == 200:
                json_data: Dict = response.json()
                logger.debug(
                    "✅ %s dev_tokens_v3 response summary: %s",
                    agent_data.agent_name,
                    _response_summary(json_data),
                    )
                dev_tokens_v3 = DevTokensV3Response(**json_data)
                return dev_tokens_v3

            else:
                logger.warning(
                    "🟨 %s status code: %s\n",
                    agent_data.agent_name, 
                    response.status_code, 
                    )
                return

        except Exception as e:
            logger.warning(
                "❌ %s problem with request: %s",
                agent_data.agent_name, e
                )
            return
        
    async def token_info(
            self, 
            agent_data: AxiomAgentData, 
            pair_address: str
            ) -> Optional[TokenInfoResponse]:
        if not await self._auth_manager.ensure_validation(agent_data):
            return
        
        url = self._base_url + AxiomTradeApiUrls.TOKEN_INFO + pair_address

        try:
            response = await \
                self._async_http_session.get(
                    url=url,
                    headers=agent_data.headers.model_dump(by_alias=True),
                    cookies=agent_data.cookies.get_cookies_for_request(),
                    timeout=15,
                    impersonate="chrome124",
                    proxy=agent_data.proxy
                )
            
            if response.status_code == 200:
                json_data: Dict = response.json()
                logger.debug(
                    "✅ %s token_info response summary: %s",
                    agent_data.agent_name,
                    _response_summary(json_data),
                    )
                token_info = TokenInfoResponse(**json_data)
                return token_info
            
            else:
                logger.warning(
                    "🟨 %s status code: %s\n",
                    agent_data.agent_name, 
                    response.status_code, 
                    )
                return

        except Exception as e:
            logger.warning(
                "❌ %s problem with request: %s",
                agent_data.agent_name, e
                )
            return

    async def pair_info(
            self,
            agent_data: AxiomAgentData,
            pair_address: str
        ) -> Optional[PairInfoResponse]:
        if not await self._auth_manager.ensure_validation(agent_data):
            return
        
        url = self._base_url + AxiomTradeApiUrls.PAIR_INFO + pair_address

        try:
            response = await \
                self._async_http_session.get(
                    url=url,
                    headers=agent_data.headers.model_dump(by_alias=True),
                    cookies=agent_data.cookies.get_cookies_for_request(),
                    timeout=15,
                    impersonate="chrome124",
                    proxy=agent_data.proxy
                )
            
            if response.status_code == 200:
                json_data: Dict = response.json()
                logger.debug(
                    "✅ %s pair_info response summary: %s",
                    agent_data.agent_name,
                    _response_summary(json_data),
                    )
                token_info = PairInfoResponse(**json_data)
                return token_info
            
            else:
                logger.warning(
                    "🟨 %s status code: %s\n",
                    agent_data.agent_name, 
                    response.status_code, 
                    )
                return

        except Exception as e:
            logger.warning(
                "❌ %s problem with request: %s",
                agent_data.agent_name, e
                )
            return

        
                




    

