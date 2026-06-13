"""One-off script: fetch a curated URL list and write demo_links.json.

Run from repo root (with backend deps installed):
    python backend/scripts/generate_seed.py

Output: backend/app/seed/demo_links.json

Do NOT import this module at application startup — it's a local dev tool only.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Make sure app package is importable when run from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ingest import _extract_body_and_meta, _fetch_page_body

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_PATH = Path(__file__).parent.parent / "app" / "seed" / "demo_links.json"

# ---------------------------------------------------------------------------
# Curated URL list — evergreen, no paywall, no news, diverse topics.
# Programming: Python, JS/TS, Go, Rust, Haskell, Clojure, Elixir, Lisp, OCaml
# ML/AI, Design, Philosophy, Science, Productivity, Tools, Web
# ---------------------------------------------------------------------------
URLS = [
    # --- Python ---
    ("https://docs.python.org/3/tutorial/classes.html",
     "Python Classes — official tutorial"),
    ("https://docs.python.org/3/howto/functional.html",
     "Functional Programming HOWTO — Python docs"),
    ("https://realpython.com/python-concurrency/",
     "Python Concurrency: asyncio, threads, processes — Real Python"),
    # --- JavaScript / TypeScript ---
    ("https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures",
     "Closures — MDN JavaScript Guide"),
    ("https://www.typescriptlang.org/docs/handbook/2/types-from-types.html",
     "Types from Types — TypeScript Handbook"),
    # --- Go ---
    ("https://go.dev/doc/effective_go",
     "Effective Go — official Go documentation"),
    ("https://go.dev/blog/concurrency-is-not-parallelism",
     "Concurrency is not Parallelism — The Go Blog"),
    # --- Rust ---
    ("https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html",
     "What Is Ownership? — The Rust Book"),
    ("https://doc.rust-lang.org/book/ch16-00-concurrency.html",
     "Fearless Concurrency — The Rust Book"),
    # --- Haskell / Functional Programming ---
    ("https://www.haskell.org/tutorial/monads.html",
     "A Gentle Introduction to Haskell: Monads"),
    ("https://wiki.haskell.org/Typeclassopedia",
     "Typeclassopedia — HaskellWiki"),
    # --- Clojure ---
    ("https://clojure.org/about/rationale",
     "Clojure Rationale — clojure.org"),
    # --- Elixir ---
    ("https://elixir-lang.org/getting-started/processes.html",
     "Processes — Elixir Getting Started Guide"),
    # --- Lisp / Scheme ---
    ("https://mitpress.mit.edu/sites/default/files/sicp/full-text/book/book-Z-H-4.html",
     "SICP — Structure and Interpretation of Computer Programs (Preface)"),
    # --- Systems & CS Fundamentals ---
    ("https://en.wikipedia.org/wiki/CAP_theorem",
     "CAP Theorem — Wikipedia"),
    ("https://en.wikipedia.org/wiki/MapReduce",
     "MapReduce — Wikipedia"),
    ("https://en.wikipedia.org/wiki/B-tree",
     "B-tree — Wikipedia"),
    # --- Databases ---
    ("https://www.postgresql.org/docs/current/indexes-types.html",
     "PostgreSQL Index Types — official docs"),
    ("https://redis.io/docs/latest/develop/data-types/",
     "Redis Data Types — redis.io"),
    # --- ML / AI ---
    ("https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
     "Transformer architecture — Wikipedia"),
    ("https://en.wikipedia.org/wiki/Attention_mechanism",
     "Attention Mechanism — Wikipedia"),
    ("https://pytorch.org/tutorials/beginner/blitz/tensor_tutorial.html",
     "What is PyTorch? Tensor Tutorial — PyTorch docs"),
    ("https://scikit-learn.org/stable/modules/clustering.html",
     "Clustering — scikit-learn documentation"),
    # --- Web / APIs ---
    ("https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview",
     "An overview of HTTP — MDN Web Docs"),
    ("https://restfulapi.net/rest-architectural-constraints/",
     "REST Architectural Constraints — restfulapi.net"),
    ("https://graphql.org/learn/",
     "Introduction to GraphQL — graphql.org"),
    # --- Design ---
    ("https://www.nngroup.com/articles/ten-usability-heuristics/",
     "10 Usability Heuristics for User Interface Design — Nielsen Norman Group"),
    ("https://www.nngroup.com/articles/cognitive-load/",
     "Minimize Cognitive Load to Maximize Usability — Nielsen Norman Group"),
    # --- Philosophy ---
    ("https://en.wikipedia.org/wiki/Turing_test",
     "Turing Test — Wikipedia"),
    ("https://en.wikipedia.org/wiki/Chinese_room",
     "Chinese Room — Wikipedia"),
    ("https://plato.stanford.edu/entries/logic-classical/",
     "Classical Logic — Stanford Encyclopedia of Philosophy"),
    # --- Science ---
    ("https://en.wikipedia.org/wiki/Entropy",
     "Entropy — Wikipedia"),
    ("https://en.wikipedia.org/wiki/CRISPR",
     "CRISPR — Wikipedia"),
    # --- Productivity / Tools ---
    ("https://en.wikipedia.org/wiki/Pomodoro_Technique",
     "Pomodoro Technique — Wikipedia"),
    ("https://en.wikipedia.org/wiki/Getting_Things_Done",
     "Getting Things Done — Wikipedia"),
    ("https://neovim.io/doc/user/usr_01.html",
     "Neovim User Manual — Introduction"),
    ("https://docs.docker.com/get-started/overview/",
     "Docker overview — Docker docs"),
    ("https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F",
     "What is Git? — Pro Git Book"),
    # --- Security ---
    ("https://owasp.org/www-project-top-ten/",
     "OWASP Top Ten — owasp.org"),
    # --- Math / Algorithms ---
    ("https://en.wikipedia.org/wiki/Big_O_notation",
     "Big O Notation — Wikipedia"),
    ("https://en.wikipedia.org/wiki/Dynamic_programming",
     "Dynamic Programming — Wikipedia"),
    ("https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm",
     "Dijkstra's Algorithm — Wikipedia"),
]


async def fetch_one(url: str, hint_title: str) -> dict | None:
    """Fetch a single URL and return a seed entry dict, or None on failure."""
    logger.info("Fetching %s", url)
    try:
        page_body, meta_description = await _fetch_page_body(url)
    except Exception as exc:
        logger.warning("DROP %s — exception: %s", url, exc)
        return None

    if page_body is None and meta_description is None:
        logger.warning("DROP %s — no content extracted", url)
        return None

    return {
        "url": url,
        "title": hint_title,
        "snippet": None,
        "page_body": page_body,
        "meta_description": meta_description,
    }


async def main() -> None:
    # Run fetches with bounded concurrency (5 at a time) to be polite.
    semaphore = asyncio.Semaphore(5)

    async def bounded_fetch(url: str, title: str) -> dict | None:
        async with semaphore:
            return await fetch_one(url, title)

    tasks = [bounded_fetch(url, title) for url, title in URLS]
    results = await asyncio.gather(*tasks)

    entries = [r for r in results if r is not None]
    dropped = len(URLS) - len(entries)

    logger.info("Fetched %d/%d entries (%d dropped)", len(entries), len(URLS), dropped)

    if len(entries) < 30:
        logger.error(
            "Only %d valid entries — minimum is 30. Check network or add more URLs.",
            len(entries),
        )
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    logger.info("Wrote %d entries to %s", len(entries), OUTPUT_PATH)
    if dropped:
        logger.warning("%d URLs were dropped (fetch failed or no content):", dropped)
        fetched_urls = {e["url"] for e in entries}
        for url, _ in URLS:
            if url not in fetched_urls:
                logger.warning("  DROPPED: %s", url)


if __name__ == "__main__":
    asyncio.run(main())
