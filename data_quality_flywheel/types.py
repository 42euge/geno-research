"""Shared dataclasses used across the flywheel."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Transcript:
    """A single training transcript."""

    id: str
    prompt: str
    response: str
    metadata: dict[str, Any] = field(default_factory=dict)
    reward: float | None = None
    grade: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transcript":
        return cls(
            id=str(data["id"]),
            prompt=data.get("prompt", ""),
            response=data.get("response", ""),
            metadata=data.get("metadata", {}) or {},
            reward=data.get("reward"),
            grade=data.get("grade"),
        )


@dataclass
class Issue:
    """A detected quality issue on a transcript."""

    transcript_id: str
    issue_type: str
    severity: float  # 0.0 (mild) to 1.0 (severe)
    detector: str
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScore:
    """Aggregated quality score for a transcript."""

    transcript_id: str
    score: float  # 0.0 (worst) to 1.0 (best)
    components: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Fix:
    """A curation action to apply to a transcript."""

    transcript_id: str
    action: str  # "edit", "remove", "keep", "rewrite_response"
    new_prompt: str | None = None
    new_response: str | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
