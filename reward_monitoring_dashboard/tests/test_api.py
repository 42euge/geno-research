import json

import pytest
from fastapi.testclient import TestClient

from reward_monitoring_dashboard.backend.app import create_app
from reward_monitoring_dashboard.storage.db import Sample


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "api.db"
    alerts = tmp_path / "alerts.yaml"
    alerts.write_text(
        "'*':\n"
        "  - name: low_mean\n"
        "    metric: mean\n"
        "    op: lt\n"
        "    threshold: 0.0\n"
        "    severity: critical\n"
    )
    monkeypatch.setenv("REWARD_DASHBOARD_ALERTS", str(alerts))
    app = create_app(db_path=db)
    return TestClient(app), db


def _seed(db_path, run_id="r1", n=120):
    from reward_monitoring_dashboard.storage import Storage
    store = Storage(db_path)
    store.upsert_run(run_id, f"Run {run_id}", "2026-04-26T00:00:00Z", {"seed": 42})
    samples = []
    for step in range(n):
        reward = 0.4 + 0.002 * step
        if step in (50, 90):
            reward = -0.9
        samples.append(Sample(run_id, step, "2026-04-26T00:00:00Z", "p", "out", reward, "qa", 100 + step))
    store.insert_samples(samples)


def test_health(client):
    c, _ = client
    assert c.get("/api/health").json() == {"status": "ok"}


def test_runs_list_empty(client):
    c, _ = client
    assert c.get("/api/runs").json() == []


def test_run_endpoints(client):
    c, db = client
    _seed(db)
    runs = c.get("/api/runs").json()
    assert len(runs) == 1
    assert runs[0]["run_id"] == "r1"

    detail = c.get("/api/runs/r1").json()
    assert detail["summary"]["count"] == 120
    assert detail["anomaly_count"] >= 2

    series = c.get("/api/runs/r1/series").json()
    assert len(series["steps"]) == 120

    dist = c.get("/api/runs/r1/distribution?bins=20").json()
    assert sum(dist["counts"]) == 120

    anomalies = c.get("/api/runs/r1/anomalies").json()
    assert any(a["step"] == 50 for a in anomalies)


def test_samples_pagination(client):
    c, db = client
    _seed(db)
    page1 = c.get("/api/runs/r1/samples?offset=0&limit=10").json()
    assert page1["total"] == 120
    assert len(page1["items"]) == 10
    sample_id = page1["items"][0]["id"]
    s = c.get(f"/api/samples/{sample_id}").json()
    assert s["step"] == 0


def test_compare(client):
    c, db = client
    _seed(db, run_id="a", n=40)
    _seed(db, run_id="b", n=40)
    data = c.get("/api/compare?runs=a,b").json()
    assert {r["run_id"] for r in data["runs"]} == {"a", "b"}


def test_404s(client):
    c, _ = client
    assert c.get("/api/runs/nope").status_code == 404
    assert c.get("/api/runs/nope/series").status_code == 404


def test_alerts_endpoint(client):
    c, db = client
    # Seed a run whose mean is negative so the global low_mean rule triggers.
    from reward_monitoring_dashboard.storage import Storage
    store = Storage(db)
    store.upsert_run("bad", "Bad", "2026-04-26T00:00:00Z", {})
    store.insert_samples([
        Sample("bad", i, "2026-04-26T00:00:00Z", "p", "o", -0.5, "qa", 10) for i in range(20)
    ])
    alerts = c.get("/api/runs/bad/alerts").json()
    assert any(a["name"] == "low_mean" for a in alerts)
