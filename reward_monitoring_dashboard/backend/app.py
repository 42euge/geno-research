"""FastAPI application exposing the dashboard API and serving the frontend."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from ..metrics import (
    by_task,
    detect_anomalies,
    distribution,
    drift_score,
    evaluate_alerts,
    length_correlation,
    load_alert_rules,
    summary,
    time_series,
)
from ..storage import Storage, default_db_path

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _alerts_path() -> Path:
    env = os.environ.get("REWARD_DASHBOARD_ALERTS")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "alerts.yaml"


def create_app(db_path: Path | str | None = None) -> FastAPI:
    storage = Storage(db_path or default_db_path())
    app = FastAPI(title="Reward Monitoring Dashboard", version="0.1.0")

    def get_storage() -> Storage:
        return storage

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/runs")
    def list_runs(store: Storage = Depends(get_storage)) -> list[dict[str, Any]]:
        runs = store.list_runs()
        out = []
        for r in runs:
            samples = store.fetch_samples(r.run_id)
            s = summary(samples)
            out.append(
                {
                    "run_id": r.run_id,
                    "name": r.name,
                    "created_at": r.created_at,
                    "metadata": r.metadata,
                    "summary": s,
                }
            )
        return out

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str, store: Storage = Depends(get_storage)) -> dict[str, Any]:
        run = store.get_run(run_id)
        if not run:
            raise HTTPException(404, f"Run {run_id} not found")
        samples = store.fetch_samples(run_id)
        s = summary(samples)
        d = drift_score(samples)
        anomalies = detect_anomalies(samples)
        rules = load_alert_rules(_alerts_path(), run_id)
        alerts = evaluate_alerts(rules, s, d, len(anomalies))
        return {
            "run_id": run.run_id,
            "name": run.name,
            "created_at": run.created_at,
            "metadata": run.metadata,
            "summary": s,
            "drift": d,
            "anomaly_count": len(anomalies),
            "alerts": alerts,
        }

    @app.delete("/api/runs/{run_id}")
    def delete_run(run_id: str, store: Storage = Depends(get_storage)) -> dict[str, Any]:
        if not store.delete_run(run_id):
            raise HTTPException(404, f"Run {run_id} not found")
        return {"deleted": run_id}

    @app.get("/api/runs/{run_id}/series")
    def series(
        run_id: str,
        window: int = Query(50, ge=1, le=10_000),
        store: Storage = Depends(get_storage),
    ) -> dict[str, Any]:
        _require_run(store, run_id)
        return time_series(store.fetch_samples(run_id), window=window)

    @app.get("/api/runs/{run_id}/distribution")
    def reward_distribution(
        run_id: str,
        bins: int = Query(30, ge=2, le=200),
        store: Storage = Depends(get_storage),
    ) -> dict[str, Any]:
        _require_run(store, run_id)
        return distribution(store.fetch_samples(run_id), bins=bins)

    @app.get("/api/runs/{run_id}/by_task")
    def task_breakdown(
        run_id: str, store: Storage = Depends(get_storage)
    ) -> list[dict[str, Any]]:
        _require_run(store, run_id)
        return by_task(store.fetch_samples(run_id))

    @app.get("/api/runs/{run_id}/length_corr")
    def length_corr(
        run_id: str, store: Storage = Depends(get_storage)
    ) -> dict[str, Any]:
        _require_run(store, run_id)
        return length_correlation(store.fetch_samples(run_id))

    @app.get("/api/runs/{run_id}/anomalies")
    def anomalies(
        run_id: str,
        window: int = Query(50, ge=2, le=10_000),
        z_threshold: float = Query(3.0, gt=0),
        store: Storage = Depends(get_storage),
    ) -> list[dict[str, Any]]:
        _require_run(store, run_id)
        return detect_anomalies(
            store.fetch_samples(run_id), window=window, z_threshold=z_threshold
        )

    @app.get("/api/runs/{run_id}/alerts")
    def run_alerts(
        run_id: str, store: Storage = Depends(get_storage)
    ) -> list[dict[str, Any]]:
        _require_run(store, run_id)
        samples = store.fetch_samples(run_id)
        s = summary(samples)
        d = drift_score(samples)
        a = detect_anomalies(samples)
        rules = load_alert_rules(_alerts_path(), run_id)
        return evaluate_alerts(rules, s, d, len(a))

    @app.get("/api/runs/{run_id}/samples")
    def run_samples(
        run_id: str,
        offset: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=500),
        order_by: str = Query("step"),
        descending: bool = Query(False),
        store: Storage = Depends(get_storage),
    ) -> dict[str, Any]:
        _require_run(store, run_id)
        rows, total = store.page_samples(
            run_id, offset=offset, limit=limit, order_by=order_by, descending=descending
        )
        return {"total": total, "offset": offset, "limit": limit, "items": rows}

    @app.get("/api/samples/{sample_id}")
    def get_sample(sample_id: int, store: Storage = Depends(get_storage)) -> dict[str, Any]:
        sample = store.get_sample(sample_id)
        if not sample:
            raise HTTPException(404, f"Sample {sample_id} not found")
        return sample

    @app.get("/api/compare")
    def compare(
        runs: str = Query(..., description="comma-separated run ids"),
        window: int = Query(50, ge=1, le=10_000),
        store: Storage = Depends(get_storage),
    ) -> dict[str, Any]:
        ids = [r.strip() for r in runs.split(",") if r.strip()]
        if not ids:
            raise HTTPException(400, "Provide at least one run id")
        out: list[dict[str, Any]] = []
        for rid in ids:
            run = store.get_run(rid)
            if not run:
                continue
            samples = store.fetch_samples(rid)
            out.append(
                {
                    "run_id": rid,
                    "name": run.name,
                    "summary": summary(samples),
                    "drift": drift_score(samples),
                    "series": time_series(samples, window=window),
                    "by_task": by_task(samples),
                }
            )
        return {"runs": out}

    if FRONTEND_DIR.exists():
        app.mount(
            "/static",
            StaticFiles(directory=FRONTEND_DIR / "static"),
            name="static",
        )

        @app.get("/")
        def root() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

        @app.get("/runs")
        def runs_page() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

        @app.get("/run/{run_id}")
        def run_page(run_id: str) -> FileResponse:
            return FileResponse(FRONTEND_DIR / "run.html")

        @app.get("/compare")
        def compare_page() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "compare.html")

    @app.exception_handler(ValueError)
    async def value_error_handler(_request, exc: ValueError):
        return JSONResponse({"error": str(exc)}, status_code=400)

    return app


def _require_run(store: Storage, run_id: str) -> None:
    if not store.get_run(run_id):
        raise HTTPException(404, f"Run {run_id} not found")


app = create_app()
