# Reward Monitoring Dashboard

A local-first dashboard and monitoring system that gives researchers visibility
into reward signal quality across RL/RLHF training runs.

## Features

- **Ingest training logs** from JSONL/CSV files via CLI
- **Reward statistics**: distribution, drift, variance, length correlation, per-task breakdown
- **Anomaly detection**: rolling z-score and threshold-based alerting
- **Compare runs**: overlay metrics from multiple runs side-by-side
- **Drill down**: inspect individual prompt/output samples per run
- **Local-first**: SQLite + FastAPI + vanilla JS, no cloud dependencies

## Architecture

```
reward_monitoring_dashboard/
├── backend/        # FastAPI app exposing /api/* and serving the frontend
├── storage/        # SQLite-backed persistence layer
├── metrics/        # Reward statistics & anomaly detection
├── frontend/       # Static HTML + Chart.js dashboard
├── cli/            # `ingest_run_logs` command-line entrypoint
├── data/           # Default location for the SQLite DB (gitignored)
├── examples/       # Sample log files for trying it out
└── tests/          # Pytest suite
```

## Quickstart

```bash
# 1. Install dependencies
pip install -r reward_monitoring_dashboard/requirements.txt

# 2. Ingest the example run
python -m reward_monitoring_dashboard.cli.ingest_run_logs \
    --file reward_monitoring_dashboard/examples/run_alpha.jsonl \
    --run-id alpha \
    --name "Alpha baseline" \
    --metadata '{"model":"policy-v1","seed":42}'

# 3. Start the dashboard
uvicorn reward_monitoring_dashboard.backend.app:app --reload --port 8000

# 4. Open http://localhost:8000/
```

## Log format

Each line of a JSONL file (or row of a CSV) should look like:

```json
{
  "timestamp": "2026-04-26T12:00:00Z",
  "step": 42,
  "prompt": "Explain quantum tunneling.",
  "output": "Quantum tunneling is...",
  "reward": 0.83,
  "task_type": "explanation",
  "output_length": 184
}
```

`output_length` is auto-computed from `output` if missing. `task_type` defaults
to `"unknown"`. `step` defaults to insertion order.

## CLI

```bash
python -m reward_monitoring_dashboard.cli.ingest_run_logs --help
```

## API

| Endpoint                         | Description                                   |
|----------------------------------|-----------------------------------------------|
| `GET /api/runs`                  | List all runs                                 |
| `GET /api/runs/{run_id}`         | Run metadata + headline metrics               |
| `GET /api/runs/{run_id}/series`  | Time-series of reward (with rolling stats)    |
| `GET /api/runs/{run_id}/distribution` | Reward histogram                         |
| `GET /api/runs/{run_id}/by_task` | Reward stats grouped by `task_type`           |
| `GET /api/runs/{run_id}/length_corr` | Reward vs. length correlation + scatter   |
| `GET /api/runs/{run_id}/anomalies` | Detected reward anomalies                   |
| `GET /api/runs/{run_id}/samples` | Paginated raw samples (drill-down)            |
| `GET /api/compare?runs=a,b,c`    | Side-by-side comparison payload               |

## Alerting (optional)

Threshold rules can be defined per run in `data/alerts.yaml`; the API surfaces
triggered alerts at `/api/runs/{run_id}/alerts`. See `docs/ALERTS.md` for the
schema.

## Tests

```bash
pytest reward_monitoring_dashboard/tests
```
