"""numpy-aware JSON serialization for the ViBo index sidecar.

Why this exists
---------------
``vibo.vector_index.VectorIndex.save()`` (compiled) packs embedding values with
``json.dumps()``, and the embeddings come back from the embedder as
``numpy.float32``. numpy scalars are not JSON serializable, so ``save()`` raised
``TypeError: Object of type float32 is not JSON serializable``. In ``vibo_use.py``
that call sat inside ``except Exception: pass``, so the ``.vec`` sidecar was never
written while ``add`` kept printing "✅ Added" — and every ``find`` answered
"Memory is small", i.e. semantic search did nothing on a fresh install.

The permanent fix belongs in the compiled module (``float(v)`` before packing).
Until that module is rebuilt, this shim keeps numpy scalars serializable so the
index reaches disk.

Usage: ``from vibo_json_shim import install; install()`` — idempotent, never
raises.
"""

from __future__ import annotations

import json

_INSTALLED = False


def install() -> bool:
    """Teach the stdlib JSON encoder numpy scalars. Returns True if active."""
    global _INSTALLED
    if _INSTALLED:
        return True
    try:
        import numpy as np

        def _numpy_to_json(obj):
            if isinstance(obj, np.generic):
                return obj.item()
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            raise TypeError(
                f"Object of type {obj.__class__.__name__} is not JSON serializable"
            )

        # Encoders built with default=None delegate to this shared instance.
        shared = getattr(json, "_default_encoder", None)
        if shared is not None:
            shared.default = _numpy_to_json
        json.JSONEncoder.default = lambda self, o: _numpy_to_json(o)
        _INSTALLED = True
    except Exception:
        return False
    return _INSTALLED
