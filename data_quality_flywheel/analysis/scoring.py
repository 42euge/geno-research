"""Quality scoring: heuristics + optional model-based scoring.

Heuristic components are deterministic and zero-dependency. The
``ModelScorer`` adapter accepts any callable ``(prompt, response) -> float``
so a researcher can wire up their grader of choice (Anthropic Claude API,
a local reward model, a rubric LLM judge, etc.) without us depending on
that infrastructure here.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Callable

from ..types import QualityScore, Transcript


_WORD_RE = re.compile(r"\w+")
_REFUSAL_PATTERNS = (
    "i cannot",
    "i can't",
    "i am unable",
    "i'm unable",
    "as an ai",
    "i do not have",
    "sorry, but",
)
_LOW_SIGNAL_PATTERNS = (
    "i don't know",
    "n/a",
    "tbd",
    "todo",
    "not sure",
    "no answer",
)


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _length_score(text: str) -> float:
    """Reward responses that fall in a reasonable length window."""
    n = len(_tokenize(text))
    if n == 0:
        return 0.0
    if n < 5:
        return 0.2
    if n < 15:
        return 0.6
    if n < 400:
        return 1.0
    if n < 800:
        return 0.7
    return 0.4


def _diversity_score(text: str) -> float:
    """Type-token ratio, smoothed for short responses."""
    tokens = _tokenize(text)
    if not tokens:
        return 0.0
    unique = len(set(tokens))
    return min(1.0, unique / (math.sqrt(len(tokens)) + 1.0))


def _repetition_penalty(text: str) -> float:
    """Penalize responses where a few tokens dominate."""
    tokens = _tokenize(text)
    if len(tokens) < 8:
        return 1.0
    counts = Counter(tokens)
    top_share = sum(c for _, c in counts.most_common(3)) / len(tokens)
    return max(0.0, 1.0 - max(0.0, top_share - 0.4))


def _refusal_penalty(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for p in _REFUSAL_PATTERNS if p in lower)
    if hits == 0:
        return 1.0
    return max(0.0, 1.0 - 0.3 * hits)


def _low_signal_penalty(text: str) -> float:
    lower = text.lower().strip()
    if not lower:
        return 0.0
    for p in _LOW_SIGNAL_PATTERNS:
        if lower == p or lower.startswith(p + ".") or lower.startswith(p + " "):
            return 0.1
    if len(_tokenize(lower)) <= 2:
        return 0.2
    return 1.0


def _prompt_response_overlap(prompt: str, response: str) -> float:
    """Higher overlap (response just parrots prompt) -> lower score."""
    pset = set(_tokenize(prompt))
    rset = set(_tokenize(response))
    if not pset or not rset:
        return 1.0
    overlap = len(pset & rset) / len(rset)
    return max(0.0, 1.0 - max(0.0, overlap - 0.6))


def _reward_component(reward: float | None) -> float | None:
    if reward is None:
        return None
    # Squash to [0, 1] assuming reward is in [-1, 1] but tolerate any range.
    if -1.0 <= reward <= 1.0:
        return (reward + 1.0) / 2.0
    return 1.0 / (1.0 + math.exp(-reward))


def score_transcript(
    transcript: Transcript,
    model_scorer: Callable[[str, str], float] | None = None,
) -> QualityScore:
    """Compute a 0..1 quality score for a single transcript."""
    prompt = transcript.prompt
    response = transcript.response

    components: dict[str, float] = {
        "length": _length_score(response),
        "diversity": _diversity_score(response),
        "repetition": _repetition_penalty(response),
        "refusal": _refusal_penalty(response),
        "low_signal": _low_signal_penalty(response),
        "prompt_overlap": _prompt_response_overlap(prompt, response),
    }

    reward_c = _reward_component(transcript.reward)
    if reward_c is not None:
        components["reward"] = reward_c

    if model_scorer is not None:
        try:
            model_score = float(model_scorer(prompt, response))
            components["model"] = max(0.0, min(1.0, model_score))
        except Exception as exc:  # noqa: BLE001 - record failure, don't crash
            components["model_error"] = 0.0
            components["model_error_msg"] = exc  # type: ignore[assignment]

    weights = {
        "length": 0.10,
        "diversity": 0.10,
        "repetition": 0.10,
        "refusal": 0.10,
        "low_signal": 0.20,
        "prompt_overlap": 0.10,
        "reward": 0.15,
        "model": 0.15,
    }
    total_w = 0.0
    total = 0.0
    for k, v in components.items():
        if k not in weights or not isinstance(v, (int, float)):
            continue
        total += weights[k] * float(v)
        total_w += weights[k]
    score = total / total_w if total_w else 0.0

    clean_components = {
        k: float(v) for k, v in components.items() if isinstance(v, (int, float))
    }
    return QualityScore(
        transcript_id=transcript.id, score=round(score, 4), components=clean_components
    )


def score_dataset(
    transcripts: list[Transcript],
    model_scorer: Callable[[str, str], float] | None = None,
) -> list[QualityScore]:
    return [score_transcript(t, model_scorer) for t in transcripts]


class ModelScorer:
    """Adapter for plugging in arbitrary model-based scorers.

    Example:
        def my_judge(prompt, response):
            # call your reward model / LLM judge
            return 0.8
        scorer = ModelScorer(my_judge)
        score_transcript(t, scorer)
    """

    def __init__(self, fn: Callable[[str, str], float]):
        self._fn = fn

    def __call__(self, prompt: str, response: str) -> float:
        return float(self._fn(prompt, response))
