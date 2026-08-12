# 💰 Save 50-150× Tokens with ViBo

### ⚡ Cheap token. Pay less. Same AI.

**Persistent memory for AI agents — cuts token costs by 50-150× on every request.**

ViBo gives AI agents and bots persistent memory: facts are saved between sessions, found by meaning, and protected by L1/L2/L3 encryption. Instead of loading ALL memory into every prompt, the agent retrieves only the relevant facts — so you pay for what you use, not for everything you know.

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue) ![License: MIT](https://img.shields.io/badge/License-MIT-green) ![Stars](https://img.shields.io/github/stars/vnbochkarev-netizen/ViBo-memory)

---

## ⚡ The headline number

| Without ViBo | With ViBo | Savings |
|---|---|---|
| 86,315 tokens per request (all memory) | 1-187 tokens (relevant facts) | **99.9%** |
| 10,000 facts → 155,000 tokens | ~2,000 tokens | **50-150×** |
| $130/month (DeepSeek, 6K req) | $2/month | **$128/month saved** |

Measured on real data. Not estimated.

---

## Why ViBo

Agents forget everything between sessions. Every conversation starts from zero:
- "Who is this client again?"
- "What did we agree on last week?"
- "Which API keys does this project use?"

ViBo fixes that. It's memory that actually works:

| Problem | Without ViBo | With ViBo |
|---|---|---|
| **Forgetting** | Agent starts blank every session | Facts persist across sessions |
| **Context cost** | Whole memory dumped into the prompt | Only relevant facts retrieved (50-150× fewer tokens) |
| **Secrets** | Keys and passwords can leak to the LLM | L1/L2/L3 encryption — secrets never reach the model |
| **Language** | Memory only in one language | Understands facts and search in 50+ languages |

---

## 🎥 Demo

![ViBo demo](https://github.com/vnbochkarev-netizen/ViBo-memory/raw/main/demo/vibo_demo.gif)

---

## What you get

- **Persistent memory** — your agent remembers between sessions
- **Semantic search** — ask "what did I discuss with Anna?" and get the right facts
- **Three encryption tiers**:
  - **L1 (Public)** — visible to agent and LLM: names, tags, general knowledge
  - **L2 (Private)** — encrypted with the agent key: notes, plans, roadmaps
  - **L3 (Secret)** — encrypted with your password: API keys, credentials. **Never** reaches the LLM — only a 🔒 placeholder
- **Portable** — memory lives in one `.web` file. Backup = one copy command
- **50+ languages** — write facts in your language, ViBo understands
- **Works with any agent** — Hermes, OpenClaw, LangChain, or your own (see INSTALL.md)

---

## Quick start

```python
from vibo.core import Graph
from vibo.crypto import Crypto, SecurityLevel
from vibo.web import WebFile
from vibo.navigator import ViBoNavigator

# Load memory (or create)
graph = WebFile("memory.web").read() if Path("memory.web").exists() else Graph()
crypto = Crypto(agent_key="my-agent-key", user_password="my-password")

# Save a fact
graph.add_node("Anna", "Client, loves coffee without sugar", tags=["person"])

# Save a secret (never reaches the LLM)
graph.add_node("api-key", crypto.seal(SecurityLevel.L3_SECRET, "sk-..."), level="L3")

# Ask memory
nav = ViBoNavigator(graph, crypto)
context = nav.compose("what about Anna")

# Save
WebFile("memory.web").write(graph, crypto=crypto)
```

---

## Measured results

| Memory size | Build | Search | Tokens saved |
|---|---|---|---|
| 1,000 facts | 0.00s | 39 ms | 37,450 (100%) |
| 10,000 facts | 0.02s | 145 ms | 374,950 (100%) |
| 50,000 facts | 0.12s | 700 ms | 1,874,950 (100%) |
| 100,000 facts | 0.33s | 1,261 ms | 3,749,950 (100%) |

Typical savings: **50-150× fewer tokens** (up to 2,000× on large memories). Measured, not estimated.

---

## 🌐 Product 2: Web Search Savings

Web search results are huge (5-15K tokens per article). Dumping them all
into the LLM context is expensive. ViBo compresses them first.

**Measured: 96.2% fewer tokens** (12,975 → 489 per article).

```python
from vibo_web import compress_article, WebCache

# Compress search results before the LLM sees them
for article in search_results:
    compressed, stats = compress_article(article["text"], query)
    article["text"] = compressed          # only the essence
    print(f"saved {stats['saved_pct']}%")

# Cache — repeated questions cost 0 tokens
cache = WebCache("web_cache.json")
if not cache.get(query):
    results = search(query)
    cache.put(query, results)
```

| Without ViBo | With ViBo |
|---|---|
| 10 articles × 12,975 tokens | 10 × 489 tokens |
| $0.018/query (DeepSeek) | $0.0007/query |
| repeated: paid again | repeated: **$0** |

---

## When does ViBo save you money?

Honest answer: **savings come from memory work, not code work.**

| Your agent does | Savings |
|---|---|
| Talks to people (support, sales, assistant) | **Huge savings** — memory grows, every conversation searches it |
| Works with big memory (10K+ facts) | **50-150×** — reads only relevant facts |
| Writes code | **Little to no savings** — code doesn't "remember" |
| Small memory (100 facts) | **~2×** — not much to save yet |

The bigger the memory, the bigger the savings. ViBo is about **memory work**:
chatting with clients, researching, consulting, planning — anything where
the agent needs to *recall* what it knows.

---

## The math: it pays for itself

Assumptions: 10K facts in memory, 6,000 requests/month (200/day), the agent reads all memory without ViBo. Prices per 1M input tokens.

| Model | Without ViBo | With ViBo | You save | ViBo cost |
|---|---|---|---|---|
| DeepSeek ($0.14/M) | $130/mo | $2/mo | **$128/mo** | $5 |

### Honest note (measured, not marketing)

Savings depend on **memory size**:

| Memory size | Savings |
|---|---|
| 100 facts | ~2× (measured: 62% fewer tokens) |
| 1,000 facts | 10-20× |
| 10,000 facts | **50-150×** (measured) |
| 100,000+ facts | up to 2,000× |

In the first days the memory is small, so savings grow over time as facts accumulate.

---

## How the savings work

Every request reads only the **relevant facts** instead of the whole memory:

```
Without ViBo: 10,000 facts → ~155,000 tokens → $0.022 (DeepSeek)
With ViBo:    ~2,000 tokens         → $0.0003
                                    → 50-150× fewer tokens
```

---

## CLI

```bash
vibo --file memory.web seed               # demo memory
vibo --file memory.web find "query"       # semantic search
vibo --file memory.web dream              # nightly self-analysis (TTL, dedup)
vibo --file memory.web stats              # statistics
vibo --file memory.web usage              # REAL savings: tokens & money saved
```

---

## Roadmap

- [x] Core memory engine (L1/L2/L3 encryption, semantic search)
- [x] .web portable format
- [x] CLI + Python API
- [x] LangChain adapter
- [x] Trial system (2 days, built-in key)
- [ ] MCP server (Model Context Protocol)
- [ ] Desktop GUI
- [ ] Team sharing (multi-user memory)
- [ ] Export to JSON/Markdown

---

## License

ViBo is a commercial product. Get a license key: [wwwvibo.com](https://wwwvibo.com)

One key = one machine. The core is distributed as a compiled module.
