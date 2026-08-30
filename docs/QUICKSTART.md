# ViBo quickstart (2 minutes)

1. Install: `openclaw skills install @vnbochkarev-netizen/vibo-memory`
2. Setup: `python3 vibo_use.py setup <password>` (L3 secrets)
3. Save: `python3 vibo_use.py add "project X" "decided: use Y" --tag project`
4. Find: `python3 vibo_use.py find "project X"`
5. Verify: `python3 vibo_use.py verify "claim about X" --report`
6. Ask (memory + web): `python3 vibo_use.py ask "question"`
7. Savings: `python3 vibo_use.py usage`

Tips:
- `VIBO_MEM_FILE` env overrides the store path; the store resolves next to the script by default.
- Facts are L1 (public) by default; use `--level L2` for private, L3 for secrets.
- `ask` saves web answers into memory automatically — the store grows with use.
