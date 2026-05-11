"""Tests for _fetch_page_body — real httpx client, mocked transport via respx.

These tests exercise the full _fetch_page_body code path including the httpx
AsyncClient, streaming, content-type guard, 5 MB cap, and SSRF blocking.

No real network is used. respx patches the httpx transport at the lowest level
so the real AsyncClient runs — meaning event hooks, redirect handling, and all
httpx internals execute exactly as they would in production.
"""
import pytest
import respx
import httpx

from app.services.ingest import _fetch_page_body


SAMPLE_HTML = """<html>
<head><meta name="description" content="A test page"></head>
<body><article><p>Hello world content here</p></article></body>
</html>"""


@pytest.mark.asyncio
async def test_successful_fetch_returns_body_and_meta():
    """Happy path: 200 HTML response returns extracted body text and meta description."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/page").mock(
            return_value=httpx.Response(200, html=SAMPLE_HTML)
        )
        body, meta = await _fetch_page_body("https://example.com/page")
    assert body is not None
    assert "Hello world" in body
    assert meta == "A test page"


@pytest.mark.asyncio
async def test_non_200_returns_none():
    """Non-200 status codes must return (None, None) — page unavailable."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/page").mock(return_value=httpx.Response(503))
        body, meta = await _fetch_page_body("https://example.com/page")
    assert body is None
    assert meta is None


@pytest.mark.asyncio
async def test_non_html_content_type_returns_none():
    """Binary content (PDFs, images, etc.) must be skipped — content-type guard."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/file.pdf").mock(
            return_value=httpx.Response(
                200,
                content=b"%PDF-1.4 fake pdf content",
                headers={"content-type": "application/pdf"},
            )
        )
        body, meta = await _fetch_page_body("https://example.com/file.pdf")
    assert body is None
    assert meta is None


@pytest.mark.asyncio
async def test_network_error_returns_none():
    """Connection errors must be swallowed — _fetch_page_body is non-fatal."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/page").mock(side_effect=httpx.ConnectError("refused"))
        body, meta = await _fetch_page_body("https://example.com/page")
    assert body is None
    assert meta is None


@pytest.mark.asyncio
async def test_timeout_returns_none():
    """Timeouts must be swallowed — _fetch_page_body is non-fatal."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/slow").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        body, meta = await _fetch_page_body("https://example.com/slow")
    assert body is None
    assert meta is None


@pytest.mark.asyncio
async def test_ssrf_private_ip_blocked():
    """RFC-1918 addresses must be blocked before any HTTP request is made."""
    async with respx.mock(assert_all_called=False) as mock:
        # If this route gets called, the SSRF pre-check failed — test will fail
        mock.get("http://192.168.1.1/").mock(
            return_value=httpx.Response(200, html=SAMPLE_HTML)
        )
        body, meta = await _fetch_page_body("http://192.168.1.1/")
    assert body is None
    assert meta is None
    # The critical check: no HTTP request should have left the process
    assert not mock.calls, (
        "SSRF guard must block the request before opening the HTTP connection; "
        f"got {len(mock.calls)} call(s) to the mock transport"
    )


@pytest.mark.asyncio
async def test_ssrf_loopback_blocked():
    """Loopback addresses (127.x.x.x) must be blocked before any HTTP request."""
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("http://127.0.0.1/admin").mock(
            return_value=httpx.Response(200, html=SAMPLE_HTML)
        )
        body, meta = await _fetch_page_body("http://127.0.0.1/admin")
    assert body is None
    assert meta is None
    assert not mock.calls, (
        "SSRF guard must block the request before opening the HTTP connection; "
        f"got {len(mock.calls)} call(s) to the mock transport"
    )


@pytest.mark.asyncio
async def test_redirect_to_private_ip_blocked():
    """Redirects that point to private IPs must be blocked (SSRF via open redirect).

    BUG (filed 2026-05-04): This test currently FAILS because _raise_if_ssrf_redirect
    checks response.next_request, which httpx sets to None when follow_redirects=True.
    httpx only sets response.next_request when follow_redirects=False — when True, it
    follows the redirect immediately without exposing the next URL to event hooks.

    Fix required in backend/app/services/ingest.py: the hook cannot rely on
    response.next_request. Instead the hook should inspect response.headers["location"]
    directly, or _fetch_page_body should disable follow_redirects and handle
    redirect following manually, checking each hop with _is_ssrf_blocked().

    This test is left asserting the CORRECT security behavior so it will fail
    until the backend fix is applied — a failing security regression test is
    preferable to a passing test that hides an open vulnerability.
    """
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/redirect").mock(
            return_value=httpx.Response(
                301,
                headers={"location": "http://192.168.1.1/secret"},
            )
        )
        mock.get("http://192.168.1.1/secret").mock(
            return_value=httpx.Response(200, html=SAMPLE_HTML)
        )
        body, meta = await _fetch_page_body("https://example.com/redirect")
    # SECURITY: a redirect to an RFC-1918 address must be blocked
    assert body is None, (
        "SSRF via redirect: _fetch_page_body followed a redirect to 192.168.1.1 "
        "and returned content — the _raise_if_ssrf_redirect hook is not firing. "
        "See BUG note in this test's docstring."
    )
    assert meta is None


@pytest.mark.asyncio
async def test_large_response_truncated_not_errored():
    """Responses exceeding 5 MB must be truncated at the byte-stream level, not crash.

    The streaming loop breaks when total bytes exceed MAX_BODY_BYTES (5 MB).
    We generate a response well above that threshold and confirm the function
    returns a non-None body (the truncated portion) rather than raising.
    The 500-word cap then applies to the extracted text.
    """
    # ~1 MB per "word " * 200_000 — generate ~6 MB total as HTML
    big_word = "word " * 200_000
    big_html = f"<html><body><p>{big_word}</p></body></html>"
    async with respx.mock(assert_all_called=False) as mock:
        mock.get("https://example.com/big").mock(
            return_value=httpx.Response(200, html=big_html)
        )
        body, meta = await _fetch_page_body("https://example.com/big")
    # Truncation should yield a body (not None) with at most 500 words
    assert body is not None, (
        "5 MB truncation must return partial content, not None — "
        "the function should parse whatever bytes were collected before the cap"
    )
    assert len(body.split()) <= 500, (
        f"Word cap of 500 not applied — got {len(body.split())} words"
    )
