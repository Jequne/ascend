"""Probe Axiom refresh responses without printing credentials or proxies."""

import argparse
import asyncio
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import jwt
from curl_cffi import AsyncSession
from curl_cffi.const import CurlHttpVersion
from curl_cffi.requests.impersonate import REAL_TARGET_MAP

from third_party_apis.axiom_trade_api.client import AxiomTradeClient
from third_party_apis.axiom_trade_api.models.auth import AxiomAgentData
from third_party_apis.axiom_trade_api.urls import (
    AAllBaseUrls,
    AxiomTradeApiUrls,
)


def _agents(path: Path) -> list[AxiomAgentData]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [AxiomAgentData.model_validate(item) for item in data]


def _labels(values: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for value in values:
        labels.setdefault(value, str(len(labels) + 1))
    return labels


def _route_labels(agents: list[AxiomAgentData]) -> dict[str, str]:
    routes = _labels([agent.proxy or "direct" for agent in agents])
    return {route: f"route-{label}" for route, label in routes.items()}


async def _probe(
    agent: AxiomAgentData, host: str, proxy: str | None = None
) -> str:
    async with AsyncSession() as session:
        try:
            response = await session.post(
                url=host + AxiomTradeApiUrls.REFRESH_TOKEN,
                headers=agent.headers.request_headers,
                cookies=agent.cookies.get_cookies_for_request(),
                timeout=15,
                impersonate="chrome136",
                proxy=proxy if proxy is not None else agent.proxy,
            )
        except Exception as exc:
            return f"transport-error:{type(exc).__name__}"
        rotated = response.cookies.get("auth-refresh-token")
        rotated_from_current = bool(
            rotated and rotated != agent.cookies.auth_refresh_token.cookie
        )
        server = response.headers.get("server", "unknown")
        content_type = response.headers.get("content-type", "unknown")
        cf_response = sorted(
            key
            for key in response.cookies.get_dict()
            if key == "cf_clearance" or key.startswith("__cf_")
        )
        cf_session = sorted(
            key
            for key in session.cookies.get_dict()
            if key == "cf_clearance" or key.startswith("__cf_")
        )
        return (
            f"{response.status_code} server={server} "
            f"content-type={content_type.split(';')[0]} "
            f"new-refresh-cookie={bool(rotated)} "
            f"refresh-rotated={rotated_from_current} "
            f"cf-response={cf_response} cf-session={cf_session}"
        )


async def _public_status(
    url: str, proxy: str | None, impersonate: str = "chrome136"
) -> str:
    async with AsyncSession() as session:
        try:
            response = await session.get(
                url=url,
                timeout=15,
                impersonate=impersonate,
                proxy=proxy,
            )
        except Exception as exc:
            return f"transport-error:{type(exc).__name__}"
        content_type = response.headers.get("content-type", "unknown")
        ray = response.headers.get("cf-ray", "")
        colo = ray.rsplit("-", 1)[-1] if "-" in ray else "unknown"
        try:
            payload = response.json()
            if isinstance(payload, dict):
                body = {
                    key: payload[key]
                    for key in ("error", "message", "code", "status")
                    if key in payload
                }
                body_shape = f"keys={sorted(payload)} error={body}"
            elif isinstance(payload, int):
                body_shape = f"json-int={payload}"
            else:
                body_shape = f"json-type={type(payload).__name__}"
        except ValueError:
            body_shape = "non-json"
        return (
            f"{response.status_code} "
            f"server={response.headers.get('server', 'unknown')} "
            f"content-type={content_type.split(';')[0]} "
            f"colo={colo} "
            f"cf-mitigated={response.headers.get('cf-mitigated', 'none')} "
            f"{body_shape}"
        )


async def _egress_ip(proxy: str | None) -> str | None:
    async with AsyncSession() as session:
        try:
            response = await session.get(
                url="https://www.cloudflare.com/cdn-cgi/trace",
                timeout=15,
                impersonate="chrome136",
                proxy=proxy,
            )
            if response.status_code != 200:
                return None
            values = dict(
                line.split("=", 1)
                for line in response.text.splitlines()
                if "=" in line
            )
            return values.get("ip")
        except Exception:
            return None


async def _httpx_public_status(proxy: str | None) -> str:
    try:
        async with httpx.AsyncClient(proxy=proxy, timeout=15) as client:
            response = await client.get(AxiomTradeApiUrls.SERVER_TIME_URL)
            return str(response.status_code)
    except Exception as exc:
        return f"transport-error:{type(exc).__name__}"


async def _network_info(proxy: str | None) -> str:
    async with AsyncSession() as session:
        try:
            response = await session.get(
                url="https://ipinfo.io/json",
                timeout=15,
                impersonate="chrome136",
                proxy=proxy,
            )
            if response.status_code != 200:
                return f"status={response.status_code}"
            data = response.json()
            if not isinstance(data, dict):
                return "invalid-response"
            org = str(data.get("org", "unknown"))
            asn = org.split(" ", 1)[0] if org.startswith("AS") else "unknown"
            return f"country={data.get('country', 'unknown')} asn={asn}"
        except Exception as exc:
            return f"transport-error:{type(exc).__name__}"


async def _fingerprint_status(
    proxy: str | None,
    *,
    impersonate: str,
    default_headers: bool,
    http_version: CurlHttpVersion | None = None,
) -> str:
    async with AsyncSession() as session:
        try:
            response = await session.get(
                url=AxiomTradeApiUrls.SERVER_TIME_URL,
                timeout=15,
                proxy=proxy,
                impersonate=impersonate,
                default_headers=default_headers,
                http_version=http_version,
            )
            return str(response.status_code)
        except Exception as exc:
            return f"transport-error:{type(exc).__name__}"


async def _support_evidence(proxy: str | None) -> str:
    async with AsyncSession() as session:
        try:
            response = await session.get(
                url=AxiomTradeApiUrls.SERVER_TIME_URL,
                timeout=15,
                impersonate="chrome136",
                proxy=proxy,
            )
            checked_at = datetime.now(timezone.utc).isoformat()
            ray = response.headers.get("cf-ray", "missing")
            return f"time={checked_at} status={response.status_code} ray={ray}"
        except Exception as exc:
            return f"transport-error:{type(exc).__name__}"


def _token_expiry(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
            algorithms=["HS256"],
        )
        exp = payload.get("exp")
        if isinstance(exp, int):
            return datetime.fromtimestamp(exp, timezone.utc).strftime(
                "%Y-%m-%d"
            )
    except jwt.PyJWTError, OverflowError, ValueError:
        pass
    return "unknown"


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--agents-file",
        type=Path,
        default=Path("axiom_users_fingerprints.json"),
    )
    parser.add_argument("--host", choices=AAllBaseUrls.URLS)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--agent", action="append", default=[])
    parser.add_argument("--proxy-agent")
    parser.add_argument("--public-check", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--egress-check", action="store_true")
    parser.add_argument("--httpx-check", action="store_true")
    parser.add_argument("--network-info", action="store_true")
    parser.add_argument("--fingerprint-check", action="store_true")
    parser.add_argument("--support-evidence", action="store_true")
    args = parser.parse_args()
    if args.probe and args.host is None:
        parser.error("--probe requires --host")

    agents = _agents(args.agents_file)
    names = Counter(agent.agent_name for agent in agents)
    if any(count > 1 for count in names.values()):
        raise ValueError("agent names must be unique for diagnostics")
    selected = [
        agent
        for agent in agents
        if not args.agent or agent.agent_name in args.agent
    ]
    if args.agent and len(selected) != len(set(args.agent)):
        raise ValueError("unknown agent name")
    proxy_agent = next(
        (agent for agent in agents if agent.agent_name == args.proxy_agent),
        None,
    )
    if args.proxy_agent and proxy_agent is None:
        raise ValueError("unknown proxy agent name")

    routes = _route_labels(agents)
    user_agents = _labels([agent.headers.user_agent or "" for agent in agents])
    refresh_tokens = _labels(
        [agent.cookies.auth_refresh_token.cookie for agent in agents]
    )
    print(f"agents={len(selected)} unique_routes={len(routes)}")
    print(f"curl-cffi-chrome136-target={REAL_TARGET_MAP.get('chrome136')}")
    for agent in selected:
        route = routes[agent.proxy or "direct"]
        scheme = urlsplit(agent.proxy).scheme if agent.proxy else "direct"
        ua = user_agents[agent.headers.user_agent or ""]
        token = refresh_tokens[agent.cookies.auth_refresh_token.cookie]
        expiry = _token_expiry(agent.cookies.auth_refresh_token.cookie)
        chrome = re.search(r"Chrome/(\d+)", agent.headers.user_agent or "")
        ua_chrome = chrome.group(1) if chrome else "unknown"
        print(
            f"{agent.agent_name} {route} scheme={scheme} "
            f"ua-group={ua} refresh-token-group={token} "
            f"refresh-exp={expiry} ua-chrome={ua_chrome}"
        )
    if args.probe:
        assert args.host is not None
        print(f"host={urlsplit(args.host).hostname}")
        if proxy_agent is not None:
            print(f"test-route={routes[proxy_agent.proxy or 'direct']}")
        for agent in selected:
            status = await _probe(
                agent,
                args.host,
                proxy_agent.proxy if proxy_agent is not None else None,
            )
            print(f"{agent.agent_name} refresh_status={status}")
    if args.public_check:
        checked: set[str] = set()
        for agent in selected:
            proxy = (
                proxy_agent.proxy if proxy_agent is not None else agent.proxy
            )
            route = routes[proxy or "direct"]
            if route in checked:
                continue
            checked.add(route)
            axiom_status = await _public_status(
                AxiomTradeApiUrls.SERVER_TIME_URL, proxy
            )
            example_status = await _public_status(
                "https://example.com/", proxy
            )
            site_status = await _public_status("https://axiom.trade/", proxy)
            print(f"{route} public_chrome136_status={axiom_status}")
            print(f"{route} example_status={example_status}")
            print(f"{route} axiom_site_status={site_status}")
    if args.preflight:
        client = AxiomTradeClient(agents)
        try:
            results = await client.exclude_unavailable_routes()
            for name, probe_status in results.items():
                print(f"{name} preflight_status={probe_status}")
        finally:
            await client.close()
    if args.egress_check:
        ip_labels: dict[str, str] = {}
        for agent in selected:
            observations = []
            for _ in range(3):
                ip = await _egress_ip(agent.proxy)
                if ip is None:
                    observations.append("unavailable")
                    continue
                ip_labels.setdefault(ip, f"egress-{len(ip_labels) + 1}")
                observations.append(ip_labels[ip])
            print(f"{agent.agent_name} egress={observations}")
    if args.httpx_check:
        for agent in selected:
            status = await _httpx_public_status(agent.proxy)
            print(f"{agent.agent_name} httpx_public_status={status}")
    if args.network_info:
        for agent in selected:
            info = await _network_info(agent.proxy)
            print(f"{agent.agent_name} {info}")
    if args.fingerprint_check:
        for agent in selected:
            for label, impersonate, default_headers, http_version in (
                ("chrome136-http1", "chrome136", True, CurlHttpVersion.V1_1),
                ("chrome136-no-default-headers", "chrome136", False, None),
                ("chrome136", "chrome136", True, None),
            ):
                status = await _fingerprint_status(
                    agent.proxy,
                    impersonate=impersonate,
                    default_headers=default_headers,
                    http_version=http_version,
                )
                print(f"{agent.agent_name} {label}_status={status}")
    if args.support_evidence:
        for agent in selected:
            evidence = await _support_evidence(agent.proxy)
            print(f"{agent.agent_name} {evidence}")


if __name__ == "__main__":
    asyncio.run(main())
