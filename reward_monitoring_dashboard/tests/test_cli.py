import json
from pathlib import Path

from click.testing import CliRunner

from reward_monitoring_dashboard.cli.ingest_run_logs import main
from reward_monitoring_dashboard.storage import Storage


def _write_jsonl(path: Path, n: int) -> None:
    with path.open("w") as f:
        for i in range(n):
            f.write(json.dumps({
                "step": i,
                "timestamp": "2026-04-26T00:00:00Z",
                "prompt": f"prompt {i}",
                "output": "x" * (50 + i),
                "reward": 0.5,
                "task_type": "qa",
            }) + "\n")


def _write_csv(path: Path, n: int) -> None:
    with path.open("w") as f:
        f.write("step,reward,prompt,output,task_type\n")
        for i in range(n):
            f.write(f"{i},0.5,p{i},out{i},qa\n")


def test_ingest_jsonl(tmp_path):
    log = tmp_path / "run.jsonl"
    db = tmp_path / "db.sqlite"
    _write_jsonl(log, 25)
    runner = CliRunner()
    result = runner.invoke(main, [
        "--file", str(log),
        "--run-id", "alpha",
        "--name", "Alpha",
        "--metadata", '{"seed":1}',
        "--db", str(db),
    ])
    assert result.exit_code == 0, result.output
    assert "ingested 25" in result.output

    storage = Storage(db)
    runs = storage.list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "alpha"
    assert runs[0].metadata == {"seed": 1}
    assert len(storage.fetch_samples("alpha")) == 25


def test_ingest_csv_and_default_step(tmp_path):
    log = tmp_path / "run.csv"
    db = tmp_path / "db.sqlite"
    _write_csv(log, 5)
    runner = CliRunner()
    result = runner.invoke(main, [
        "--file", str(log),
        "--run-id", "csv",
        "--db", str(db),
    ])
    assert result.exit_code == 0, result.output
    storage = Storage(db)
    samples = storage.fetch_samples("csv")
    assert len(samples) == 5
    assert samples[0]["output_length"] == len("out0")  # auto-computed


def test_invalid_metadata_errors(tmp_path):
    log = tmp_path / "run.jsonl"
    db = tmp_path / "db.sqlite"
    _write_jsonl(log, 1)
    runner = CliRunner()
    result = runner.invoke(main, [
        "--file", str(log), "--run-id", "x", "--metadata", "not json", "--db", str(db),
    ])
    assert result.exit_code != 0
    assert "invalid --metadata" in result.output


def test_missing_reward_errors(tmp_path):
    log = tmp_path / "run.jsonl"
    db = tmp_path / "db.sqlite"
    log.write_text(json.dumps({"step": 0, "prompt": "p", "output": "o"}) + "\n")
    runner = CliRunner()
    result = runner.invoke(main, [
        "--file", str(log), "--run-id", "x", "--db", str(db),
    ])
    assert result.exit_code != 0
    assert "reward" in result.output


def test_multiple_files(tmp_path):
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    db = tmp_path / "db.sqlite"
    _write_jsonl(a, 10)
    _write_jsonl(b, 5)
    runner = CliRunner()
    result = runner.invoke(main, [
        "--file", str(a), "--file", str(b),
        "--run-id", "multi", "--db", str(db),
    ])
    assert result.exit_code == 0, result.output
    storage = Storage(db)
    assert len(storage.fetch_samples("multi")) == 15
