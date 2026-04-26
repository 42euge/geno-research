"""Content-addressed cache for intermediate results.

Cache keys are SHA-1 hashes of:
  - the transform name + version
  - the canonical JSON of params
  - the upstream cache keys (in dependency order)

If any of those change, the key changes; otherwise we reuse the stored value.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


@dataclass
class CacheEntry:
    key: str
    path: Path

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> Any:
        with open(self.path, "rb") as f:
            return pickle.load(f)

    def store(self, value: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".pkl.tmp")
        with open(tmp, "wb") as f:
            pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(self.path)


class Cache:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def compute_key(
        transform_name: str,
        transform_version: str,
        params: dict,
        upstream_keys: Iterable[str],
    ) -> str:
        payload = {
            "transform": transform_name,
            "version": transform_version,
            "params": _canonical(params),
            "upstream": list(upstream_keys),
        }
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha1(blob).hexdigest()

    def entry(self, key: str) -> CacheEntry:
        return CacheEntry(key=key, path=self.root / f"{key}.pkl")

    def get(self, key: str) -> Optional[Any]:
        entry = self.entry(key)
        if not entry.exists():
            return None
        return entry.load()

    def put(self, key: str, value: Any) -> None:
        self.entry(key).store(value)

    def clear(self) -> None:
        for p in self.root.glob("*.pkl"):
            p.unlink()


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    return value
