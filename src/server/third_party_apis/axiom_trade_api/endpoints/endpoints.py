import logging
import random
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Type, TypeVar

from curl_cffi import AsyncSession
from curl_cffi.requests import Response
from curl_cffi.requests.exceptions import RequestException
from pydantic import ValidationError

from ..auth import AuthManager
from .exceptions import *
from ..models import *
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


logger = logging.getLogger(__name__)

ResponseModelT = TypeVar("ResponseModelT")


def _get_retry_after_seconds(response: Response) -> float | None:
    retry_after = response.headers.get("Retry-After")
    if not retry_after:
        return None

    try:
        return max(0.0, float(retry_after))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(retry_after)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(
                0.0,
                (retry_at - datetime.now(timezone.utc)).total_seconds(),
            )
        except (TypeError, ValueError, OverflowError):
            return None


def _response_summary(json_data: dict) -> str:
    keys = sorted(json_data.keys())

    tokens = json_data.get("tokens")
    points = json_data.get("points")

    tokens_count = len(tokens) if isinstance(tokens, list) else None
    points_count = len(points) if isinstance(points, list) else None

    details = [f"keys={keys}"]

    if tokens_count is not None:
        details.append(f"tokens={tokens_count}")

    if points_count is not None:
        details.append(f"points={points_count}")

    return ", ".join(details)


class AxiomTradeEndpoints:
    def __init__(
        self,
        auth_manager: AuthManager,
    ) -> None:
        self._auth_manager = auth_manager
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def __get_request(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        url: str,
    ) -> Response:
        session, agent_data = session_and_agent

        try:
            return await session.get(
                url=url,
                headers=agent_data.headers.model_dump(by_alias=True),
                cookies=agent_data.cookies.get_cookies_for_request(),
                timeout=15,
                impersonate="chrome136",
                proxy=agent_data.proxy,
            )

        except RequestException as exc:
            raise AxiomRequestError(
                f"{agent_data.agent_name}: request failed: {url}"
            ) from exc

    async def __get_response_model(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        url: str,
        response_model: Type[ResponseModelT],
        endpoint_name: str,
    ) -> ResponseModelT:
        agent_data = session_and_agent[1]

        is_valid = await self._auth_manager.ensure_validation(
            session_and_agent
        )

        if not is_valid:
            raise AxiomApiError(
                f"{agent_data.agent_name}: authentication validation failed"
            )

        response = await self.__get_request(
            session_and_agent=session_and_agent,
            url=url,
        )

        if response.status_code != 200:
            raise AxiomHTTPStatusError(
                f"{agent_data.agent_name}: "
                f"{endpoint_name} returned status {response.status_code}",
                status_code=response.status_code,
                retry_after=_get_retry_after_seconds(response),
            )

        try:
            json_data: dict = response.json()

        except ValueError as exc:
            raise AxiomResponseError(
                f"{agent_data.agent_name}: "
                f"{endpoint_name} returned invalid JSON"
            ) from exc

        logger.debug(
            "%s %s response summary: %s",
            agent_data.agent_name,
            endpoint_name,
            _response_summary(json_data),
        )

        try:
            return response_model(**json_data)

        except ValidationError as exc:
            raise AxiomResponseValidationError(
                f"{agent_data.agent_name}: "
                f"{endpoint_name} response validation failed"
            ) from exc

    async def pair_chart_v2(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        pair_chart_v2_params: PairChartV2Params,
    ) -> PairChartV2Response:
        logger.debug(
            "pair_chart_v2 params string: %s",
            pair_chart_v2_params.to_http_query_string(),
        )

        url = (
            self._base_url
            + AxiomTradeApiUrls.PAIR_CHART_V2
            + pair_chart_v2_params.to_http_query_string()
        )

        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=PairChartV2Response,
            endpoint_name="pair_chart_v2",
        )

    async def dev_tokens_v3(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        dev_address: str,
    ) -> DevTokensV3Response:
        url = (
            self._base_url
            + AxiomTradeApiUrls.DEV_TOKENS_V5
            + dev_address
        )

        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=DevTokensV3Response,
            endpoint_name="dev_tokens_v5",
        )

    async def token_info(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        pair_address: str,
    ) -> TokenInfoResponse:
        url = (
            self._base_url
            + AxiomTradeApiUrls.TOKEN_INFO
            + pair_address
        )

        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=TokenInfoResponse,
            endpoint_name="token_info",
        )

    async def pair_info(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
        pair_address: str,
    ) -> PairInfoResponse:
        url = (
            self._base_url
            + AxiomTradeApiUrls.PAIR_INFO
            + pair_address
        )

        return await self.__get_response_model(
            session_and_agent=session_and_agent,
            url=url,
            response_model=PairInfoResponse,
            endpoint_name="pair_info",
        )

    async def server_time(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
    ) -> Response:
        url = "https://api.axiom.trade/wo/server-time"

        return await self.__get_request(
            session_and_agent=session_and_agent,
            url=url,
        )

    async def get_announcement(
        self,
        session_and_agent: tuple[AsyncSession, AxiomAgentData],
    ) -> Response:
        url = "https://api6.axiom.trade/get-announcement?"

        return await self.__get_request(
            session_and_agent=session_and_agent,
            url=url,
        )
