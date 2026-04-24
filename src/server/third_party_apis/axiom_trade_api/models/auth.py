from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, TypedDict
from datetime import datetime, timedelta
import time


class AxiomHttpRequestContext(TypedDict, total=False):
    headers: Dict[str, str]
    cookies: Dict[str, str]
    proxy: str


class AxiomHeaders(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    user_agent: str = Field(..., alias="User-Agent")


class AxiomCookie(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")
    
    cookie: str
    expires_at: Optional[int] = Field(None, alias="exp")


class AxiomCookies(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    auth_refresh_token: AxiomCookie = Field(..., alias="auth-refresh-token")
    auth_access_token: Optional[AxiomCookie] = Field(
        None, 
        alias="auth-access-token"
        )

    @model_validator(mode="after")
    def set_refresh_token_expiry(self) -> "AxiomCookies":
        if self.auth_refresh_token and not self.auth_refresh_token.expires_at:
            expires_at = datetime.now() + timedelta(days=90)
            self.auth_refresh_token.expires_at = int(expires_at.timestamp())
        elif self.auth_refresh_token.expires_at < time.time():
            raise ValueError("auth_refresh_token already expired")
        return self

    def get_cookies_for_request(self) -> Dict[str, str]:
        cookies: Dict[str, str] = {}

        for field_name, field_info in self.__class__.model_fields.items():
            cookie_obj = getattr(self, field_name)

            if cookie_obj is None:
                continue
            if not isinstance(cookie_obj, AxiomCookie):
                continue
            if not cookie_obj.cookie:
                continue

            cookie_name = field_info.alias or field_name
            cookies[cookie_name] = cookie_obj.cookie

        return cookies


class AxiomAgentData(BaseModel):
    agent_name: str = Field(
        default="unnamed agent", 
        description="Agent num (for example axiom_api_agent_1)"
        )
    headers: AxiomHeaders = Field(...)
    cookies: AxiomCookies = Field(...)
    proxy: Optional[str] = Field(None, description="proxy for agent")

    @classmethod
    def create_with_flat_params(
        cls,
        user_agent: str,
        auth_refresh_token: str,
        auth_access_token: Optional[str] = None,
        proxy: Optional[str] = None,
        agent_name: str = "unnamed agent",
    ) -> "AxiomAgentData":
        return cls(
            agent_name=agent_name,
            headers=AxiomHeaders(user_agent=user_agent),
            cookies=AxiomCookies(
                auth_refresh_token=AxiomCookie(cookie=auth_refresh_token),
                auth_access_token=(
                    AxiomCookie(cookie=auth_access_token) \
                    if auth_access_token else None
                ),
            ),
            proxy=proxy,
        )

    def get_http_request_context(self) -> AxiomHttpRequestContext:
        context: AxiomHttpRequestContext = {
            "headers": self.headers.model_dump(by_alias=True),
            "cookies": self.cookies.get_cookies_for_request(),
        }

        if self.proxy:
            context["proxy"] = self.proxy

        return context


