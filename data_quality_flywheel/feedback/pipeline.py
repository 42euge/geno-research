"""Feedback pipeline: reinsert improved samples and build iteration reports.

The flywheel: detect -> surface -> fix -> reinsert -> track. This module
handles the ``reinsert`` and ``track`` steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..analysis import score_dataset
from ..issues import detect_all
from ..types import Issue, QualityScore, Transcript


@dataclass
class IterationReport:
    iteration: int
    size_before: int
    size_after: int
    removed: int
    edited: int
    rewritten: int
    avg_score_before: float
    avg_score_after: float
    issue_counts_before: dict[str, int]
    issue_counts_after: dict[str, int]

    def to_dict(self) -> dict:
        return self.__dict__


def reinsert(
    base: list[Transcript],
    improved: Iterable[Transcript],
    *,
    dedupe: bool = True,
) -> list[Transcript]:
    """Merge improved samples back into the base dataset.

    Improved samples replace any existing transcript with a matching ID.
    If ``dedupe`` is True, IDs not in either set are preserved.
    """
    by_id: dict[str, Transcript] = {t.id: t for t in base}
    for t in improved:
        by_id[t.id] = t
    if not dedupe:
        # caller wants raw concatenation
        return list(base) + list(improved)
    return list(by_id.values())


def _avg(scores: list[QualityScore]) -> float:
    if not scores:
        return 0.0
    return round(sum(s.score for s in scores) / len(scores), 4)


def _issue_counts(issues: Iterable[Issue]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i in issues:
        out[i.issue_type] = out.get(i.issue_type, 0) + 1
    return out


def build_iteration_report(
    iteration: int,
    before: list[Transcript],
    after: list[Transcript],
    curation_log: list[dict],
) -> IterationReport:
    """Score before/after and summarize what changed."""
    scores_before = score_dataset(before)
    scores_after = score_dataset(after)
    issues_before = detect_all(before, scores_before)
    issues_after = detect_all(after, scores_after)

    removed = sum(1 for e in curation_log if e["action"] == "remove")
    edited = sum(1 for e in curation_log if e["action"] == "edit")
    rewritten = sum(1 for e in curation_log if e["action"] == "rewrite_response")

    return IterationReport(
        iteration=iteration,
        size_before=len(before),
        size_after=len(after),
        removed=removed,
        edited=edited,
        rewritten=rewritten,
        avg_score_before=_avg(scores_before),
        avg_score_after=_avg(scores_after),
        issue_counts_before=_issue_counts(issues_before),
        issue_counts_after=_issue_counts(issues_after),
    )
