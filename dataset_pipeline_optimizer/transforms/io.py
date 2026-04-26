"""Loaders and writers for JSON, JSONL, CSV, and plain text."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List

from .registry import register


@register("load_jsonl")
def load_jsonl(_inputs, path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{i}: invalid JSON: {e}") from e
    return out


@register("load_json")
def load_json(_inputs, path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@register("load_csv")
def load_csv(_inputs, path: str, delimiter: str = ",") -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return [dict(row) for row in reader]


@register("load_text")
def load_text(_inputs, path: str, split_lines: bool = True):
    text = Path(path).read_text(encoding="utf-8")
    if split_lines:
        return [{"text": line} for line in text.splitlines() if line.strip()]
    return text


@register("write_jsonl")
def write_jsonl(inputs, path: str) -> Dict[str, Any]:
    records = inputs[0]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")
            n += 1
    return {"path": str(out), "count": n}


@register("write_json")
def write_json(inputs, path: str, indent: int = 2) -> Dict[str, Any]:
    data = inputs[0]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False, sort_keys=True)
    return {"path": str(out)}


@register("write_csv")
def write_csv(inputs, path: str, fields=None, delimiter: str = ",") -> Dict[str, Any]:
    records = inputs[0]
    if not records:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("", encoding="utf-8")
        return {"path": path, "count": 0}
    field_list = list(fields) if fields else sorted(records[0].keys())
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_list, delimiter=delimiter)
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k, "") for k in field_list})
    return {"path": str(out), "count": len(records)}
