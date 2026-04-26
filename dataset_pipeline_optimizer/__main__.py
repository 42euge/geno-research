"""Allow ``python -m dataset_pipeline_optimizer CONFIG ...``."""

from .cli.run_pipeline import main

if __name__ == "__main__":
    raise SystemExit(main())
