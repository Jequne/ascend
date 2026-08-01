import logging
from typing import Optional, Dict, TypeVar, Type, Tuple
from curl_cffi import AsyncSession
import random
from pydantic import ValidationError

from ..auth.auth_manager import AuthManager
from ..models.auth import AxiomAgentData
from ..models.endpoints.pair_chart_v2 import PairChartV2Params, PairChartV2Response
from ..models.endpoints.dev_tokens_v3 import DevTokensV3Response
from ..models.endpoints.token_info import TokenInfoResponse
from ..models.endpoints.pair_info import PairInfoResponse
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logger = logging.getLogger(__name__)
ResponseModelT = TypeVar("ResponseModelT")


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
            auth_manager: AuthManager
            ):
        self._auth_manager = auth_manager
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def __get_request(
            self, 
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            url: str
            ):
        session = session_and_agent[0]
        agent_data = session_and_agent[1]
        try:
            return await session.get(
                url=url,
                headers=agent_data.headers.model_dump(by_alias=True),
                cookies=agent_data.cookies.get_cookies_for_request(),
                timeout=15,
                impersonate="chrome136",
                proxy=agent_data.proxy,
                # proxy="http://ygnglpau:1pm7voouokdc@45.159.55.132:6504"
            )

        except Exception as e:
            logger.warning(
                "❌ %s problem with request: %s",
                agent_data.agent_name, e
            )
            return

    async def __get_response_model(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            url: str,
            response_model: Type[ResponseModelT],
            endpoint_name: str,
            ) -> Optional[ResponseModelT]:
        if not await self._auth_manager.ensure_validation(session_and_agent):
            return

        response = await self.__get_request(session_and_agent, url)
        if not response:
            return

        if response.status_code != 200:
            logger.warning(
                "🟨 %s status code for %s: %s\n"
                "url for request: %s\n",
                session_and_agent[1].agent_name,
                endpoint_name,
                response.status_code,
                url
            )
            return

        json_data: Dict = response.json()
        logger.debug(
            "✅ %s %s response summary: %s",
            session_and_agent[1].agent_name,
            endpoint_name,
            _response_summary(json_data),
        )
        try:
            return response_model(**json_data)

        except ValidationError:
            logger.warning("⚠️ validating %s response problem", endpoint_name)
            return

    async def pair_chart_v2(
            self, 
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            pair_chart_v2_params: PairChartV2Params
            ) -> Optional[PairChartV2Response]:
        logger.debug(
            "pair_chart_v2 params string: \n%s",
            pair_chart_v2_params.to_http_query_string()
            )

        url = self._base_url + AxiomTradeApiUrls.PAIR_CHART_V2 + \
            pair_chart_v2_params.to_http_query_string()
        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=PairChartV2Response,
            endpoint_name="pair_chart_v2",
        )

    async def dev_tokens_v3(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            dev_address: str
            ) -> Optional[DevTokensV3Response]:
        url = self._base_url + AxiomTradeApiUrls.DEV_TOKENS_V5 + dev_address
        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=DevTokensV3Response,
            endpoint_name="dev_tokens_v5",
        )

    async def token_info(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            pair_address: str
            ) -> Optional[TokenInfoResponse]:
        url = self._base_url + AxiomTradeApiUrls.TOKEN_INFO + pair_address
        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=TokenInfoResponse,
            endpoint_name="token_info",
        )

    async def pair_info(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
            pair_address: str
        ) -> Optional[PairInfoResponse]:
        url = self._base_url + AxiomTradeApiUrls.PAIR_INFO + pair_address
        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=PairInfoResponse,
            endpoint_name="pair_info",
        )

    async def server_time(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData],
        ) -> Optional[PairInfoResponse]:
        url = "https://api.axiom.trade/wo/server-time"
        return await self.__get_request(
            session_and_agent=session_and_agent,
            url=url
        )

    async def get_announcment(
            self,
            session_and_agent: Tuple[AsyncSession, AxiomAgentData]
            ) -> Optional[PairInfoResponse]:
        url = "https://api6.axiom.trade/get-announcement?"
        return await self.__get_request(
            session_and_agent=session_and_agent,
            url=url
        )
