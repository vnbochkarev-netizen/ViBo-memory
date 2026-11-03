# Installing ViBo on Ubuntu 22.04 / Debian 12 (glibc < 2.38)

**Short version:** memory works, three add-ons do not — and 2.1.2 gave no hint
about it. This page is the honest compatibility matrix plus the workarounds.

## What breaks and why

The release ships pre-compiled CPython 3.11 modules. Three of them were built on
a newer toolchain than the rest and require **glibc 2.38** (Ubuntu 24.04+):

| Module | Product | Needs |
|---|---|---|
| `vibo/*.so` | memory (add / find / link / stats / resume) | glibc 2.14 ✅ |
| `vibo_archive.so` | Living Archive (`.vibo` pack / search / unpack) | glibc 2.38 ❌ |
| `license.so` | `check_license.py`, `vibo_verify.py` | glibc 2.38 ❌ |
| `vibo_memory_tools.so` | tool wrappers | glibc 2.38 ❌ |

On Ubuntu 22.04 / Debian 12 the import fails with:

```
ImportError: /lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.38' not found
```

`python3.11 tools/preflight.py` reports the exact state of the box:

```
  ✅ python           Python 3.11.17
  ✅ memory core      memory core imports (vibo.core, vibo.vector_index)
  ✅ vector index     vector index saves and reloads (float32 serialization works)
  ⚠️  archive (.vibo)  needs glibc 2.38, this host has an older one — not usable here (memory is unaffected)
```

## What to do today

1. Install the runtime with the pinned requirements — **not** a bare
   `pip install fastembed usearch`:

   ```bash
   python3.11 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   ```

   `usearch` must stay at `2.15.0`: 2.26.x makes the second `add` die with
   `SIGSEGV` right after writing the fact.

2. Use the CLI that ships with this branch (`vibo_use.py` + `vibo_json_shim.py`).
   Without it the `.vec` index is silently never written and every `find`
   answers «Memory is small» — the memory looks empty while `stats` shows facts.

3. If a base was already written by 2.1.2, repair it once:

   ```bash
   .venv/bin/python vibo_use.py reindex
   ```

4. If you need the archive on this host today: run it on Ubuntu 24.04 (a small
   container or a second VPS is enough — `.vibo` files are portable).

## What has to change in the build

* Rebuild `vibo_archive`, `license`, `vibo_memory_tools` against
  **manylinux_2_17** (or a glibc 2.35 toolchain) instead of the current
  toolchain. One wheel per Python version, built in the oldest image you intend
  to support — that is the only durable fix.
* Keep `vibo/*.so` on the same baseline so the whole package has a single
  glibc floor.
* The CI matrix in `.github/workflows/smoke.yml` runs the released package on
  both 24.04 and 22.04, so a regression like this shows up on the release
  commit instead of on a customer's machine. Once the modules are rebuilt,
  flip `expect_archive` for the 22.04 job from `fail` to `ok`.
