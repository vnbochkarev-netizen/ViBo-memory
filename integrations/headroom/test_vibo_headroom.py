"""End-to-end test for the ViBo + Headroom adapter.

Run: python3 test_vibo_headroom.py   (requires: pip install headroom-ai)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from vibo_headroom import compress_article  # noqa: E402


def main() -> int:
    # Realistic tool output: redundant JSON rows (headroom's bread and butter).
    rows = [
        {
            "id": i,
            "name": f"user_{i}",
            "email": f"user{i}@example.com",
            "status": "active",
            "role": "admin" if i % 2 else "member",
        }
        for i in range(80)
    ]
    data = json.dumps(rows)

    out = compress_article(data, model="gpt-4o", target_ratio=0.3)

    assert out["text"], "compressed text must not be empty"
    assert out["orig_tokens"] > 0, "orig_tokens must be positive"
    assert out["saved_tokens"] > 0, "expected real savings on redundant JSON"
    assert out["saved_pct"] > 0, "saved_pct must be positive"

    print(f"orig_tokens = {out['orig_tokens']}")
    print(f"comp_tokens = {out['comp_tokens']}")
    print(f"saved_tokens = {out['saved_tokens']}")
    print(f"saved_pct = {out['saved_pct']}%")
    print("PASS: ViBo + Headroom adapter compresses end-to-end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
