"""Transform registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List


TransformFn = Callable[..., Any]


@dataclass
class Transform:
    name: str
    version: str
    fn: TransformFn

    def run(self, inputs: List[Any], params: Dict[str, Any]) -> Any:
        return self.fn(inputs, **params)


REGISTRY: Dict[str, Transform] = {}


def register(name: str, version: str = "1") -> Callable[[TransformFn], TransformFn]:
    def decorator(fn: TransformFn) -> TransformFn:
        if name in REGISTRY:
            raise ValueError(f"transform already registered: {name}")
        REGISTRY[name] = Transform(name=name, version=version, fn=fn)
        return fn

    return decorator
