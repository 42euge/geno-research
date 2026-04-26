"""Dataset pipeline optimizer package.

Importing the package registers all built-in transforms and validators in
``transforms.registry.REGISTRY``.
"""

from . import transforms as _transforms  # noqa: F401  - registers built-ins
from . import validation as _validation  # noqa: F401  - registers validators

__version__ = "0.1.0"
