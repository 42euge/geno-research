"""Generate example training-run logs for demoing the dashboard.

Produces three runs with deliberately different shapes so the dashboard's
charts and anomaly detection have something interesting to display:

    run_alpha.jsonl   - Healthy run that climbs steadily.
    run_beta.jsonl    - Run that plateaus then collapses (catastrophic drift).
    run_gamma.jsonl   - Run with reward-hacking via verbosity (length corr).
"""
from __future__ import annotations

import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
TASKS = ["explanation", "summarization", "code", "math", "qa"]
PROMPTS = {
    "explanation": "Explain the following concept clearly: {topic}.",
    "summarization": "Summarize this passage in 3 sentences: {topic}.",
    "code": "Write a Python function that {topic}.",
    "math": "Solve the following step by step: {topic}.",
    "qa": "Answer the question precisely: {topic}.",
}
TOPICS = ["entropy", "merge sort", "Fourier transforms", "RLHF", "kernels",
          "graph coloring", "Bayesian updating", "transformers", "TCP slow start"]


def synth_output(prompt: str, length: int) -> str:
    base = "Sure — here's a response. "
    body = " ".join(["lorem ipsum dolor sit amet"] * max(1, length // 28))
    return (base + body)[:length]


def write_run(path: Path, run_seed: int, n: int, profile: str) -> None:
    rng = random.Random(run_seed)
    start = datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)
    with path.open("w", encoding="utf-8") as f:
        for step in range(n):
            task = rng.choice(TASKS)
            topic = rng.choice(TOPICS)
            prompt = PROMPTS[task].format(topic=topic)

            if profile == "healthy":
                trend = 0.3 + 0.4 * (step / n)
                noise = rng.gauss(0, 0.08)
                reward = max(-1.0, min(1.0, trend + noise))
                length = int(120 + rng.gauss(0, 25))
            elif profile == "collapse":
                if step < int(0.7 * n):
                    reward = 0.6 + rng.gauss(0, 0.1)
                else:
                    decay = (step - 0.7 * n) / (0.3 * n)
                    reward = 0.6 - 0.9 * decay + rng.gauss(0, 0.12)
                length = int(140 + rng.gauss(0, 25))
            elif profile == "reward_hack":
                length = int(60 + step * 1.5 + rng.gauss(0, 15))
                reward = 0.2 + 0.6 * math.tanh(length / 200) + rng.gauss(0, 0.05)
            else:
                raise ValueError(profile)

            # Inject a couple of hard anomalies so detect_anomalies has something
            # to find.
            if profile == "healthy" and step in {n // 3, 2 * n // 3 + 4}:
                reward = -0.9

            length = max(20, length)
            timestamp = (start + timedelta(seconds=step * 30)).strftime("%Y-%m-%dT%H:%M:%SZ")
            record = {
                "step": step,
                "timestamp": timestamp,
                "prompt": prompt,
                "output": synth_output(prompt, length),
                "reward": round(reward, 4),
                "task_type": task,
                "output_length": length,
            }
            f.write(json.dumps(record) + "\n")


def main() -> None:
    write_run(HERE / "run_alpha.jsonl", run_seed=1, n=300, profile="healthy")
    write_run(HERE / "run_beta.jsonl", run_seed=2, n=300, profile="collapse")
    write_run(HERE / "run_gamma.jsonl", run_seed=3, n=300, profile="reward_hack")
    print(f"wrote example runs into {HERE}")


if __name__ == "__main__":
    main()
