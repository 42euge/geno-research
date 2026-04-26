"""Reusable transform operations.

Each transform is registered in ``REGISTRY`` and exposes a ``run(inputs, **params)``
callable. Inputs are positional values from upstream nodes (in dependency order).
"""

from .registry import REGISTRY, Transform, register
from . import io as _io  # noqa: F401  - registers loaders/writers
from . import filtering as _filtering  # noqa: F401
from . import dedup as _dedup  # noqa: F401
from . import formatting as _formatting  # noqa: F401
from . import augmentation as _augmentation  # noqa: F401

__all__ = ["REGISTRY", "Transform", "register"]
