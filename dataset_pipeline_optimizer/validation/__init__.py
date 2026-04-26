"""Schema and quality-check transforms.

Each validator is a registered transform: it returns its input unchanged on
success and raises ``ValidationError`` (a ValueError subclass) on failure.
This lets validators sit anywhere in the DAG.
"""

from . import schema as _schema  # noqa: F401  - registers transforms
from . import quality as _quality  # noqa: F401

from .errors import ValidationError

__all__ = ["ValidationError"]
