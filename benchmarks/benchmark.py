#!/usr/bin/env python3
"""ViBo benchmark — real measured numbers, not claims.

Run (requires Python 3.11 + the ViBo core):
    VIBO_LIB=/path/to/vibo python3 benchmark.py

Measures:
  1. Memory search savings — N stored facts vs. the relevant context returned.
  2. Web-search compression — a full HTML page vs. the compressed essence.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LIB = os.environ.get("VIBO_LIB", "/root/vibo")
sys.path.insert(0, LIB)

from vibo.core import Graph                       # noqa: E402
from vibo.crypto import Crypto                    # noqa: E402
from vibo.navigator import ViBoNavigator          # noqa: E402


def _tokens(chars: int) -> int:
    return max(1, chars // 4)


def bench_memory(n: int = 1000) -> dict:
    """Build N facts, then measure how many tokens a semantic search returns
    vs. dumping the whole memory."""
    graph = Graph()
    crypto = Crypto(agent_key="bench", user_password="")
    for i in range(n):
        graph.add_node(
            f"client-{i}",
            f"Client {i} prefers option {i % 5}, budget ${i * 100}, "
            f"region r{i % 10}, note about project p{i % 7}.",
            tags=["bench"],
        )
    full_chars = sum(len(n.content) + len(n.label) + 2 for n in graph.nodes.values())
    full_tokens = _tokens(full_chars)

    nav = ViBoNavigator(graph, crypto, max_context_chars=2000)
    _, usage = nav.navigate_with_usage("client-42", model="deepseek")
    ctx_tokens = int(usage.get("context_tokens") or 0)

    saved = max(0, full_tokens - ctx_tokens)
    return {
        "facts": n,
        "full_tokens": full_tokens,
        "context_tokens": ctx_tokens,
        "saved_pct": round(saved / full_tokens * 100, 1) if full_tokens else 0.0,
    }


def bench_web() -> dict:
    """Compress a realistic HTML page (navigation + ads + body) and measure."""
    from vibo_web import compress_article

    page = (
        "<html><nav>" + ("menu " * 200)
        + "</nav><div class='ads'>" + ("ad " * 300)
        + "</div><article>" + ("The quick brown fox jumps over the lazy dog. " * 200)
        + "</article></html>"
    )
    _, stats = compress_article(page, "fox")
    return stats


def main() -> int:
    print("=== ViBo benchmark (real measured) ===")
    m = bench_memory()
    print(
        f"Memory: {m['facts']} facts → {m['context_tokens']} tokens in context "
        f"vs {m['full_tokens']} full dump → {m['saved_pct']}% saved"
    )
    w = bench_web()
    print(
        f"Web: {w['orig_tokens']} → {w['comp_tokens']} tokens "
        f"({w['saved_pct']}% saved)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
