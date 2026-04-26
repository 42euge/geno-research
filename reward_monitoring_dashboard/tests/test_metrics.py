from reward_monitoring_dashboard.metrics import (
    by_task,
    detect_anomalies,
    distribution,
    drift_score,
    length_correlation,
    summary,
    time_series,
)


def test_summary_empty():
    s = summary([])
    assert s["count"] == 0
    assert s["mean"] is None


def test_summary_basic(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    s = summary(samples)
    assert s["count"] == 120
    assert s["mean"] is not None
    assert s["min"] <= s["max"]
    assert s["first_step"] == 0
    assert s["last_step"] == 119


def test_time_series(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    ts = time_series(samples, window=10)
    assert len(ts["steps"]) == len(ts["rewards"]) == len(ts["rolling_mean"]) == 120
    assert ts["window"] == 10
    # Rolling mean should be monotonic-ish for the steady ascent (excluding anomalies)
    assert ts["rolling_mean"][-1] > ts["rolling_mean"][20]


def test_distribution(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    d = distribution(samples, bins=10)
    assert sum(d["counts"]) == 120
    assert len(d["bin_edges"]) == 11


def test_by_task(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    rows = by_task(samples)
    types = {r["task_type"] for r in rows}
    assert types == {"explanation", "code"}
    assert all(r["count"] == 60 for r in rows)


def test_length_correlation(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    lc = length_correlation(samples)
    assert lc["pearson"] is not None
    # length is tied to step which drives reward → positive correlation, dampened by anomaly spikes
    assert lc["pearson"] > 0.2
    assert len(lc["points"]) == 120


def test_drift_score(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    d = drift_score(samples)
    assert d["delta"] is not None
    assert d["late_mean"] > d["early_mean"]


def test_detect_anomalies_finds_spikes(populated_storage):
    samples = populated_storage.fetch_samples("r1")
    anomalies = detect_anomalies(samples, window=20, z_threshold=2.5)
    found_steps = {a["step"] for a in anomalies}
    # Steps 50 and 90 were injected as -0.9; both should be flagged.
    assert 50 in found_steps
    assert 90 in found_steps
    assert all(a["direction"] == "low" for a in anomalies if a["step"] in {50, 90})


def test_detect_anomalies_handles_short_runs():
    samples = [
        {"id": i, "step": i, "timestamp": "", "reward": 0.5, "task_type": "qa", "output_length": 10}
        for i in range(5)
    ]
    assert detect_anomalies(samples) == []
