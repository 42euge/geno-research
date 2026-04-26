from reward_monitoring_dashboard.storage.db import Sample


def test_run_roundtrip(storage):
    storage.upsert_run("r1", "Run", "2026-04-26T00:00:00Z", {"k": "v"})
    runs = storage.list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == "r1"
    assert runs[0].metadata == {"k": "v"}

    fetched = storage.get_run("r1")
    assert fetched is not None
    assert fetched.name == "Run"


def test_upsert_updates_metadata(storage):
    storage.upsert_run("r1", "Run", "2026-04-26T00:00:00Z", {"k": "v1"})
    storage.upsert_run("r1", "Run renamed", "2026-04-26T00:00:00Z", {"k": "v2"})
    run = storage.get_run("r1")
    assert run.name == "Run renamed"
    assert run.metadata == {"k": "v2"}


def test_insert_and_fetch_samples(storage):
    storage.upsert_run("r1", "Run", "2026-04-26T00:00:00Z", {})
    n = storage.insert_samples(
        [
            Sample("r1", 0, "2026-04-26T00:00:00Z", "p", "o", 0.5, "qa", 100),
            Sample("r1", 1, "2026-04-26T00:00:01Z", "p", "o", 0.6, "qa", 110),
        ]
    )
    assert n == 2
    rows = storage.fetch_samples("r1")
    assert len(rows) == 2
    assert rows[0]["step"] == 0
    assert rows[1]["reward"] == 0.6


def test_pagination(populated_storage):
    items, total = populated_storage.page_samples("r1", offset=0, limit=10)
    assert total == 120
    assert len(items) == 10
    assert items[0]["step"] == 0

    items_desc, _ = populated_storage.page_samples("r1", limit=5, descending=True)
    assert items_desc[0]["step"] == 119


def test_delete_run_cascades(populated_storage):
    assert populated_storage.delete_run("r1") is True
    assert populated_storage.get_run("r1") is None
    assert populated_storage.fetch_samples("r1") == []


def test_get_sample(populated_storage):
    items, _ = populated_storage.page_samples("r1", limit=1)
    sample_id = items[0]["id"]
    s = populated_storage.get_sample(sample_id)
    assert s["step"] == 0
    assert s["run_id"] == "r1"
