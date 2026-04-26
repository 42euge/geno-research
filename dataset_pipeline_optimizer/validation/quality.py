"""Quality-check transforms."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..transforms.registry import register
from .errors import ValidationError


@register("assert_min_count")
def assert_min_count(inputs, min_count: int) -> List[Any]:
    records = inputs[0]
    if len(records) < min_count:
        raise ValidationError(
            f"min_count={min_count} not satisfied (got {len(records)})"
        )
    return records


@register("assert_max_count")
def assert_max_count(inputs, max_count: int) -> List[Any]:
    records = inputs[0]
    if len(records) > max_count:
        raise ValidationError(
            f"max_count={max_count} exceeded (got {len(records)})"
        )
    return records


@register("assert_unique")
def assert_unique(inputs, field: str) -> List[Dict[str, Any]]:
    seen: Dict[Any, int] = {}
    records = inputs[0]
    for i, r in enumerate(records):
        v = r.get(field)
        if v in seen:
            raise ValidationError(
                f"duplicate value {v!r} for field {field!r} "
                f"(records {seen[v]} and {i})"
            )
        seen[v] = i
    return records


@register("assert_no_nulls")
def assert_no_nulls(inputs, fields: List[str] = None) -> List[Dict[str, Any]]:
    records = inputs[0]
    keys: Optional[List[str]] = list(fields) if fields else None
    for i, r in enumerate(records):
        check = keys if keys is not None else list(r.keys())
        for k in check:
            if r.get(k) in (None, ""):
                raise ValidationError(
                    f"record {i} has null/empty field {k!r}"
                )
    return records
