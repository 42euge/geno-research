import os
import sys
from pathlib import Path

# Make the package importable when tests are run from the repo root.
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from reward_monitoring_dashboard.storage import Storage
from reward_monitoring_dashboard.storage.db import Sample


@pytest.fixture
def storage(tmp_path) -> Storage:
    db = tmp_path / "test.db"
    return Storage(db)


@pytest.fixture
def populated_storage(storage: Storage) -> Storage:
    storage.upsert_run("r1", "Test Run", "2026-04-26T00:00:00Z", {"seed": 1})
    samples = []
    for step in range(120):
        reward = 0.4 + 0.002 * step
        if step in (50, 90):
            reward = -0.9  # injected anomalies
        samples.append(
            Sample(
                run_id="r1",
                step=step,
                timestamp=f"2026-04-26T00:{step // 60:02d}:{step % 60:02d}Z",
                prompt=f"prompt {step}",
                output="o" * (100 + step),
                reward=reward,
                task_type="explanation" if step % 2 == 0 else "code",
                output_length=100 + step,
            )
        )
    storage.insert_samples(samples)
    return storage
