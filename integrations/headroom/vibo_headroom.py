"""ViBo <-> Headroom adapter.

Direction A (this file): use `headroom-ai` as the compressor inside ViBo's
web-search savings pipeline, instead of the naive HTML->text pass.

Direction B (see README.md): an agent using Headroom gains persistent memory
via the ViBo MCP server (`@vibo-dev/vibo-mcp`, tools `memory_add` / `memory_search`).

Requires: pip install headroom-ai
"""

from __future__ import annotations

from typing import Any


def compress_article(
    text: str,
    model: str = "gpt-4o",
    query: str = "",
    **kwargs: Any,
) -> dict[str, Any]:
    """Compress a web article (or any text) with Headroom.

    Returns a dict compatible with ViBo's own web-compression stats shape:
        text        - the compressed text (ready for the agent's context)
        orig_tokens - tokens before compression
        comp_tokens - tokens after compression
        saved_tokens- tokens saved
        saved_pct   - percent saved (0-100)
    """
    try:
        from headroom import compress
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "headroom-ai is not installed. Run: pip install headroom-ai"
        ) from exc

    messages = [{"role": "user", "content": text}]
    # A web article arrives as a user message; headroom protects user messages
    # by default, so enable compression of them explicitly.
    kwargs.setdefault("compress_user_messages", True)
    result = compress(messages, model=model, optimize=True, **kwargs)

    compressed = ""
    if result.messages:
        first = result.messages[0]
        compressed = first.get("content", "") if isinstance(first, dict) else str(first)

    saved_pct = round(float(result.compression_ratio or 0.0) * 100, 1)
    return {
        "text": compressed,
        "orig_tokens": int(result.tokens_before or 0),
        "comp_tokens": int(result.tokens_after or 0),
        "saved_tokens": int(result.tokens_saved or 0),
        "saved_pct": saved_pct,
    }


if __name__ == "__main__":  # pragma: no cover - quick demo
    import sys

    sample = sys.stdin.read() if not sys.stdin.isatty() else " ".join(sys.argv[1:])
    if not sample:
        sample = (
            "Web search results are huge. Dumping full articles into the LLM "
            "context is expensive. Compression removes navigation, ads and "
            "duplicates while keeping the paragraphs relevant to the query. "
            "Repeated questions are answered from cache at zero cost. "
        ) * 4
    out = compress_article(sample)
    print(
        f"💾 {out['orig_tokens']} -> {out['comp_tokens']} tokens "
        f"({out['saved_pct']}% saved)"
    )
    print("--- compressed ---")
    print(out["text"][:400])
