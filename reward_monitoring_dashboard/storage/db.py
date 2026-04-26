"""SQLite-backed storage for runs and samples.

The schema is intentionally minimal: one row per training sample, plus a runs
table holding metadata. SQLite gives us a single-file, local-first store with
no daemon, while still supporting indexed queries for the dashboard.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator


def default_db_path() -> Path:
    env = os.environ.get("REWARD_DASHBOARD_DB")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "data" / "rewards.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id      TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    metadata    TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS samples (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL,
    step          INTEGER NOT NULL,
    timestamp     TEXT NOT NULL,
    prompt        TEXT NOT NULL,
    output        TEXT NOT NULL,
    reward        REAL NOT NULL,
    task_type     TEXT NOT NULL DEFAULT 'unknown',
    output_length INTEGER NOT NULL,
    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_samples_run_step ON samples(run_id, step);
CREATE INDEX IF NOT EXISTS idx_samples_run_task ON samples(run_id, task_type);
"""


@dataclass
class Run:
    run_id: str
    name: str
    created_at: str
    metadata: dict[str, Any]


@dataclass
class Sample:
    run_id: str
    step: int
    timestamp: str
    prompt: str
    output: str
    reward: float
    task_type: str
    output_length: int


class Storage:
    """Thin wrapper around a SQLite connection.

    Safe to use from FastAPI: each call opens a short-lived connection. A lock
    serializes writes so concurrent ingestion from multiple processes is safe
    (SQLite handles this natively, but the lock avoids `database is locked`
    spam under heavy parallel ingest).
    """

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write_lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ----- runs --------------------------------------------------------------

    def upsert_run(self, run_id: str, name: str, created_at: str, metadata: dict) -> None:
        with self._write_lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs(run_id, name, created_at, metadata)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    name = excluded.name,
                    metadata = excluded.metadata
                """,
                (run_id, name, created_at, json.dumps(metadata)),
            )

    def list_runs(self) -> list[Run]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT run_id, name, created_at, metadata FROM runs ORDER BY created_at DESC"
            ).fetchall()
        return [
            Run(r["run_id"], r["name"], r["created_at"], json.loads(r["metadata"]))
            for r in rows
        ]

    def get_run(self, run_id: str) -> Run | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id, name, created_at, metadata FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if not row:
            return None
        return Run(row["run_id"], row["name"], row["created_at"], json.loads(row["metadata"]))

    def delete_run(self, run_id: str) -> bool:
        with self._write_lock, self._connect() as conn:
            cur = conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
            return cur.rowcount > 0

    # ----- samples -----------------------------------------------------------

    def insert_samples(self, samples: Iterable[Sample]) -> int:
        rows = [
            (
                s.run_id,
                s.step,
                s.timestamp,
                s.prompt,
                s.output,
                s.reward,
                s.task_type,
                s.output_length,
            )
            for s in samples
        ]
        if not rows:
            return 0
        with self._write_lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO samples
                    (run_id, step, timestamp, prompt, output, reward, task_type, output_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
        return len(rows)

    def fetch_samples(self, run_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, step, timestamp, prompt, output, reward, task_type, output_length
                FROM samples WHERE run_id = ? ORDER BY step ASC
                """,
                (run_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def page_samples(
        self,
        run_id: str,
        offset: int = 0,
        limit: int = 50,
        order_by: str = "step",
        descending: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        if order_by not in {"step", "reward", "output_length", "timestamp"}:
            order_by = "step"
        direction = "DESC" if descending else "ASC"
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM samples WHERE run_id = ?", (run_id,)
            ).fetchone()[0]
            rows = conn.execute(
                f"""
                SELECT id, step, timestamp, prompt, output, reward, task_type, output_length
                FROM samples WHERE run_id = ?
                ORDER BY {order_by} {direction}
                LIMIT ? OFFSET ?
                """,
                (run_id, limit, offset),
            ).fetchall()
        return [dict(r) for r in rows], total

    def get_sample(self, sample_id: int) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, run_id, step, timestamp, prompt, output, reward, task_type, output_length
                FROM samples WHERE id = ?
                """,
                (sample_id,),
            ).fetchone()
        return dict(row) if row else None
