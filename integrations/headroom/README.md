# ViBo + Headroom — integration

Two complementary layers, one pipeline: **Headroom compresses the context, ViBo remembers it.**

- **Headroom** = the context compression layer (60–95% fewer tokens for tool outputs, logs, JSON, RAG chunks).
- **ViBo** = the memory layer (facts survive sessions, semantic search returns only the relevant ones, secrets encrypted L1/L2/L3).

The gap this closes: compression cuts token cost *within* a window, but the *next* session still starts from zero. Together they compress **and** persist.

---

## Direction A — ViBo uses Headroom as its compressor

`vibo_headroom.py` drops Headroom into ViBo's web-search savings pipeline as the
compressor (replacing the naive HTML→text pass).

```bash
pip install headroom-ai
```

```python
from vibo_headroom import compress_article

result = compress_article(article_html, model="gpt-4o")
# result["text"]         -> compressed text, ready for the agent context
# result["saved_pct"]    -> percent saved
# result["orig_tokens"]  -> tokens before
# result["comp_tokens"]  -> tokens after
```

CLI quick demo:

```bash
echo "Your article text..." | python3 vibo_headroom.py
```

### Interface Headroom exposes (what this depends on)

```python
from headroom import compress

result = compress(
    messages=[{"role": "user", "content": text}],  # OpenAI/Anthropic message list
    model="gpt-4o",                                  # used for token counting
    optimize=True,
)
# result.messages          -> compressed messages
# result.tokens_before     -> int
# result.tokens_after      -> int
# result.tokens_saved      -> int
# result.compression_ratio -> float (0..1)
```

---

## Direction B — Headroom agents gain persistent memory (MCP)

A Headroom-wrapped agent gets optional persistence via the ViBo MCP server.
No changes to Headroom — MCP is the contract.

```bash
npx @vibo-dev/vibo-mcp
# env: VIBO_API_KEY=<your ViBo key>  VIBO_BASE_URL=https://wwwvibo.com (default)
```

Tools: `memory_add` (store a fact, L1/L2/L3), `memory_search` (semantic recall),
`thread_memory`, `usage`.

```jsonc
// claude_desktop_config.json / cursor / any MCP client
{
  "mcpServers": {
    "vibo": {
      "command": "npx",
      "args": ["-y", "@vibo-dev/vibo-mcp"],
      "env": { "VIBO_API_KEY": "<key>" }
    }
  }
}
```

### Interface Headroom exposes (what this depends on)

Nothing — the MCP server advertises a standard tool list; any MCP client can call it.

---

## Who maintains what

- **ViBo team** maintains this adapter (`vibo_headroom.py`) and its tests.
- **Headroom** keeps its public Python API (`headroom.compress`) and MCP server stable.
