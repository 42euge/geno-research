"""Curation tools: flag, edit, or remove transcripts.

The expected workflow is:

  1. Run ``suggest_fixes`` (or write the template) to produce a JSONL
     file of one Fix per transcript.
  2. A human reviewer edits that file (changing ``action`` or filling in
     ``new_response``).
  3. ``apply_fixes`` replays the file against the dataset and produces a
     cleaned dataset plus a curation log.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from ..types import Fix, Issue, Transcript


SEVERITY_REMOVE = 0.85
SEVERITY_EDIT = 0.5


def suggest_fixes(
    transcripts: list[Transcript], issues: list[Issue]
) -> list[Fix]:
    """Heuristic suggestions a human can override.

    Defaults:
      - duplicate / redundancy with high severity -> remove
      - low_signal -> rewrite_response (placeholder)
      - inconsistency -> edit (flag for human review)
      - everything else -> keep
    """
    by_id: dict[str, list[Issue]] = defaultdict(list)
    for issue in issues:
        by_id[issue.transcript_id].append(issue)

    fixes: list[Fix] = []
    for t in transcripts:
        bucket = by_id.get(t.id, [])
        if not bucket:
            fixes.append(Fix(transcript_id=t.id, action="keep", reason="no issues"))
            continue
        max_sev = max(i.severity for i in bucket)
        types = sorted({i.issue_type for i in bucket})
        reason = f"types={','.join(types)}; severity={max_sev:.2f}"

        if any(i.issue_type in {"duplicate", "redundancy"} and i.severity >= SEVERITY_REMOVE for i in bucket):
            fixes.append(Fix(transcript_id=t.id, action="remove", reason=reason))
        elif any(i.issue_type == "low_signal" and i.severity >= SEVERITY_EDIT for i in bucket):
            fixes.append(
                Fix(
                    transcript_id=t.id,
                    action="rewrite_response",
                    new_response=None,
                    reason=reason,
                )
            )
        elif any(i.issue_type in {"inconsistency", "ambiguity"} for i in bucket):
            fixes.append(Fix(transcript_id=t.id, action="edit", reason=reason))
        else:
            fixes.append(Fix(transcript_id=t.id, action="keep", reason=reason))
    return fixes


def write_fixes_template(fixes: list[Fix], path: str | Path) -> Path:
    """Write fixes as JSONL ready for human review."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for fix in fixes:
            fh.write(json.dumps(fix.to_dict(), ensure_ascii=False) + "\n")
    return path


def load_fixes(path: str | Path) -> list[Fix]:
    """Read a fixes JSONL file (e.g., after human edits)."""
    out: list[Fix] = []
    with Path(path).open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            out.append(
                Fix(
                    transcript_id=str(data["transcript_id"]),
                    action=data.get("action", "keep"),
                    new_prompt=data.get("new_prompt"),
                    new_response=data.get("new_response"),
                    reason=data.get("reason", ""),
                )
            )
    return out


def apply_fixes(
    transcripts: list[Transcript], fixes: Iterable[Fix]
) -> tuple[list[Transcript], list[dict]]:
    """Apply fixes to a dataset.

    Returns ``(cleaned, log)``. Transcripts not referenced in ``fixes`` are
    kept as-is. Unknown actions are treated as ``keep`` and logged.
    """
    fix_map: dict[str, Fix] = {f.transcript_id: f for f in fixes}
    cleaned: list[Transcript] = []
    log: list[dict] = []
    for t in transcripts:
        fix = fix_map.get(t.id)
        if fix is None:
            cleaned.append(t)
            continue
        action = fix.action
        if action == "remove":
            log.append({"id": t.id, "action": "remove", "reason": fix.reason})
            continue
        if action == "edit":
            new = Transcript(
                id=t.id,
                prompt=fix.new_prompt if fix.new_prompt is not None else t.prompt,
                response=fix.new_response if fix.new_response is not None else t.response,
                metadata={**t.metadata, "curation_reason": fix.reason},
                reward=t.reward,
                grade=t.grade,
            )
            cleaned.append(new)
            log.append({"id": t.id, "action": "edit", "reason": fix.reason})
            continue
        if action == "rewrite_response":
            if fix.new_response is None:
                # No human rewrite supplied; drop to avoid keeping a known-bad row.
                log.append(
                    {
                        "id": t.id,
                        "action": "drop_pending_rewrite",
                        "reason": fix.reason,
                    }
                )
                continue
            new = Transcript(
                id=t.id,
                prompt=t.prompt,
                response=fix.new_response,
                metadata={**t.metadata, "curation_reason": fix.reason, "rewritten": True},
                reward=t.reward,
                grade=t.grade,
            )
            cleaned.append(new)
            log.append({"id": t.id, "action": "rewrite_response", "reason": fix.reason})
            continue
        # keep / unknown
        cleaned.append(t)
        log.append({"id": t.id, "action": "keep", "reason": fix.reason})
    return cleaned, log
