"""Deduplication transforms."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional

from .registry import register


def _hash_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


@register("deduplicate")
def deduplicate(
    inputs,
    key: Optional[str] = None,
    keys: Optional[List[str]] = None,
    keep: str = "first",
) -> List[Dict[str, Any]]:
    if key is None and not keys:
        raise ValueError("deduplicate requires 'key' or 'keys'")
    if keys is None:
        keys = [key]

    def make_key(record):
        return tuple(record.get(k) for k in keys)

    records = inputs[0]
    if keep == "first":
        seen = set()
        out = []
        for r in records:
            k = make_key(r)
            if k in seen:
                continue
            seen.add(k)
            out.append(r)
        return out
    if keep == "last":
        bucket: Dict[Any, Any] = {}
        order: List[Any] = []
        for r in records:
            k = make_key(r)
            if k not in bucket:
                order.append(k)
            bucket[k] = r
        return [bucket[k] for k in order]
    raise ValueError(f"unknown 'keep' option: {keep!r}")


_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")


@register("deduplicate_normalized")
def deduplicate_normalized(
    inputs,
    field: str,
    lowercase: bool = True,
    strip_punct: bool = True,
) -> List[Dict[str, Any]]:
    """Dedup by a normalized form of ``field`` (whitespace / case / punctuation)."""
    seen = set()
    out = []
    for r in inputs[0]:
        text = str(r.get(field, ""))
        if lowercase:
            text = text.lower()
        if strip_punct:
            text = _PUNCT_RE.sub(" ", text)
        text = _WS_RE.sub(" ", text).strip()
        digest = _hash_text(text)
        if digest in seen:
            continue
        seen.add(digest)
        out.append(r)
    return out
