"""Reward statistics over a run's samples.

All functions accept a list of sample dicts (as returned by `Storage.fetch_samples`)
and return JSON-serializable dictionaries suitable for the API. We use pandas for
ergonomic group-bys but keep the public interface plain dicts so callers don't
need pandas to consume results.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _to_frame(samples: list[dict[str, Any]]) -> pd.DataFrame:
    if not samples:
        return pd.DataFrame(
            columns=["step", "timestamp", "reward", "task_type", "output_length"]
        )
    df = pd.DataFrame(samples)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.sort_values("step").reset_index(drop=True)
    return df


def summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    df = _to_frame(samples)
    if df.empty:
        return {
            "count": 0,
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "median": None,
            "p10": None,
            "p90": None,
            "first_step": None,
            "last_step": None,
            "mean_length": None,
        }
    rewards = df["reward"].to_numpy(dtype=float)
    return {
        "count": int(len(df)),
        "mean": float(np.mean(rewards)),
        "std": float(np.std(rewards, ddof=1)) if len(rewards) > 1 else 0.0,
        "min": float(np.min(rewards)),
        "max": float(np.max(rewards)),
        "median": float(np.median(rewards)),
        "p10": float(np.percentile(rewards, 10)),
        "p90": float(np.percentile(rewards, 90)),
        "first_step": int(df["step"].iloc[0]),
        "last_step": int(df["step"].iloc[-1]),
        "mean_length": float(df["output_length"].mean()),
    }


def time_series(
    samples: list[dict[str, Any]],
    window: int = 50,
) -> dict[str, Any]:
    """Per-step rewards plus a rolling mean/std envelope.

    The rolling window smooths noisy per-sample rewards into a trend the
    dashboard can plot. We use min_periods=1 so the curve starts immediately
    rather than after `window` steps.
    """
    df = _to_frame(samples)
    if df.empty:
        return {"steps": [], "rewards": [], "rolling_mean": [], "rolling_std": [], "window": window}
    win = max(1, min(window, len(df)))
    rolling = df["reward"].rolling(win, min_periods=1)
    return {
        "steps": df["step"].astype(int).tolist(),
        "timestamps": df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
        "rewards": df["reward"].astype(float).tolist(),
        "rolling_mean": rolling.mean().astype(float).tolist(),
        "rolling_std": rolling.std().fillna(0.0).astype(float).tolist(),
        "window": win,
    }


def distribution(samples: list[dict[str, Any]], bins: int = 30) -> dict[str, Any]:
    df = _to_frame(samples)
    if df.empty:
        return {"bin_edges": [], "counts": [], "bins": bins}
    counts, edges = np.histogram(df["reward"].to_numpy(dtype=float), bins=bins)
    return {
        "bin_edges": [float(e) for e in edges],
        "counts": [int(c) for c in counts],
        "bins": int(bins),
    }


def by_task(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    df = _to_frame(samples)
    if df.empty:
        return []
    grouped = df.groupby("task_type")["reward"].agg(
        count="count", mean="mean", std="std", min="min", max="max", median="median"
    )
    grouped["std"] = grouped["std"].fillna(0.0)
    out = []
    for task, row in grouped.iterrows():
        out.append(
            {
                "task_type": str(task),
                "count": int(row["count"]),
                "mean": float(row["mean"]),
                "std": float(row["std"]),
                "min": float(row["min"]),
                "max": float(row["max"]),
                "median": float(row["median"]),
            }
        )
    out.sort(key=lambda r: r["count"], reverse=True)
    return out


def length_correlation(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Pearson correlation between output length and reward, plus scatter data.

    A strong correlation can indicate reward-hacking via verbosity (or terseness),
    so we expose the coefficient + raw points the frontend can plot.
    """
    df = _to_frame(samples)
    if df.empty or len(df) < 2:
        return {"pearson": None, "n": int(len(df)), "points": []}
    lengths = df["output_length"].to_numpy(dtype=float)
    rewards = df["reward"].to_numpy(dtype=float)
    if np.std(lengths) == 0 or np.std(rewards) == 0:
        pearson = 0.0
    else:
        pearson = float(np.corrcoef(lengths, rewards)[0, 1])
    points = [
        {"length": int(l), "reward": float(r), "step": int(s)}
        for l, r, s in zip(lengths, rewards, df["step"].to_numpy())
    ]
    return {"pearson": pearson, "n": int(len(df)), "points": points}


def drift_score(samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare the first vs last quartile of the run.

    Returns the difference of means (positive = improving) and a normalized
    drift magnitude (delta / pooled std). This captures slow trends a rolling
    mean alone might smooth over.
    """
    df = _to_frame(samples)
    n = len(df)
    if n < 8:
        return {"early_mean": None, "late_mean": None, "delta": None, "normalized": None, "n": n}
    cut = max(1, n // 4)
    early = df["reward"].iloc[:cut].to_numpy(dtype=float)
    late = df["reward"].iloc[-cut:].to_numpy(dtype=float)
    delta = float(late.mean() - early.mean())
    pooled = float(np.sqrt((early.var(ddof=1) + late.var(ddof=1)) / 2)) if cut > 1 else 0.0
    normalized = float(delta / pooled) if pooled > 0 else None
    return {
        "early_mean": float(early.mean()),
        "late_mean": float(late.mean()),
        "delta": delta,
        "normalized": normalized,
        "n": n,
    }
