# ViBo benchmark

Real measured numbers, not marketing claims. Run it yourself:

```bash
# Python 3.11 + the ViBo core (a valid license)
VIBO_LIB=/path/to/vibo python3 benchmark.py
```

## Results (measured on this build)

| Test | Result |
|---|---|
| **Memory search** | 1000 facts → **22 tokens** in context vs **22 167 tokens** full dump → **99.9% fewer** |
| **Web compression** | 2 741 → **486 tokens** → **82.3% fewer** |

> Memory savings grow with the number of stored facts: the more memory, the
> more you save by sending only the relevant fragment instead of the whole dump.

## What it measures

1. **Memory search savings** — builds `N` synthetic facts, then runs one
   semantic search and compares the tokens returned in the context against
   dumping the entire memory into the prompt. `full_dump - context` is the
   saving.
2. **Web compression** — a realistic HTML page (navigation + ads + body) is
   compressed down to the relevant paragraphs.

## Reproduce

```bash
pip install -r requirements.txt  # fastembed + usearch (for the vector index)
VIBO_LIB=/path/to/vibo python3 benchmark.py
```

The numbers are deterministic for a given `N`; bump `bench_memory(n=...)` to
see how savings scale with memory size.
