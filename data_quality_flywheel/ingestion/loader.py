"""Dataset loaders + normalization.

Supports JSON arrays, JSONL, and CSV with columns
(id, prompt, response, [reward], [grade], [metadata as JSON]).
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

from ..types import Transcript


_WHITESPACE_RE = re.compile(r"\s+")


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        return "jsonl"
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    raise ValueError(f"Unsupported dataset format: {path.suffix}")


def _stable_id(prompt: str, response: str, index: int) -> str:
    digest = hashlib.sha1(f"{prompt}\n---\n{response}".encode("utf-8")).hexdigest()[:10]
    return f"t{index:04d}_{digest}"


def _coerce_record(raw: dict, index: int) -> Transcript:
    prompt = raw.get("prompt") or raw.get("input") or raw.get("instruction") or ""
    response = raw.get("response") or raw.get("output") or raw.get("completion") or ""
    rid = raw.get("id") or _stable_id(prompt, response, index)
    metadata = raw.get("metadata") or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except json.JSONDecodeError:
            metadata = {"raw": metadata}
    reward = raw.get("reward")
    if reward is not None:
        try:
            reward = float(reward)
        except (TypeError, ValueError):
            reward = None
    grade = raw.get("grade")
    return Transcript(
        id=str(rid),
        prompt=str(prompt),
        response=str(response),
        metadata=metadata if isinstance(metadata, dict) else {},
        reward=reward,
        grade=str(grade) if grade is not None else None,
    )


def _read_json(path: Path) -> Iterable[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        # support {"data": [...]}
        data = data.get("data", [data])
    if not isinstance(data, list):
        raise ValueError("JSON dataset must be a list (or {'data': [...]})")
    return data


def _read_jsonl(path: Path) -> Iterable[dict]:
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _read_csv(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def load_dataset(path: str | Path) -> list[Transcript]:
    """Load a dataset from JSON, JSONL, or CSV into a list of Transcripts."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    fmt = _detect_format(path)
    if fmt == "json":
        records = _read_json(path)
    elif fmt == "jsonl":
        records = _read_jsonl(path)
    else:
        records = _read_csv(path)
    return [_coerce_record(r, i) for i, r in enumerate(records)]


def save_dataset(transcripts: list[Transcript], path: str | Path) -> Path:
    """Persist a dataset, format inferred from extension."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fmt = _detect_format(path)
    payload = [t.to_dict() for t in transcripts]
    if fmt == "json":
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    elif fmt == "jsonl":
        with path.open("w", encoding="utf-8") as fh:
            for row in payload:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=["id", "prompt", "response", "reward", "grade", "metadata"]
            )
            writer.writeheader()
            for row in payload:
                writer.writerow(
                    {
                        "id": row["id"],
                        "prompt": row["prompt"],
                        "response": row["response"],
                        "reward": row.get("reward"),
                        "grade": row.get("grade"),
                        "metadata": json.dumps(row.get("metadata") or {}),
                    }
                )
    return path


def normalize(transcripts: list[Transcript]) -> list[Transcript]:
    """Normalize text: strip, collapse whitespace, drop empty rows.

    Duplicate IDs are made unique by appending a suffix.
    """
    seen: dict[str, int] = {}
    out: list[Transcript] = []
    for t in transcripts:
        prompt = _WHITESPACE_RE.sub(" ", t.prompt or "").strip()
        response = _WHITESPACE_RE.sub(" ", t.response or "").strip()
        if not prompt and not response:
            continue
        tid = t.id
        if tid in seen:
            seen[tid] += 1
            tid = f"{tid}#{seen[tid]}"
        else:
            seen[tid] = 0
        out.append(
            Transcript(
                id=tid,
                prompt=prompt,
                response=response,
                metadata=dict(t.metadata or {}),
                reward=t.reward,
                grade=t.grade,
            )
        )
    return out
