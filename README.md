# 💰 ViBo — Memory for AI Agents + Living Document Archive

**One license. One key. Your agent remembers — and your documents think.**

<a href="https://wwwvibo.com"><img src="https://img.shields.io/badge/website-wwwvibo.com-22c55e" alt="site"></a>
<a href="https://t.me/ViBomemorybot"><img src="https://img.shields.io/badge/Telegram-@ViBomemorybot-blue" alt="tg"></a>
<a href="https://wwwvibo.com/archive"><img src="https://img.shields.io/badge/Archive-live%20demo-22c55e" alt="archive"></a>


📖 **The Living Archive: How My Agent Started Working Through ViBo** — [read the story](docs/LIVING_ARCHIVE.md)

## What it is

**ViBo Memory** — persistent memory for AI agents: facts survive between sessions, found by meaning, encrypted L1/L2/L3. Agent reads only relevant facts → **50-150× fewer tokens** on large bases (measured).

**ViBo Archive** — a living document archive in our own `.vibo` format: compressed (~84%), searched by meaning, answers questions in milliseconds. LLM reads 22 KB instead of 146 KB.

## How to use

```bash
vibo add "client Anna" "prefers espresso, budget 10K"
vibo find "what does Anna prefer?"

vibo archive pack ./contracts -o archive.vibo
vibo archive search archive.vibo "total amount and deadline?"
vibo archive unpack archive.vibo -o ./restored
```

- **Skill** — drop into any Python agent (Hermes, OpenClaw, LangChain).
- **n8n** — verified node [n8n-nodes-vibo](https://github.com/vnbochkarev-netizen/n8n-nodes-vibo).
- **Dify** — plugin (PR in review).
- **Cloud API** — memory for your SaaS.

## What it is for

- **Banks** — "What did we promise this client?" → milliseconds. Secrets stay encrypted (L3).
- **Archives** — millions of pages stop being dust.
- **Libraries** — "What is this book about?" → instant.
- **Law firms** — a question instead of hours of searching.
- **Medicine** — patient histories, protocols, studies.
- **Business** — knowledge bases that answer 24/7.

## Honest measurements

| Memory | Tokens saved |
|---|---|
| 100 facts | ~2× |
| 1K facts | 10-20× |
| 10K+ facts | 50-150× |
| 100K+ facts | up to 2,000× |

Web search: 96-99%. Threads: -72%. Archive: 84%, 0.1s. **Empty memory = 0 savings.**

## Pricing

One license, $5/month (first 100 users keep **$2.5 forever**). Cloud API $5/10/25. 2-day free trial.

Get it from [@ViBomemorybot](https://t.me/ViBomemorybot) or [wwwvibo.com](https://wwwvibo.com).

---

*Dust is no longer dust. Dust is memory that was waiting for its hour.*

## 🚀 Projects

| Project | What it is | Link |
|---|---|---|
| **ViBo Memory** | Persistent memory for AI agents — 50-150× fewer tokens, L1/L2/L3 encryption | [site](https://wwwvibo.com) |
| **ViBo Archive** | Living document archive (.vibo) — 84% compression, search by meaning, answers in ms | [demo](https://wwwvibo.com/archive) |
| **Cloud API** | Memory for your SaaS — instant, encrypted, zero infrastructure | [site](https://wwwvibo.com) |
| **n8n node** | Verified node for n8n workflows | [npm](https://www.npmjs.com/package/n8n-nodes-vibo) |
| **Dify plugin** | Memory tools for Dify (search, add, thread, usage) | [PR](https://github.com/langgenius/dify-plugins/pull/2886) |
| **MCP server** | Model Context Protocol server for AI tools | [registry](https://registry.modelcontextprotocol.io) |
| **Telegram bot** | Get the key, manage subscription, support | [@ViBomemorybot](https://t.me/ViBomemorybot) |

All projects share one license, one key, one product.

*Dust is no longer dust. Dust is memory that was waiting for its hour.*
