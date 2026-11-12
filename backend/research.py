import asyncio
import ipaddress
import socket
from urllib.parse import urljoin

import aiohttp
from protego import Protego
from trafilatura import extract
from yarl import URL

AGENT = "ArticleResearchBot"
MAX_BYTES = 2_000_000


def public(address):
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


class PublicResolver(aiohttp.abc.AbstractResolver):
    async def resolve(self, host, port=0, family=socket.AF_UNSPEC):
        rows = await asyncio.get_running_loop().getaddrinfo(
            host, port, family=family, type=socket.SOCK_STREAM
        )
        if not rows or any(not public(row[4][0]) for row in rows):
            raise OSError("Non-public DNS address")
        return [
            dict(hostname=host, host=addr[0], port=addr[1], family=kind,
                 proto=proto, flags=socket.AI_NUMERICHOST)
            for kind, _, proto, _, addr in rows
        ]

    async def close(self):
        pass


def checked_url(value):
    url = URL(value)
    host = url.raw_host
    if (url.scheme not in {"http", "https"} or not host or url.user is not None
            or url.port not in {80, 443} or host.endswith((".local", ".localhost"))
            or host == "localhost" or "%" in host):
        raise ValueError("Unsupported destination")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return url
    if not public(host):
        raise ValueError("Non-public destination")
    return url


async def fetch(session, value, *, robots=False):
    for _ in range(5):
        url = checked_url(value)
        if not robots:
            await check_robots(session, url)
        async with session.get(url, allow_redirects=False) as response:
            if response.status in {301, 302, 303, 307, 308}:
                value = urljoin(str(url), response.headers["Location"])
                continue
            if robots and response.status in {404, 410}:
                return ""
            response.raise_for_status()
            if response.status != 200 or (not robots and response.content_type not in
                                          {"text/html", "application/xhtml+xml"}):
                raise ValueError("Unsupported response")
            body = bytearray()
            async for chunk in response.content.iter_chunked(32_768):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise ValueError("Response too large")
            return body.decode(response.charset or "utf-8", errors="replace")
    raise ValueError("Too many redirects")


async def check_robots(session, url):
    text = await fetch(session, str(url.origin().join(URL("/robots.txt"))), robots=True)
    if not Protego.parse(text).can_fetch(str(url), AGENT):
        raise ValueError("Disallowed by robots.txt")


async def review(sources):
    limit = asyncio.Semaphore(4)
    connector = aiohttp.TCPConnector(resolver=PublicResolver(), limit=4, use_dns_cache=False)
    async with aiohttp.ClientSession(
        connector=connector, timeout=aiohttp.ClientTimeout(total=8),
        headers={"User-Agent": AGENT}, trust_env=False,
    ) as session:
        async def one(source):
            async with limit:
                try:
                    async with asyncio.timeout(16):
                        html = await fetch(session, source["url"])
                        body = await asyncio.to_thread(
                            extract, html, favor_precision=True, include_comments=False
                        )
                    if body and len(body.split()) >= 100:
                        source.update(status="Reviewed", text=body[:6500])
                except (aiohttp.ClientError, TimeoutError, ValueError, OSError, LookupError):
                    pass
        await asyncio.gather(*(one(source) for source in sources))
    seen = set()
    for source in sources:
        body = source.get("text")
        if body and body in seen:
            source.pop("text")
            source["status"] = "Snippet only" if source["snippet"] else "Unavailable"
        elif body:
            seen.add(body)


async def search(client, settings, request):
    response = await client.get(settings["search_url"], params={
        "engine": "google", "api_key": settings["search_key"], "q": request.topic,
        "gl": request.country.lower(), "hl": request.language.lower(), "num": 10,
    })
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise ValueError("Search provider rejected the request")
    sources = []
    for rank, entry in enumerate(data.get("organic_results", [])[:10], 1):
        snippet = (entry.get("snippet") or "")[:500]
        sources.append(dict(rank=rank, title=(entry.get("title") or "Untitled")[:300],
                            url=entry.get("link") or "", snippet=snippet,
                            status="Snippet only" if snippet else "Unavailable"))
    return sources
