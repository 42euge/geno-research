from pathlib import Path

import yaml

from reward_monitoring_dashboard.metrics.alerts import (
    AlertRule,
    evaluate_alerts,
    load_alert_rules,
)


def test_alert_rule_evaluate():
    rule = AlertRule(name="x", metric="mean", op="lt", threshold=0.0)
    assert rule.evaluate(-0.1)
    assert not rule.evaluate(0.5)
    assert not rule.evaluate(None)


def test_evaluate_alerts_returns_violations():
    rules = [
        AlertRule(name="low", metric="mean", op="lt", threshold=0.0, severity="critical"),
        AlertRule(name="too_many", metric="anomaly_count", op="gt", threshold=2),
    ]
    triggered = evaluate_alerts(
        rules,
        summary_stats={"mean": -0.1, "std": 0.2, "min": -1, "max": 1, "median": 0},
        drift={"delta": 0.0, "normalized": 0.0},
        anomaly_count=5,
    )
    names = {a["name"] for a in triggered}
    assert names == {"low", "too_many"}


def test_load_alert_rules_merges_wildcard_and_run(tmp_path):
    cfg = tmp_path / "alerts.yaml"
    cfg.write_text(yaml.safe_dump({
        "*": [{"name": "global", "metric": "mean", "op": "lt", "threshold": 0.0}],
        "r1": [{"name": "specific", "metric": "std", "op": "gt", "threshold": 0.5}],
    }))
    rules = load_alert_rules(cfg, "r1")
    assert {r.name for r in rules} == {"global", "specific"}

    rules_other = load_alert_rules(cfg, "other")
    assert {r.name for r in rules_other} == {"global"}


def test_load_alert_rules_missing_file(tmp_path):
    assert load_alert_rules(tmp_path / "nope.yaml", "r1") == []
