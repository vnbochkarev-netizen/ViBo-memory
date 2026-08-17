# 🤝 ViBo Orchestrator

**One memory for your whole agent team.**

Team Memory for orchestrators: your agents write into a shared namespace, the
orchestrator reads one compact context block. No re-asking, no duplicates,
no forgotten decisions. Measured: up to **96% fewer tokens** per handoff on a
3-agent team.

## 30-second test

```bash
bash test_orchestra.sh
```

## Features

- `--namespace team:x` — shared team memory
- `vibo context` — one summary for the orchestrator
- `--by <agent>` — author on every fact
- `--ttl 6h` — metrics expire automatically
- Private facts never leak to the team

## Install

1. Unpack `vibo_orchestrator_1.0.0.zip`
2. Requires **Python 3.11**
3. `python3.11 activate.py` — free 2-day trial key by email, or your $5 key

## Demo limits (trial)

- Up to **50 facts**, up to **2 team namespaces**
- Full access: **$5/month — everything included** (memory, web savings,
  archives, privacy, team memory) → https://wwwvibo.com

## License

Proprietary — see [EULA.md](EULA.md). Licensor: Viacheslav Bochkarev.
Contact: hello@wwwvibo.com
