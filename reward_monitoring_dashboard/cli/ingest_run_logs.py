"""CLI to ingest training-run logs into the dashboard's storage.

Usage:
    python -m reward_monitoring_dashboard.cli.ingest_run_logs \
        --file path/to/run.jsonl --run-id alpha --name "Alpha baseline"

Supported formats: JSONL (one JSON object per line) and CSV.

A "log line" must contain at minimum a `reward` field; the rest are filled in
with sensible defaults so noisy or partially-specified logs still work.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

import click

from ..storage import Storage, default_db_path
from ..storage.db import Sample


REQUIRED_FIELDS = {"reward"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                raise click.ClickException(f"{path}:{lineno}: invalid JSON ({e})")


def _iter_csv(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {k: v for k, v in row.items() if v != ""}


def _normalize(record: dict, run_id: str, fallback_step: int) -> Sample:
    if "reward" not in record:
        raise click.ClickException(f"record missing required field 'reward': {record}")
    try:
        reward = float(record["reward"])
    except (TypeError, ValueError) as e:
        raise click.ClickException(f"reward must be numeric, got {record['reward']!r}: {e}")

    prompt = str(record.get("prompt", ""))
    output = str(record.get("output", ""))
    task_type = str(record.get("task_type", "unknown"))
    timestamp = str(record.get("timestamp") or _now_iso())

    if "step" in record and record["step"] not in ("", None):
        step = int(record["step"])
    else:
        step = fallback_step

    if "output_length" in record and record["output_length"] not in ("", None):
        output_length = int(record["output_length"])
    else:
        output_length = len(output)

    return Sample(
        run_id=run_id,
        step=step,
        timestamp=timestamp,
        prompt=prompt,
        output=output,
        reward=reward,
        task_type=task_type,
        output_length=output_length,
    )


def _records_from(path: Path) -> Iterable[dict]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl" or suffix == ".ndjson":
        return _iter_jsonl(path)
    if suffix == ".csv":
        return _iter_csv(path)
    if suffix == ".json":
        # Allow a top-level JSON array too.
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise click.ClickException(f"{path}: expected a JSON array")
        return data
    raise click.ClickException(f"unsupported file type: {path.suffix}")


def ingest(
    file: Path,
    run_id: str,
    name: str | None,
    metadata: dict,
    db_path: Path | None,
) -> int:
    storage = Storage(db_path or default_db_path())
    storage.upsert_run(
        run_id=run_id,
        name=name or run_id,
        created_at=_now_iso(),
        metadata=metadata or {},
    )
    samples: list[Sample] = []
    for i, record in enumerate(_records_from(file)):
        samples.append(_normalize(record, run_id=run_id, fallback_step=i))
    return storage.insert_samples(samples)


@click.command()
@click.option("--file", "files", required=True, multiple=True, type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="Path to a JSONL/CSV/JSON log file. May be passed multiple times.")
@click.option("--run-id", required=True, help="Stable identifier for the run.")
@click.option("--name", default=None, help="Human-readable name (defaults to run-id).")
@click.option("--metadata", default="{}", help="JSON object with run metadata.")
@click.option("--db", "db_path", default=None, type=click.Path(path_type=Path),
              help="Override the SQLite database path.")
def main(files: tuple[Path, ...], run_id: str, name: str | None, metadata: str, db_path: Path | None) -> None:
    """Ingest one or more log files for a single run."""
    try:
        meta = json.loads(metadata)
        if not isinstance(meta, dict):
            raise ValueError("metadata must be a JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        raise click.ClickException(f"invalid --metadata: {e}")

    total = 0
    for path in files:
        n = ingest(path, run_id=run_id, name=name, metadata=meta, db_path=db_path)
        click.echo(f"ingested {n} samples from {path}")
        total += n
    click.echo(f"done — {total} samples for run {run_id}")


if __name__ == "__main__":
    main()
