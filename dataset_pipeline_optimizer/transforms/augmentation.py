"""Augmentation transforms (cheap, deterministic variants)."""

from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from .registry import register


@register("augment_case")
def augment_case(
    inputs,
    field: str = "text",
    variants: List[str] = None,
    keep_original: bool = True,
) -> List[Dict[str, Any]]:
    """Emit case-variant copies (lower / upper / title)."""
    variants = variants or ["lower", "upper", "title"]
    out: List[Dict[str, Any]] = []
    for r in inputs[0]:
        if keep_original:
            out.append(r)
        text = str(r.get(field, ""))
        for v in variants:
            if v == "lower":
                value = text.lower()
            elif v == "upper":
                value = text.upper()
            elif v == "title":
                value = text.title()
            else:
                raise ValueError(f"unknown case variant: {v!r}")
            if value == text and keep_original:
                continue
            out.append({**r, field: value, "_augmentation": v})
    return out


_PARA_RE = re.compile(r"\n{2,}")


@register("augment_paragraph_split")
def augment_paragraph_split(
    inputs,
    field: str = "text",
    output_field: str = "text",
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in inputs[0]:
        text = str(r.get(field, ""))
        parts = [p.strip() for p in _PARA_RE.split(text) if p.strip()]
        if not parts:
            continue
        for part in parts:
            new = dict(r)
            new[output_field] = part
            out.append(new)
    return out


@register("shuffle")
def shuffle(inputs, seed: int = 0) -> List[Any]:
    records = list(inputs[0])
    rng = random.Random(seed)
    rng.shuffle(records)
    return records
