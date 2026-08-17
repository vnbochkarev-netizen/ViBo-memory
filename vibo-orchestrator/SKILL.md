---
name: vibo-orchestrator
description: Use when your agent team needs ONE shared memory — Team Memory for orchestrators (namespace, context summary, authors, TTL). Try it in 30 seconds.
version: 1.0.0
license: proprietary (see EULA.md)
---

# 🤝 ViBo Orchestrator — Team Memory for agent teams

**One memory for your whole agent team.** Your agents write into a shared
namespace; the orchestrator reads one compact context block — no re-asking,
no duplicates, no forgotten decisions.

Measured on a 3-agent team: the orchestrator gets **3 facts instead of 3 full
conversation histories** (up to 96% fewer tokens per handoff).

## Why orchestrators need it

| Without ViBo | With ViBo Orchestrator |
|---|---|
| Each agent forgets everything between sessions | Team remembers collectively (shared namespace) |
| Orchestrator re-asks or dumps full histories | One `context` summary — 3 facts, not megabytes |
| No way to tell who wrote what | `--by` author on every fact |
| Stale metrics pile up forever | `--ttl` — metrics expire automatically |

## Quick test — 30 seconds

```bash
bash test_orchestra.sh
```

You will see: 3 agents write to `team:demo` → the orchestrator reads **one
summary** → personal facts stay private → metrics expire by TTL.

## Install

1. Copy the skill folder to your agent's skills directory (or unpack
   `vibo_orchestrator_1.0.0.zip`).
2. Requires **Python 3.11**.
3. Activate with your ViBo key (trial keys are free for 2 days by email):

```bash
python3.11 activate.py
```

## Commands

```bash
# An agent writes to the shared team namespace
python3.11 vibo_use.py add "agent-1" "disk 48G free" --namespace team:demo --by sys-agent --ttl 6h

# The orchestrator reads ONE summary for the whole team
python3.11 vibo_use.py context --namespace team:demo
# → # ViBo shared context «team:demo»: 3 facts
# → • [sys-agent] agent-1: disk 48G free

# Private facts never leak to the team (no --namespace = personal)
python3.11 vibo_use.py add "personal" "my secret"

# Metrics expire automatically
python3.11 vibo_use.py add "metric" "load 0.1" --namespace team:demo --by sys-agent --ttl 3s
```

## Limits (trial)

- **Free trial (2 days, by email):** up to 50 facts, up to 2 team namespaces.
- **Full access:** one license, $5/month — everything included (memory, web
  savings, archives, privacy, team memory). Get your key at https://wwwvibo.com.

## Files

```
vibo_use.py          # CLI (add/find/context/archive/resume/version)
activate.py          # trial key by email / full key activation
check_license.py     # license check
vibo/                # protected components (compiled)
SKILL.md             # this file
EULA.md              # license agreement
test_orchestra.sh    # 30-second team-memory test
```

## More

- Docs: https://wwwvibo.com
- Contact: hello@wwwvibo.com
- Licensor: Viacheslav Bochkarev
