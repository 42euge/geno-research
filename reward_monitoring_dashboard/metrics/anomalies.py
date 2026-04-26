"""Anomaly detection over reward time series.

Strategy: rolling z-score against a trailing window. Each sample is flagged
when |reward - rolling_mean| / rolling_std exceeds `z_threshold`. A trailing
(rather than centered) window means we only use information available up to
the sample, which mirrors how an online monitor would operate.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def detect_anomalies(
    samples: list[dict[str, Any]],
    window: int = 50,
    z_threshold: float = 3.0,
    min_samples: int = 10,
) -> list[dict[str, Any]]:
    if len(samples) < min_samples:
        return []
    df = pd.DataFrame(samples).sort_values("step").reset_index(drop=True)
    rewards = df["reward"].astype(float)
    rolling_mean = rewards.rolling(window, min_periods=min_samples).mean().shift(1)
    rolling_std = rewards.rolling(window, min_periods=min_samples).std().shift(1)
    z = (rewards - rolling_mean) / rolling_std.replace(0, np.nan)

    anomalies: list[dict[str, Any]] = []
    for idx, score in enumerate(z):
        if pd.isna(score) or abs(score) < z_threshold:
            continue
        row = df.iloc[idx]
        anomalies.append(
            {
                "id": int(row.get("id", idx)),
                "step": int(row["step"]),
                "timestamp": str(row.get("timestamp", "")),
                "reward": float(row["reward"]),
                "z_score": float(score),
                "rolling_mean": float(rolling_mean.iloc[idx]),
                "rolling_std": float(rolling_std.iloc[idx]),
                "task_type": str(row.get("task_type", "unknown")),
                "direction": "high" if score > 0 else "low",
            }
        )
    return anomalies
