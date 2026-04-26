#!/usr/bin/env python3
"""Top-level shim so users can run ``python run_pipeline.py CONFIG`` from
inside the project directory without worrying about module paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in (None, ""):
    # Make the parent of this file importable so absolute imports of the
    # ``dataset_pipeline_optimizer`` package resolve.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataset_pipeline_optimizer.cli.run_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main())
