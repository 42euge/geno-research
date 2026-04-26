"""Threshold-based alerting.

Rules are stored in a YAML file (default `data/alerts.yaml`) keyed by run_id
or by `*` for runs without a specific config. Each rule names a metric and a
threshold; when evaluated against a run's summary stats, violations are
returned as alert objects the API exposes.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AlertRule:
    name: str
    metric: str            # one of: mean, std, min, max, drift_delta, drift_normalized, anomaly_count
    op: str                # one of: lt, lte, gt, gte
    threshold: float
    severity: str = "warning"
    message: str | None = None

    def evaluate(self, value: float | None) -> bool:
        if value is None:
            return False
        if self.op == "lt":
            return value < self.threshold
        if self.op == "lte":
            return value <= self.threshold
        if self.op == "gt":
            return value > self.threshold
        if self.op == "gte":
            return value >= self.threshold
        raise ValueError(f"Unknown comparison op: {self.op}")


def load_alert_rules(path: Path | str, run_id: str) -> list[AlertRule]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r") as f:
        config = yaml.safe_load(f) or {}
    raw_rules: list[dict] = []
    raw_rules.extend(config.get("*", []) or [])
    raw_rules.extend(config.get(run_id, []) or [])
    rules = []
    for r in raw_rules:
        rules.append(
            AlertRule(
                name=r["name"],
                metric=r["metric"],
                op=r["op"],
                threshold=float(r["threshold"]),
                severity=r.get("severity", "warning"),
                message=r.get("message"),
            )
        )
    return rules


def evaluate_alerts(
    rules: list[AlertRule],
    summary_stats: dict[str, Any],
    drift: dict[str, Any],
    anomaly_count: int,
) -> list[dict[str, Any]]:
    metric_values: dict[str, float | None] = {
        "mean": summary_stats.get("mean"),
        "std": summary_stats.get("std"),
        "min": summary_stats.get("min"),
        "max": summary_stats.get("max"),
        "median": summary_stats.get("median"),
        "drift_delta": drift.get("delta"),
        "drift_normalized": drift.get("normalized"),
        "anomaly_count": float(anomaly_count),
    }
    triggered: list[dict[str, Any]] = []
    for rule in rules:
        value = metric_values.get(rule.metric)
        if rule.evaluate(value):
            triggered.append(
                {
                    "name": rule.name,
                    "metric": rule.metric,
                    "op": rule.op,
                    "threshold": rule.threshold,
                    "value": value,
                    "severity": rule.severity,
                    "message": rule.message
                    or f"{rule.metric} {rule.op} {rule.threshold} (was {value:.4f})",
                }
            )
    return triggered
