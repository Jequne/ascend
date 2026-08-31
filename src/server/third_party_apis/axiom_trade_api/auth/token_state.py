import logging
from datetime import datetime

import jwt

from .exceptions import AxiomAccessTokenError
from ..models.auth import AxiomAgentData, AxiomCookie


logger = logging.getLogger(__name__)


class AuthTokenStateService:
    def save_access_token(
        self,
        agent_data: AxiomAgentData,
        auth_access_token: str,
    ) -> None:
        try:
            decoded_auth_access_token = jwt.decode(
                jwt=auth_access_token,
                algorithms=["HS256"],
                options={"verify_signature": False},
            )
        except jwt.PyJWTError as exc:
            raise AxiomAccessTokenError(
                f"{agent_data.agent_name}: failed to decode access token"
            ) from exc

        try:
            expires_at: int = decoded_auth_access_token["exp"]
        except KeyError as exc:
            raise AxiomAccessTokenError(
                f"{agent_data.agent_name}: access token does not contain exp claim"
            ) from exc

        agent_data.cookies.auth_access_token = AxiomCookie(
            cookie=auth_access_token,
            expires_at=expires_at,
        )

        logger.debug(
            "%s access token state saved, expires_at=%s",
            agent_data.agent_name,
            expires_at,
        )

    def is_auth_access_token_valid(
        self,
        agent_data: AxiomAgentData,
        token_alive_gap: int = 120,
    ) -> bool:
        access_token = agent_data.cookies.auth_access_token

        if not access_token:
            return False

        expires_at = access_token.expires_at

        if not expires_at:
            return False

        current_time = int(datetime.now().timestamp())

        return expires_at - current_time >= token_alive_gap