# Changelog

## 2.2.0 — 2026-11-16

### Changed
- Archive and maintenance now run on pure Python implementations. The binary
  modules `vibo_archive` and `vibo_memory_tools` are no longer shipped.
- New archives use their own magic (`VIBOARCH2`), a format version field and the
  recommended extension `.vibox`. Older `.vibo` archives stay readable (read-only
  legacy reader, detected by content, never overwritten).
- `install.sh` refuses a package that contains any of the removed modules,
  including renamed copies.
- `preflight.py` reports the environment matrix (OS, architecture, libc, Python
  ABI) and the GLIBC requirement of every shipped module.
- The CLI wrapper resolves its own path, so it runs from any directory, from a
  chroot and from a container.

### Compatibility
- Requires Python 3.11 exactly (ABI limit of the compiled core).
- CLI commands and the on-disk memory file are unchanged; existing memory bases
  and archives open without migration.
- `usearch` pinned to `>=2.15,<2.26` — 2.26 crashes the index on the first write.

### Fixed
- Maintenance could make stored L2 facts unreadable; the base is now verified
  after every write and restored from a local backup on mismatch.
- Cleanup no longer deletes facts that share a label but differ in content; it
  only removes exact duplicates and reports conflicts.

### Tested
- Ubuntu 22.04 (glibc 2.35, Python 3.11.17): pass.
- Debian 12 (glibc 2.36, Python 3.11.9): pass.
- Python 3.10 and 3.12 on the same host: fail at import (expected, ABI).
