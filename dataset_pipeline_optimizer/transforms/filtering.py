"""Record filtering transforms."""

from __future__ import annotations

from typing import Any, Dict, List

from .registry import register


_ALLOWED_BUILTINS: Dict[str, Any] = {
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "sum": sum,
    "any": any,
    "all": all,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "set": set,
    "sorted": sorted,
    "round": round,
}


def _safe_eval(expr: str, record: Dict[str, Any]) -> Any:
    """Evaluate a predicate against ``record``.

    ``__builtins__`` is removed so the expression cannot reach ``open``,
    ``__import__`` etc. Only the helpers in ``_ALLOWED_BUILTINS`` plus the
    ``record`` binding are exposed.
    """
    globals_ = {"__builtins__": {}}
    locals_ = {"record": record, **_ALLOWED_BUILTINS}
    return eval(expr, globals_, locals_)  # noqa: S307 - sandboxed expr


@register("filter_records")
def filter_records(inputs, where: str) -> List[Dict[str, Any]]:
    records = inputs[0]
    return [r for r in records if _safe_eval(where, r)]


@register("filter_min_length")
def filter_min_length(inputs, field: str, min_length: int) -> List[Dict[str, Any]]:
    records = inputs[0]
    return [r for r in records if len(str(r.get(field, ""))) >= min_length]


@register("filter_max_length")
def filter_max_length(inputs, field: str, max_length: int) -> List[Dict[str, Any]]:
    records = inputs[0]
    return [r for r in records if len(str(r.get(field, ""))) <= max_length]


@register("drop_fields")
def drop_fields(inputs, fields: List[str]) -> List[Dict[str, Any]]:
    drop = set(fields)
    return [{k: v for k, v in r.items() if k not in drop} for r in inputs[0]]


@register("keep_fields")
def keep_fields(inputs, fields: List[str]) -> List[Dict[str, Any]]:
    keep = list(fields)
    return [{k: r.get(k) for k in keep} for r in inputs[0]]


@register("sample")
def sample(inputs, n: int = None, fraction: float = None, seed: int = 0):
    import random

    records = list(inputs[0])
    rng = random.Random(seed)
    if n is None and fraction is None:
        raise ValueError("sample requires 'n' or 'fraction'")
    if fraction is not None:
        n = max(0, int(round(len(records) * float(fraction))))
    n = min(int(n), len(records))
    indices = sorted(rng.sample(range(len(records)), n))
    return [records[i] for i in indices]
