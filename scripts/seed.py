# Usage: python scripts/seed.py

import json
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

LINKS = [
    # ── Machine learning / AI (5) ──────────────────────────────────────────
    {
        "url": "https://example-ml-papers.com/attention-is-all-you-need",
        "title": "Attention Is All You Need",
        "snippet": (
            "The original transformer paper introducing the self-attention mechanism "
            "that replaced recurrence and convolutions for sequence modelling. "
            "Understanding this architecture is the foundation for every large language "
            "model built since 2017 — BERT, GPT, T5, and their descendants all trace "
            "their core design back to this single paper."
        ),
        "source": "api",
    },
    {
        "url": "https://example-ml-papers.com/scaling-laws-neural-language-models",
        # No title — intentional variation
        "snippet": (
            "Empirical study showing that language model performance scales as a "
            "power law with model size, dataset size, and compute budget."
        ),
        "source": "api",
    },
    {
        "url": "https://example-ml-tools.io/huggingface-transformers-quickstart",
        "title": "Hugging Face Transformers: Getting Started",
        "snippet": (
            "Official quickstart guide for the transformers library — covers model "
            "loading, tokenization, and inference in five minutes."
        ),
        "source": "web",
    },
    {
        "url": "https://example-ml-explainers.dev/what-is-rag",
        "title": "What Is Retrieval-Augmented Generation?",
        "snippet": (
            "Plain-English explainer of RAG: why combining a vector store with a "
            "generative model reduces hallucinations and keeps facts up to date."
        ),
        "source": "web",
    },
    {
        "url": "https://example-ml-tools.io/sentence-transformers-docs",
        "title": "Sentence Transformers Documentation",
        "snippet": (
            "Library for computing dense vector embeddings from sentences and "
            "paragraphs, built on top of Hugging Face Transformers."
        ),
        "source": "extension",
    },
    # ── Web development (5) ────────────────────────────────────────────────
    {
        "url": "https://example-webdev-docs.com/react-18-concurrent-features",
        "title": "React 18: Concurrent Features Deep Dive",
        "snippet": (
            "Explains startTransition, useDeferredValue, and the new root API — "
            "and when to reach for each one."
        ),
        "source": "web",
    },
    {
        "url": "https://example-webdev-docs.com/vite-plugin-authoring",
        "title": "Authoring Vite Plugins",
        # No snippet — intentional variation
        "source": "web",
    },
    {
        "url": "https://example-webdev-perf.io/core-web-vitals-field-guide",
        "title": "Core Web Vitals: A Field Guide",
        "snippet": (
            "Practical breakdown of LCP, CLS, and INP with diagnostic recipes "
            "for each metric using Chrome DevTools and the web-vitals library."
        ),
        "source": "extension",
    },
    {
        "url": "https://example-webdev-docs.com/fetch-api-abort-streams",
        "title": "Fetch API: AbortController and Readable Streams",
        "snippet": (
            "How to cancel in-flight requests with AbortController and consume "
            "streaming responses without loading the full body into memory."
        ),
        "source": "web",
    },
    {
        "url": "https://example-webdev-perf.io/css-container-queries-explained",
        "title": "CSS Container Queries Explained",
        "snippet": (
            "Container queries let components respond to the size of their parent "
            "rather than the viewport — enabling truly self-contained responsive UI."
        ),
        "source": "web",
    },
    # ── Developer tools / productivity (5) ────────────────────────────────
    {
        "url": "https://example-devtools.sh/neovim-lsp-zero-setup",
        "title": "Neovim LSP Zero: Zero-Config Language Server Setup",
        "snippet": (
            "lsp-zero bridges nvim-lspconfig, mason, and nvim-cmp so you get "
            "IDE-grade completion and diagnostics with fewer than 20 lines of Lua."
        ),
        "source": "web",
    },
    {
        "url": "https://example-devtools.sh/zsh-dotfiles-structure",
        "title": "Structuring Your Zsh Dotfiles for Portability",
        "snippet": (
            "Opinionated guide to splitting .zshrc into sourced modules, managing "
            "secrets with 1Password CLI, and syncing across machines via a bare repo."
        ),
        "source": "web",
    },
    {
        "url": "https://example-devtools.sh/ripgrep-advanced-usage",
        "title": "ripgrep: Beyond the Basics",
        "snippet": (
            "Lesser-known ripgrep flags: --multiline, --type-add, --pre for "
            "pre-processing binary files, and PCRE2 lookaheads."
        ),
        "source": "extension",
    },
    {
        "url": "https://example-devtools.sh/tmux-sessionizer-workflow",
        "title": "The tmux Sessionizer Workflow",
        "snippet": (
            "Popularised by ThePrimeagen — fuzzy-find any project directory and "
            "jump to a named tmux session in one keystroke."
        ),
        "source": "web",
    },
    {
        "url": "https://example-devtools.sh/gh-cli-scripting",
        "title": "Scripting GitHub with the gh CLI",
        "snippet": (
            "Using gh api, gh pr, and gh run commands in shell scripts to automate "
            "PR workflows, release notes, and CI status checks."
        ),
        "source": "api",
    },
    # ── System design / architecture (5) ──────────────────────────────────
    {
        "url": "https://example-sysdesign.io/consistent-hashing-explained",
        "title": "Consistent Hashing Explained",
        "snippet": (
            "Visual walkthrough of consistent hashing rings, virtual nodes, and "
            "why it minimises key remapping when a cache node is added or removed."
        ),
        "source": "web",
    },
    {
        "url": "https://example-sysdesign.io/api-pagination-patterns",
        "title": "API Pagination: Offset vs Cursor vs Keyset",
        "snippet": (
            "Compares three pagination strategies with concrete Postgres query plans "
            "and explains why cursor-based pagination wins at scale."
        ),
        "source": "web",
    },
    {
        "url": "https://example-sysdesign.io/event-sourcing-primer",
        "title": "Event Sourcing: A Practical Primer",
        "snippet": (
            "Covers append-only event logs, projections, snapshots, and the "
            "difference between event sourcing and plain event-driven architecture."
        ),
        "source": "extension",
    },
    {
        "url": "https://example-sysdesign.io/postgres-mvcc-internals",
        "title": "How Postgres MVCC Works Under the Hood",
        "snippet": (
            "Deep dive into transaction IDs, tuple visibility rules, HOT updates, "
            "and why VACUUM exists — essential reading before tuning autovacuum."
        ),
        "source": "api",
    },
    {
        "url": "https://example-sysdesign.io/grpc-vs-rest-when-to-use",
        "title": "gRPC vs REST: When to Use Each",
        "snippet": (
            "Decision framework covering latency, streaming needs, schema evolution, "
            "and client ecosystem — with a reference table for common service types."
        ),
        "source": "web",
    },
]

# One intentional bad entry to exercise the 422 path (no scheme)
BAD_LINK = {
    "url": "example-sysdesign.io/no-scheme-url",
    "title": "Bad URL (no scheme — should fail with 422)",
    "source": "web",
}


def post_link(entry: dict) -> tuple[bool, str]:
    """POST a single link. Returns (success, label)."""
    label = entry.get("title") or entry["url"]
    payload = json.dumps(entry).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/links",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 201:
                print(f"✓ {label}")
                return True, label
            # Unexpected 2xx
            print(f"✗ {entry['url']} — {resp.status} unexpected status")
            return False, label
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        try:
            detail = json.loads(body).get("detail", body)
        except Exception:
            detail = body
        print(f"✗ {entry['url']} — {exc.code} {detail}")
        return False, label
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"\nCannot reach backend at {BASE_URL} — is it running?\n"
            f"  Reason: {exc.reason}\n"
            f"  Start it with: cd backend && uvicorn app.main:app --reload"
        ) from exc


def main() -> None:
    print(f"Seeding {len(LINKS)} links to {BASE_URL}/links …\n")

    successes = 0
    for entry in LINKS:
        ok, _ = post_link(entry)
        if ok:
            successes += 1

    # Intentional bad entry — expect 422
    print("\n--- intentional bad entry (expect 422) ---")
    post_link(BAD_LINK)
    print("------------------------------------------\n")

    print(f"Seeded {successes}/{len(LINKS)} links successfully.")


if __name__ == "__main__":
    main()
