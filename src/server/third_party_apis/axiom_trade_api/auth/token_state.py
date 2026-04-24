import logging
from datetime import datetime
from typing import Optional

import jwt

from ..models.auth import AxiomAgentData, AxiomCookie


logger = logging.getLogger(__name__)


class AuthTokenStateService:
    def save_access_token(
            self,
            agent_data: AxiomAgentData,
            auth_access_token: Optional[str],
            ) -> None:
        if not auth_access_token:
            logger.debug(
                "❌ auth_access_token "
                "not saved in self._auth_access_tokens_age "
                "because its None"
            )
            return

        decoded_auth_access_token = jwt.decode(
            jwt=auth_access_token,
            algorithms=["HS256"],
            options={"verify_signature": False},
        )

        expires_at: int = decoded_auth_access_token["exp"]

        agent_auth_access_token: AxiomCookie = AxiomCookie(
            cookie=auth_access_token,
            expires_at=expires_at,
        )

        agent_data_cookies = agent_data.cookies
        agent_data_cookies.auth_access_token = agent_auth_access_token

        logger.debug(
            "✅ %s access token age (%s) saved "
            "in self._auth_access_tokens_age",
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

        auth_access_token_expired_at = access_token.expires_at
        if not auth_access_token_expired_at:
            return False

        current_time = int(datetime.now().timestamp())
        return auth_access_token_expired_at - current_time >= token_alive_gap