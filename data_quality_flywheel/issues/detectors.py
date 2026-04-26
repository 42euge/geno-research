"""Issue detectors.

Each detector returns a list of ``Issue`` records. They're intentionally
cheap and dependency-free so they can run on the full dataset.

Tagged issue types:
    - low_signal
    - ambiguity
    - inconsistency
    - redundancy
    - duplicate
    - contradiction
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable

from ..types import Issue, QualityScore, Transcript


_WORD_RE = re.compile(r"\w+")
_NEGATIONS = (" not ", " never ", " no ", "n't ", " cannot ", " can't ")


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _shingles(tokens: list[str], n: int = 5) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def detect_duplicates(
    transcripts: list[Transcript], threshold: float = 0.85
) -> list[Issue]:
    """Find near-duplicate (prompt, response) pairs via 5-gram Jaccard."""
    sigs = [
        (t, _shingles(_tokens(f"{t.prompt} ||| {t.response}"))) for t in transcripts
    ]
    issues: list[Issue] = []
    for i in range(len(sigs)):
        ti, si = sigs[i]
        for j in range(i + 1, len(sigs)):
            tj, sj = sigs[j]
            sim = _jaccard(si, sj)
            if sim >= threshold:
                evidence = {"similar_to": tj.id, "similarity": round(sim, 3)}
                issues.append(
                    Issue(
                        transcript_id=ti.id,
                        issue_type="duplicate",
                        severity=min(1.0, sim),
                        detector="duplicates.jaccard5",
                        description=f"Near-duplicate of {tj.id} (sim={sim:.2f})",
                        evidence=evidence,
                    )
                )
    return issues


def detect_contradictions(transcripts: list[Transcript]) -> list[Issue]:
    """Group transcripts by similar prompt; flag pairs whose responses
    diverge sharply (high prompt similarity, low response similarity, with
    presence of negations)."""
    grouped: dict[tuple[str, ...], list[Transcript]] = defaultdict(list)
    for t in transcripts:
        key = tuple(sorted(set(_tokens(t.prompt)))[:8])
        if key:
            grouped[key].append(t)

    issues: list[Issue] = []
    for key, group in grouped.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                p_sim = _jaccard(set(_tokens(a.prompt)), set(_tokens(b.prompt)))
                r_sim = _jaccard(set(_tokens(a.response)), set(_tokens(b.response)))
                if p_sim < 0.6 or r_sim > 0.5:
                    continue
                a_neg = any(n in f" {a.response.lower()} " for n in _NEGATIONS)
                b_neg = any(n in f" {b.response.lower()} " for n in _NEGATIONS)
                if a_neg == b_neg:
                    continue
                severity = min(1.0, (p_sim - r_sim) + 0.2)
                issues.append(
                    Issue(
                        transcript_id=a.id,
                        issue_type="inconsistency",
                        severity=round(severity, 3),
                        detector="contradictions.negation_split",
                        description=(
                            f"Possible contradiction with {b.id} "
                            f"(prompt_sim={p_sim:.2f}, response_sim={r_sim:.2f})"
                        ),
                        evidence={
                            "compared_with": b.id,
                            "prompt_similarity": round(p_sim, 3),
                            "response_similarity": round(r_sim, 3),
                        },
                    )
                )
    return issues


def detect_low_quality(
    transcripts: list[Transcript],
    scores: list[QualityScore] | None = None,
    threshold: float = 0.5,
) -> list[Issue]:
    """Flag transcripts whose composite quality score is below threshold."""
    issues: list[Issue] = []
    by_id: dict[str, QualityScore] = {}
    if scores:
        by_id = {s.transcript_id: s for s in scores}
    for t in transcripts:
        s = by_id.get(t.id)
        if s is None:
            continue
        if s.score < threshold:
            severity = round(min(1.0, (threshold - s.score) / max(threshold, 1e-6)), 3)
            issues.append(
                Issue(
                    transcript_id=t.id,
                    issue_type="low_signal",
                    severity=severity,
                    detector="quality.threshold",
                    description=f"Quality score {s.score:.2f} below threshold {threshold}",
                    evidence={"score": s.score, "components": s.components},
                )
            )
    return issues


def detect_ambiguity(transcripts: list[Transcript]) -> list[Issue]:
    """Heuristic ambiguity flags:
    - very short prompts that ask open questions
    - prompts containing multiple distinct questions
    - hedging in the response without specifics
    """
    issues: list[Issue] = []
    hedges = ("maybe", "perhaps", "it depends", "could be", "i think", "possibly")
    for t in transcripts:
        prompt = t.prompt.strip()
        response = t.response.lower()
        prompt_tokens = _tokens(prompt)
        question_count = prompt.count("?")
        flags: list[str] = []

        if 0 < len(prompt_tokens) <= 4 and prompt.endswith("?"):
            flags.append("very_short_open_question")
        if question_count >= 2:
            flags.append("multiple_questions")
        hedge_hits = sum(response.count(h) for h in hedges)
        if hedge_hits >= 2:
            flags.append("hedging_response")

        if not flags:
            continue
        severity = min(1.0, 0.3 + 0.2 * len(flags))
        issues.append(
            Issue(
                transcript_id=t.id,
                issue_type="ambiguity",
                severity=round(severity, 3),
                detector="ambiguity.heuristics",
                description=", ".join(flags),
                evidence={"flags": flags, "question_count": question_count},
            )
        )
    return issues


def detect_redundancy(transcripts: list[Transcript]) -> list[Issue]:
    """Cluster identical (after normalization) prompts; the second-and-onward
    occurrences are flagged as redundant. Cheaper than full duplicate scan."""
    seen: dict[str, str] = {}
    issues: list[Issue] = []
    for t in transcripts:
        key = " ".join(_tokens(t.prompt))
        if not key:
            continue
        if key in seen:
            issues.append(
                Issue(
                    transcript_id=t.id,
                    issue_type="redundancy",
                    severity=0.5,
                    detector="redundancy.exact_prompt",
                    description=f"Prompt duplicates {seen[key]}",
                    evidence={"first_seen_id": seen[key]},
                )
            )
        else:
            seen[key] = t.id
    return issues


def detect_all(
    transcripts: list[Transcript],
    scores: list[QualityScore] | None = None,
    duplicate_threshold: float = 0.85,
    low_quality_threshold: float = 0.5,
) -> list[Issue]:
    """Run every detector and return a flat issue list."""
    out: list[Issue] = []
    out.extend(detect_low_quality(transcripts, scores, low_quality_threshold))
    out.extend(detect_ambiguity(transcripts))
    out.extend(detect_redundancy(transcripts))
    out.extend(detect_duplicates(transcripts, duplicate_threshold))
    out.extend(detect_contradictions(transcripts))
    return out


def group_by_transcript(issues: Iterable[Issue]) -> dict[str, list[Issue]]:
    grouped: dict[str, list[Issue]] = defaultdict(list)
    for issue in issues:
        grouped[issue.transcript_id].append(issue)
    return dict(grouped)
