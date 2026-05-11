import ipaddress
import logging
import socket
from urllib.parse import urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.link import Link
from app.schemas.link import LinkCreate
from app.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)

MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MB

_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_ssrf_blocked(url: str) -> bool:
    host = urlparse(url).hostname or ""
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
    except (socket.gaierror, ValueError):
        return True
    return any(ip in net for net in _BLOCKED_NETWORKS)


async def _raise_if_ssrf_redirect(response: httpx.Response) -> None:
    location = response.headers.get("location", "")
    if location and _is_ssrf_blocked(location):
        raise ValueError(f"Redirect to blocked host: {location}")


def text_for_embedding(
    title: str | None,
    snippet: str | None,
    page_body: str | None,
    meta_description: str | None,
) -> str:
    return " ".join(filter(None, [title, snippet, page_body, meta_description]))


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/") if parsed.path != "/" else parsed.path,
    )
    return urlunparse(normalized)


_STRIP_TAGS = {"script", "style", "nav", "footer", "header"}
_CONTENT_TAGS = ["article", "main", "body"]
_MAX_WORDS = 500


def _extract_body_and_meta(html: str) -> tuple[str | None, str | None]:
    """Parse *html* and return (page_body, meta_description).

    page_body: visible text from the best content element (article > main > body),
    stripped of noise tags, truncated to 500 words. None if empty.
    meta_description: content of <meta name="description">. None if absent.
    """
    if not html:
        return None, None

    soup = BeautifulSoup(html, "html.parser")

    # Extract meta description before stripping anything
    meta_description: str | None = None
    meta_tag = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "description"})
    if meta_tag and meta_tag.get("content"):
        meta_description = meta_tag["content"].strip() or None

    # Remove noise tags in-place
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    # Find best content element
    content_el = None
    for tag_name in _CONTENT_TAGS:
        content_el = soup.find(tag_name)
        if content_el:
            break

    if content_el is None:
        return None, meta_description

    text = content_el.get_text(separator=" ", strip=True)
    words = text.split()
    if not words:
        return None, meta_description

    if len(words) > _MAX_WORDS:
        words = words[:_MAX_WORDS]

    return " ".join(words), meta_description


async def _fetch_page_body(url: str) -> tuple[str | None, str | None]:
    """Fetch *url* and return (page_body, meta_description). Non-fatal — returns (None, None) on any error."""
    if _is_ssrf_blocked(url):
        logger.warning("page_body fetch blocked (SSRF) for %s", url)
        return None, None

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=5,
            timeout=httpx.Timeout(connect=5.0, read=5.0, write=5.0, pool=5.0),
            event_hooks={"response": [_raise_if_ssrf_redirect]},
        ) as client:
            async with client.stream(
                "GET", url, headers={"User-Agent": "Linkyard-Bot/1.0 (semantic bookmark indexer)"}
            ) as response:
                if response.status_code != 200:
                    logger.warning("page_body fetch returned %d for %s", response.status_code, url)
                    return None, None

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    logger.warning("page_body skipped non-HTML content-type %r for %s", content_type, url)
                    return None, None

                chunks: list[bytes] = []
                total = 0
                async for chunk in response.aiter_bytes(chunk_size=65536):
                    total += len(chunk)
                    if total > MAX_BODY_BYTES:
                        logger.warning("page_body size limit exceeded for %s, truncating", url)
                        break
                    chunks.append(chunk)

                raw = b"".join(chunks)

        try:
            html = raw.decode(response.encoding or "utf-8", errors="replace")
        except Exception as exc:
            logger.warning("page_body decode failed for %s: %s", url, exc)
            return None, None

    except Exception as exc:
        logger.warning("page_body fetch failed for %s: %s", url, exc)
        return None, None

    return _extract_body_and_meta(html)


async def ingest_link(
    session: AsyncSession, data: LinkCreate, provider: EmbeddingProvider
) -> Link:
    url = _normalize_url(data.url)

    page_body, fetched_meta = await _fetch_page_body(url)
    meta_description = data.meta_description or fetched_meta

    embedding = await provider.embed(
        text_for_embedding(data.title, data.snippet, page_body, meta_description)
    )

    link = Link(
        url=url,
        title=data.title,
        snippet=data.snippet,
        meta_description=meta_description,
        page_body=page_body,
        source=data.source,
        embedding=embedding,
    )
    session.add(link)
    await session.flush()
    await session.refresh(link)
    return link
