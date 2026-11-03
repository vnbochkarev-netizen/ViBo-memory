#!/usr/bin/env python3
"""ViBo preflight — tell the user what actually works on this host, before use.

Run it right after unpacking the skill:

    python3.11 tools/preflight.py [path-to-vibo-package]

Checks:
  1. interpreter version (the compiled core is CPython 3.11 only),
  2. the memory core (`vibo.core`, `vibo.vector_index`) imports,
  3. the optional compiled add-ons (`vibo_archive`, `license`) — these are
     built against a newer glibc and fail to load on older distributions,
  4. the semantic index round-trips (save + load), which is where a silent
     numpy/JSON mismatch used to wipe search.

Exit code: 0 = memory works (add-ons may be degraded, reported explicitly),
           1 = memory does not work — do not report ViBo as installed.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


def _load_pkg(pkg: Path) -> None:
    sys.path.insert(0, str(pkg))
    try:
        from vibo_json_shim import install

        install()
    except Exception:
        pass


def check_python() -> tuple[str, str]:
    v = sys.version_info
    if v[:2] == (3, 11):
        return OK, f"Python {v.major}.{v.minor}.{v.micro}"
    return FAIL, (
        f"Python {v.major}.{v.minor} — the ViBo core is compiled for CPython 3.11 only; "
        "3.10/3.12+ fail to import. Install 3.11 and re-run."
    )


def check_core() -> tuple[str, str]:
    try:
        from vibo.core import Graph  # noqa: F401
        from vibo.vector_index import VectorIndex  # noqa: F401

        return OK, "memory core imports (vibo.core, vibo.vector_index)"
    except Exception as exc:
        return FAIL, f"{type(exc).__name__}: {exc}"


def check_addons() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for label, mod in (("archive (.vibo)", "vibo_archive"), ("license", "license"),
                       ("memory tools", "vibo_memory_tools")):
        try:
            __import__(mod)
            out.append((label, OK, "imports"))
        except ImportError as exc:
            msg = str(exc)
            if "GLIBC_" in msg:
                ver = msg.split("GLIBC_")[1].split("'")[0]
                out.append((label, WARN,
                            f"needs glibc {ver}, this host has an older one — "
                            "not usable here (memory is unaffected)"))
            else:
                out.append((label, WARN, msg))
        except Exception as exc:
            out.append((label, WARN, f"{type(exc).__name__}: {exc}"))
    return out


def check_index() -> tuple[str, str]:
    """Save + reload an index with real embeddings — the path that used to fail silently."""
    try:
        from vibo.core import Graph
        from vibo.vector_index import VectorIndex

        graph = Graph()
        node = graph.add_node("preflight probe", "preflight probe about espresso", tags=[])
        node_id = getattr(node, "id", None) or list(graph.nodes)[-1]

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "probe.web.vec"
            idx = VectorIndex(path)
            idx.ensure_nodes(graph, node_ids=[node_id])
            idx.save()
            if not path.exists():
                return FAIL, "index file was not written (save() returned without error)"
            reloaded = VectorIndex(path)
            hits = reloaded.search("espresso", k=1)
            if not hits:
                return FAIL, "index file saved but reloads empty"
        return OK, "vector index saves and reloads (float32 serialization works)"
    except Exception as exc:
        return FAIL, f"{type(exc).__name__}: {exc}"


def main() -> int:
    ap = argparse.ArgumentParser(description="ViBo preflight check")
    ap.add_argument("package", nargs="?", default=".", help="directory with the ViBo package")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    pkg = Path(args.package).resolve()
    _load_pkg(pkg)

    rows: list[tuple[str, str, str]] = [("python",) + check_python()]
    core = check_core()
    rows.append(("memory core",) + core)
    index = check_index() if core[0] == OK else (FAIL, "skipped: core did not import")
    rows.append(("vector index",) + index)
    for row in check_addons():
        rows.append(row)

    memory_ok = core[0] == OK and index[0] == OK

    if args.json:
        print(json.dumps({"package": str(pkg), "memory_ok": memory_ok,
                          "checks": [{"name": n, "status": s, "detail": d} for n, s, d in rows]},
                         ensure_ascii=False, indent=2))
    else:
        print(f"ViBo preflight — {pkg}")
        width = max(len(n) for n, _, _ in rows)
        for name, status, detail in rows:
            mark = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}[status]
            print(f"  {mark} {name.ljust(width)}  {detail}")
        print()
        if memory_ok:
            print("Memory works on this host."
                  + ("" if all(s == OK for _, s, _ in rows)
                     else " Some add-ons are unavailable — see the warnings above."))
        else:
            print("Memory does NOT work here. Do not report ViBo as installed.")
    return 0 if memory_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
