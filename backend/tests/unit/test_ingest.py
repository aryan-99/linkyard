"""Unit tests for ingest pure functions — no DB, no network required."""
import pytest
from app.services.ingest import _extract_body_and_meta, text_for_embedding


# --- text_for_embedding ---

def test_text_for_embedding_all_none():
    assert text_for_embedding(None, None, None, None) == ""

def test_text_for_embedding_title_only():
    assert text_for_embedding("Hello", None, None, None) == "Hello"

def test_text_for_embedding_stacks_all_four():
    assert text_for_embedding("T", "S", "B", "M") == "T S B M"

def test_text_for_embedding_skips_none():
    assert text_for_embedding("Title", None, "Body", None) == "Title Body"


# --- _extract_body_and_meta ---

def test_extract_prefers_article():
    html = """<html><body>
      <nav>Navigation</nav>
      <article>Real content here</article>
      <footer>Footer text</footer>
    </body></html>"""
    body, meta = _extract_body_and_meta(html)
    assert body is not None
    assert "Real content" in body
    assert "Navigation" not in body
    assert "Footer" not in body

def test_extract_falls_back_to_main():
    html = "<html><body><main><p>Main content</p></main></body></html>"
    body, meta = _extract_body_and_meta(html)
    assert body is not None
    assert "Main content" in body

def test_extract_falls_back_to_body():
    html = "<html><body><p>Plain body text</p></body></html>"
    body, meta = _extract_body_and_meta(html)
    assert body is not None
    assert "Plain body text" in body

def test_extract_meta_description():
    html = """<html><head>
      <meta name="description" content="A page about cats">
    </head><body><p>Content</p></body></html>"""
    body, meta = _extract_body_and_meta(html)
    assert meta == "A page about cats"

def test_extract_meta_description_case_insensitive():
    html = """<html><head>
      <meta name="Description" content="Capital D">
    </head><body><p>Content</p></body></html>"""
    _, meta = _extract_body_and_meta(html)
    assert meta == "Capital D"

def test_extract_strips_script_and_style():
    html = """<html><body>
      <script>var x = 1;</script>
      <style>.foo { color: red; }</style>
      <p>Visible text</p>
    </body></html>"""
    body, _ = _extract_body_and_meta(html)
    assert "var x" not in body
    assert ".foo" not in body
    assert "Visible text" in body

def test_extract_strips_nav_footer_header():
    html = """<html><body>
      <header>Site Header</header>
      <nav>Nav links</nav>
      <article>Article body</article>
      <footer>Site Footer</footer>
    </body></html>"""
    body, _ = _extract_body_and_meta(html)
    assert "Site Header" not in body
    assert "Nav links" not in body
    assert "Site Footer" not in body
    assert "Article body" in body

def test_extract_truncates_to_500_words():
    words = ["word"] * 600
    html = f"<html><body><p>{' '.join(words)}</p></body></html>"
    body, _ = _extract_body_and_meta(html)
    assert len(body.split()) == 500

def test_extract_empty_body_returns_none():
    html = "<html><body></body></html>"
    body, _ = _extract_body_and_meta(html)
    assert body is None

def test_extract_empty_string_returns_none_none():
    body, meta = _extract_body_and_meta("")
    assert body is None
    assert meta is None
