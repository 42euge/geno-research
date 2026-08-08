"""Lightweight content-addressed dataset versioning.

Each ``commit`` snapshots a dataset (as JSONL) plus optional metadata
(scores, iteration report, curation log). A linear log records the
sequence of versions so iteration improvements can be traced.

This is intentionally a stand-alone implementation (no git dependency)
so the flywheel runs in any environment.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ..types import Transcript


def _hash_dataset(transcripts: list[Transcript]) -> str:
    h = hashlib.sha256()
    for t in sorted(transcripts, key=lambda x: x.id):
        h.update(t.id.encode("utf-8"))
        h.update(b"\x00")
        h.update(t.prompt.encode("utf-8"))
        h.update(b"\x00")
        h.update(t.response.encode("utf-8"))
        h.update(b"\x01")
    return h.hexdigest()[:16]


class VersionStore:
    """A directory-backed dataset version store.

    Layout::

        <root>/
            log.jsonl                # one entry per commit, oldest first
            versions/<hash>.jsonl    # snapshotted dataset
            versions/<hash>.meta.json
    """

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.versions_dir = self.root / "versions"
        self.log_path = self.root / "log.jsonl"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()

    def commit(
        self,
        transcripts: list[Transcript],
        message: str,
        meta: dict[str, Any] | None = None,
    ) -> str:
        version_id = _hash_dataset(transcripts)
        snapshot = self.versions_dir / f"{version_id}.jsonl"
        with snapshot.open("w", encoding="utf-8") as fh:
            for t in transcripts:
                fh.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n")

        meta_path = self.versions_dir / f"{version_id}.meta.json"
        meta_payload = {
            "version_id": version_id,
            "size": len(transcripts),
            "created_at": time.time(),
            "message": message,
            "meta": meta or {},
        }
        meta_path.write_text(
            json.dumps(meta_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "version_id": version_id,
                        "message": message,
                        "size": len(transcripts),
                        "created_at": meta_payload["created_at"],
                    }
                )
                + "\n"
            )
        return version_id

    def history(self) -> list[dict]:
        if not self.log_path.exists():
            return []
        out: list[dict] = []
        with self.log_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def load(self, version_id: str) -> list[Transcript]:
        snapshot = self.versions_dir / f"{version_id}.jsonl"
        if not snapshot.exists():
            raise FileNotFoundError(version_id)
        out: list[Transcript] = []
        with snapshot.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(Transcript.from_dict(json.loads(line)))
        return out

    def meta(self, version_id: str) -> dict:
        meta_path = self.versions_dir / f"{version_id}.meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(version_id)
        return json.loads(meta_path.read_text(encoding="utf-8"))
