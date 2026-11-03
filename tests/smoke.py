#!/usr/bin/env python3
"""ViBo smoke test — the install path a customer actually walks.

Runs the shipped CLI against a throwaway memory base and fails loudly on the
three regressions that made 2.1.2 look broken on a clean machine:

  1. second `add` crashing (usearch 2.26 + the compiled vector_index),
  2. the `.vec` sidecar never being written (float32 not JSON serializable),
     which made every `find` answer "Memory is small",
  3. `find` not returning an added fact.

Usage:
    python tests/smoke.py <package-dir> [--expect-archive ok|fail]

<package-dir> must contain vibo_use.py and the compiled vibo/ package
(unpacked release zip, optionally overlaid with this repository's CLI fix).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

FACTS = [
    ("Клиент Анна", "предпочитает кофе без сахара, бюджет 10 тысяч рублей"),
    ("Сервер", "боевой сайт живёт на VPS в Москве, Ubuntu 22.04"),
    ("Договор", "оферта подписана 12 марта, срок оплаты 10 рабочих дней"),
]


class Failures(list):
    def check(self, condition: bool, message: str) -> None:
        if condition:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
            self.append(message)


def run(cli: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-u", str(cli), *args],
        capture_output=True, text=True, env=env, timeout=600,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="ViBo smoke test")
    ap.add_argument("package", help="directory with vibo_use.py + compiled vibo/")
    ap.add_argument("--expect-archive", choices=["ok", "fail"], default="ok",
                    help="'fail' on hosts whose glibc is too old for vibo_archive")
    args = ap.parse_args()

    pkg = Path(args.package).resolve()
    cli = pkg / "vibo_use.py"
    failures = Failures()

    print(f"ViBo smoke test — {pkg}")
    failures.check(cli.exists(), "vibo_use.py is present")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "memory.web"
        env = {**os.environ, "VIBO_MEM_FILE": str(base)}

        for label, content in FACTS:
            res = run(cli, env, "add", label, content)
            failures.check(
                res.returncode == 0 and "Added" in res.stdout,
                f"add «{label}» (rc={res.returncode})"
                + (f" stderr={res.stderr.strip()[:200]}" if res.returncode else ""),
            )

        vec = Path(str(base) + ".vec")
        failures.check(vec.exists() and vec.stat().st_size > 0,
                       f"vector index written ({vec.name})")

        res = run(cli, env, "find", "что предпочитает Анна?")
        failures.check(res.returncode == 0, f"find exits 0 (rc={res.returncode})")
        failures.check("Анна" in res.stdout, "find returns the added fact")
        failures.check("Memory is small" not in res.stdout,
                       "find does not fall back to «Memory is small»")

        res = run(cli, env, "reindex")
        failures.check(res.returncode == 0 and "Reindexed" in res.stdout,
                       "reindex rebuilds the sidecar")

        res = run(cli, env, "stats")
        failures.check("3/500" in res.stdout or "(3 nodes" in res.stdout
                       or "3/500" in res.stderr, "stats reports 3 facts")

    # The archive add-on is a separate compiled module: probe the import itself
    # (the CLI would only reach it once a real .vibo path is passed).
    probe = ("import sys; sys.path.insert(0, %r); import vibo_archive"
             % str(pkg))
    res = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    if args.expect_archive == "ok":
        failures.check(res.returncode == 0, "archive add-on importable")
    else:
        failures.check(
            res.returncode != 0 and "GLIBC" in res.stderr,
            "archive reports a clear glibc incompatibility (expected on this host)",
        )

    # The shim itself: numpy scalars must survive json.dumps.
    code = ("import sys, json; sys.path.insert(0, %r);"
            "from vibo_json_shim import install; install();"
            "import numpy as np; print(json.dumps({'v': np.float32(0.5)}))" % str(pkg))
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    ok = res.returncode == 0 and json.loads(res.stdout.strip() or "{}") == {"v": 0.5}
    failures.check(ok, "float32 embeddings serialize to JSON")

    print()
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
