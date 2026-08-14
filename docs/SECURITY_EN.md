# 🔒 ViBo Security — how we protect your data

*Ready answer when a client asks "how do you protect my data?"*

---

## 1. Three-tier encryption (L1/L2/L3)

| Tier | What it is | How it's protected |
|---|---|---|
| **L1 — Public** | General facts (skills, preferences) | Safe by default |
| **L2 — Private** | Personal data, history | **AES-256-GCM**, encrypted at rest |
| **L3 — Secrets** | Passwords, keys, medical data, strategies | **NEVER reach the LLM**. The agent knows a secret exists — but never receives its value |

**Key point:** the LLM physically cannot leak what it never saw.

## 2. Cryptography (verifiable)

- **AES-256-GCM** — industry-standard encryption
- **PBKDF2 600,000 iterations** — 30× beyond the OWASP password standard
- **Each client key = a separate encryption key**
- The key is NOT stored on our server — it stays with the client (local-first)

## 3. Local-first storage (default)

```
Your memory = a file on YOUR machine (memory.web)
It is encrypted. Without your key it's random bytes.
No one (including us) can read it.
```

## 4. Cloud API (if you use it)

| Protection | How |
|---|---|
| Isolation | Each key = separate file (`/data/memories/<hash>.web`) |
| Encryption | File encrypted with the owner's key |
| Client A ≠ Client B | Different keys = different files = no mixing |
| Server | Non-root (UID 10001), Docker, no external SSH |
| Transport | HTTPS (TLS) on all requests |

## 5. Honesty & transparency

- We publish **where ViBo does NOT help** (code-gen, small memory) — no empty promises
- Savings metrics are **real measurements**, not marketing
- 2-day free trial without a card — test us before paying
- Support is a **real human** (not a bot): hello@wwwvibo.com

## 6. What we NEVER do

- ❌ Never sell or share your data with third parties
- ❌ Never send your secrets into the LLM (L3)
- ❌ Never store your key on the server
- ❌ Never spy on your memory (it's encrypted)

---

## 🎯 One-sentence answer to the client:
> "Your data is encrypted (AES-256-GCM), secrets never reach the
> LLM (L3), the file lives on your machine, and we cannot read it
> without your key. Try it free — no card required."
