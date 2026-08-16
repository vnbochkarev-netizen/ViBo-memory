#!/usr/bin/env python3
"""lib_vibo.py — thin Python client for the ViBo CLI (vibo_use.py).

The vibo-selfdeed skill uses ONLY this client to talk to memory:
add / find / usage / link / stats. The core (vibo/*.so) is not duplicated.

Notes (from acceptance review):
- vibo_use.py lookup: VIBO_CLI env → PATH → next to the skill → walk up (3 levels)
- interpreter: python3.11 (core .so) → python3
- find parses the real CLI output: "• [L1] label: content"

Usage:
    from lib_vibo import ViBo
    v = ViBo()
    v.find("project architecture")
    v.add("lesson", "do not use Y")
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


class ViBoError(RuntimeError):
    """Error while talking to the ViBo CLI."""


def _find_cli() -> str:
    """Find vibo_use.py: VIBO_CLI → PATH → next to the skill → walk up 3 levels.

    Security: VIBO_CLI is accepted only if it is an existing .py file
    (not an executable script/binary) — protects against path substitution.
    """
    env = os.environ.get("VIBO_CLI")
    if env:
        p = Path(env).expanduser()
        if p.is_file() and p.suffix == ".py":
            return str(p.resolve())
        raise ViBoError(
            f"VIBO_CLI must point to a .py file: {env!r} — rejected."
        )
    w = shutil.which("vibo_use.py")
    if w:
        return w
    here = Path(__file__).resolve().parent
    # next to the skill and walk up to 3 levels
    for depth in range(4):
        cand = here / "vibo_use.py"
        if cand.is_file():
            return str(cand.resolve())
        here = here.parent
    raise ViBoError(
        "vibo_use.py not found.\n"
        "→ Get ViBo (free tier: 500 facts forever, no card): https://wwwvibo.com/download/skill\n"
        "→ or 2-day trial: https://wwwvibo.com/download/trial\n"
        "Then set: export VIBO_CLI=/path/to/vibo_use.py"
    )


def _find_python() -> str:
    """python3.11 (core .so) → python3."""
    for name in ("python3.11", "python3"):
        p = shutil.which(name)
        if p:
            return p
    return sys.executable


class ViBo:
    """Thin wrapper over vibo_use.py (subprocess, no core import)."""

    def __init__(self, cli: str | Path | None = None, env: dict | None = None):
        self.cli = str(cli) if cli else _find_cli()
        self.python = _find_python()
        # Pass ONLY a safe minimum (whitelist) to the child process,
        # not the whole os.environ — env secrets never reach subprocess.
        self.env = {k: os.environ.get(k) for k in ("PATH", "HOME", "LANG", "LC_ALL")}
        self.env["VIBO_MEM_FILE"] = os.environ.get("VIBO_MEM_FILE", "memory.web")
        self.env = {k: v for k, v in self.env.items() if v is not None}
        if env:
            self.env.update(env)

    def _run(self, args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
        try:
            # vibo_use.py keeps memory.web relative to CWD — run the CLI
            # from its folder so it sees its own memory (acceptance fix v3).
            return subprocess.run(
                [self.python, self.cli, *args],
                capture_output=True, text=True, timeout=timeout, env=self.env,
                cwd=os.path.dirname(os.path.abspath(self.cli)),
            )
        except subprocess.TimeoutExpired as e:
            raise ViBoError(f"ViBo CLI timeout ({timeout}s)") from e

    # ── commands ────────────────────────────────────────────────────────

    def add(self, label: str, content: str = "", level: str = "L1", tags: list[str] | None = None) -> dict:
        """Save a fact. level: L1/L2/L3. Returns {'ok': bool, 'nodes': int, 'raw': str}."""
        args = ["add", label[:60]]
        if content:
            args += [content]
        if level != "L1":
            args += ["--level", level]
        for t in tags or []:
            args += ["--tag", t]
        r = self._run(args)
        out = (r.stdout or "").strip()
        m = re.search(r"\((\d+) nodes\)", out)
        return {"ok": r.returncode == 0, "nodes": int(m.group(1)) if m else 0,
                "raw": out, "exit": r.returncode}

    def find(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic search. Real CLI format:
        "• [L1] label: content"  →  {'label': ..., 'content': ..., 'level': 'L1'}.
        """
        r = self._run(["find", query, "--limit", str(limit)])
        facts: list[dict] = []
        line_re = re.compile(r"^\s*[•\-*]\s*\[([A-Z0-9]+)\]\s*([^:]+):\s?(.*)$")
        for line in (r.stdout or "").splitlines():
            m = line_re.match(line)
            if m:
                facts.append({"label": m.group(2).strip(),
                              "content": m.group(3).strip(),
                              "level": m.group(1)})
            if len(facts) >= limit:
                break
        return facts

    def usage(self) -> dict:
        """Real savings. Returns {'ok': bool, 'raw': str}."""
        r = self._run(["usage"])
        return {"ok": r.returncode == 0, "raw": (r.stdout or "").strip()}

    def link(self, a: str, b: str, rel: str = "related") -> dict:
        """Link two facts (by label)."""
        r = self._run(["link", a, b, "--rel", rel])
        return {"ok": r.returncode == 0, "raw": (r.stdout or "").strip(), "exit": r.returncode}

    def stats(self) -> dict:
        """Memory stats."""
        r = self._run(["stats"])
        raw = (r.stdout or "").strip()
        m = re.search(r"Nodes:\s*(\d+)/(\d+)", raw) or re.search(r"Nodes:\s*(\d+)", raw)
        nodes = int(m.group(1)) if m else 0
        return {"ok": r.returncode == 0, "nodes": nodes, "raw": raw}


if __name__ == "__main__":
    # CLI mode: python3 lib_vibo.py find "test" | stats | add ... | usage
    v = ViBo()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if cmd == "stats":
        print(json.dumps(v.stats(), ensure_ascii=False))
    elif cmd == "find":
        q = sys.argv[2] if len(sys.argv) > 2 else ""
        print(json.dumps(v.find(q), ensure_ascii=False, indent=1))
    elif cmd == "add":
        label = sys.argv[2] if len(sys.argv) > 2 else "test"
        content = sys.argv[3] if len(sys.argv) > 3 else ""
        print(json.dumps(v.add(label, content), ensure_ascii=False))
    elif cmd == "usage":
        print(json.dumps(v.usage(), ensure_ascii=False))
    else:
        print(__doc__)
