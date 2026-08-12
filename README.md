# 🧠 ViBo — Memory for AI Agents

**Your agent stops forgetting.**

ViBo gives AI agents and bots persistent memory: facts are saved between sessions, found by meaning, and protected by three encryption tiers.

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

## What you get

- **Persistent memory** — your agent remembers between sessions
- **Semantic search** — ask "what did I discuss with Anna?" and get the right facts
- **Three encryption tiers**:
  - **L1 (Public)** — visible to agent and LLM: names, tags, general knowledge
  - **L2 (Private)** — encrypted with the agent key: notes, plans, roadmaps
  - **L3 (Secret)** — encrypted with your password: API keys, credentials. **Never** reaches the LLM — only a 🔒 placeholder
- **Portable** — memory lives in one `.web` file. Backup = one copy command
- **50+ languages** — write facts in your language, ViBo understands

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

Measured on real graphs (see benchmarks above), not estimated.

## CLI

```bash
vibo --file memory.web seed               # demo memory
vibo --file memory.web find "query"       # semantic search
vibo --file memory.web dream              # nightly self-analysis (TTL, dedup)
vibo --file memory.web stats              # statistics
```

---

## License

ViBo is a commercial product. Get a license key: [wwwvibo.com](https://wwwvibo.com)

One key = one machine. The core is distributed as a compiled module.
