import random
import logging
import cloudscraper
import asyncio
from requests import Response
import jwt
from typing import Optional, Dict, Set
from datetime import datetime


from ..models.auth import AxiomAgentData, AxiomCookie
from ..urls import AAllBaseUrls, AxiomTradeApiUrls


FORMAT = "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="%d.%m.%Y %H:%M:%S"
)
logger = logging.getLogger(__name__)


class AuthManager:
    def __init__(self):
        self._scraper = cloudscraper.create_scraper(
            browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
        )
        self._base_url = random.choice(AAllBaseUrls.URLS)

    async def refresh_auth_access_token(
            self, 
            agent_data: AxiomAgentData
            ) -> Optional[str]:
        url = self._base_url + AxiomTradeApiUrls.REFRESH_TOKEN

        try:
            response = await asyncio.to_thread(
                self._scraper.post,
                url=url,
                headers=agent_data.headers.model_dump(by_alias=True),
                cookies=agent_data.cookies.get_cookies_for_request(),
                timeout=15
                # proxy=agent_data.proxy,
            )
            if response.status_code == 200:
                logger.info(
                    "✅ %s access token refreshed", agent_data.agent_name
                    )
                auth_access_token = \
                    response.cookies.get("auth-access-token", None)

                if auth_access_token:
                    return auth_access_token
                else:
                    logger.warning(
                    "✅ access token refreshed"
                    "The response did not contain " \
                    "the auth-access-token cookie. " \
                    "Perhaps her name has changed at axiom trade api"
                    )
                    return 
            else:
                logger.warning(
                    "❌ refresh auth access token response: %s", 
                    response.status_code
                )
                return 

        except Exception as e:
            logger.warning(
                "❌ %s access token not refreshed. Problem: %s",
                agent_data.agent_name, e
                )
            return 
            
    def _save_access_token_age(
            self, 
            agent_data: AxiomAgentData,
            auth_access_token: Optional[str]
            ) -> None:
        if not auth_access_token:
            logger.debug(
                "❌ auth_access_token " \
                "not saved in self._auth_access_tokens_age " \
                "because its None"
                )
            return None
        
        decoded_auth_access_token = jwt.decode(
            jwt=auth_access_token,
            algorithms=["HS256"],
            options={"verify_signature": False}
        )

        expires_at: int = decoded_auth_access_token["exp"]

        agent_auth_access_token: AxiomCookie = AxiomCookie(
            cookie=auth_access_token,
            expires_at=expires_at
        )

        agent_data_cookies = agent_data.cookies
        agent_data_cookies.auth_access_token = agent_auth_access_token

        logger.debug(
            "✅ %s access token age (%s) saved "
            "in self._auth_access_tokens_age",
            agent_data.agent_name, 
            expires_at
            )
        return

    async def _is_auth_access_token_valid(
            self,
            agent_data: AxiomAgentData,
            token_alive_gap: int = 120
            ) -> bool:
        access_token = agent_data.cookies.auth_access_token
        if not access_token:
            logger.warning(
                "🟨 %s don't have auth_access_token",
                agent_data.agent_name
                )
            return False

        auth_access_token_expired_at = access_token.expires_at
        
        if not auth_access_token_expired_at:
            logger.warning(
                "🟨 %s don't have auth_access_token", 
                agent_data.agent_name
                )
            return False

        current_time = int(datetime.now().timestamp())

        if auth_access_token_expired_at - current_time < token_alive_gap:
            logger.debug(
                "🟨 %s auth_access_token is expired", 
                agent_data.agent_name
                )
            return False
        else:
            logger.debug("✅ %s auth_access_token is valid", agent_data.agent_name)
            return True
        
    
    
            
            
    
        
    

            
    
            
        