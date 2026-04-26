"""Schema validation transforms."""

from __future__ import annotations

from typing import Any, Dict, List

from ..transforms.registry import register
from .errors import ValidationError


_TYPE_MAP = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": (int, float),
    "number": (int, float),
    "bool": bool,
    "boolean": bool,
    "list": list,
    "array": list,
    "dict": dict,
    "object": dict,
}


def _check_type(value: Any, type_name: str) -> bool:
    expected = _TYPE_MAP.get(type_name)
    if expected is None:
        raise ValidationError(f"unknown schema type: {type_name!r}")
    if isinstance(expected, tuple):
        return isinstance(value, expected) and not isinstance(value, bool) or (
            type_name in ("bool", "boolean") and isinstance(value, bool)
        )
    if expected is bool:
        return isinstance(value, bool)
    if expected is int:
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, expected)


@register("validate_schema")
def validate_schema(
    inputs,
    required: List[str] = None,
    types: Dict[str, str] = None,
    forbid_extra: bool = False,
) -> List[Dict[str, Any]]:
    """Validate every record against ``required`` keys and ``types`` map."""
    records = inputs[0]
    required = list(required or [])
    types = dict(types or {})
    allowed_extra = set(required) | set(types.keys())
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            raise ValidationError(f"record {i} is not a mapping: {type(r).__name__}")
        for key in required:
            if key not in r:
                raise ValidationError(f"record {i} missing required field {key!r}")
        for key, type_name in types.items():
            if key not in r:
                continue
            if not _check_type(r[key], type_name):
                raise ValidationError(
                    f"record {i} field {key!r}: expected {type_name}, "
                    f"got {type(r[key]).__name__}"
                )
        if forbid_extra:
            extra = set(r) - allowed_extra
            if extra:
                raise ValidationError(
                    f"record {i} has unexpected fields: {sorted(extra)}"
                )
    return records
