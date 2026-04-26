import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from dataset_pipeline_optimizer.cli.run_pipeline import main


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cwd = os.getcwd()
        # Stage examples dir into a clean workspace so 'out/' lands in tmp
        shutil.copytree(PROJECT_ROOT / "examples", Path(self.tmp.name) / "examples")
        os.chdir(self.tmp.name)
        self.addCleanup(lambda: os.chdir(self.cwd))

    def test_training_ready_pipeline(self):
        rc = main(["examples/configs/training_ready.yaml", "--quiet"])
        self.assertEqual(rc, 0)
        out = Path("out/training.jsonl")
        self.assertTrue(out.exists(), f"missing {out}")
        records = [json.loads(line) for line in out.read_text().splitlines()]
        self.assertGreater(len(records), 0)
        for r in records:
            self.assertIn("messages", r)
            roles = [m["role"] for m in r["messages"]]
            self.assertEqual(roles[0], "system")
            self.assertEqual(roles[-1], "user")

    def test_multi_source_pipeline(self):
        rc = main(["examples/configs/multi_source.yaml", "--quiet"])
        self.assertEqual(rc, 0)
        out = Path("out/merged.jsonl")
        self.assertTrue(out.exists())
        records = [json.loads(line) for line in out.read_text().splitlines()]
        # 12 jsonl rows + 3 csv rows, after filter+dedup should still be plural
        self.assertGreaterEqual(len(records), 5)
        for r in records:
            self.assertIn("prompt", r)

    def test_visualize_ascii_does_not_run(self):
        rc = main(["examples/configs/training_ready.yaml", "--visualize", "ascii"])
        self.assertEqual(rc, 0)
        # When --visualize is used, no outputs should be produced
        self.assertFalse(Path("out").exists())

    def test_only_subset(self):
        rc = main(
            [
                "examples/configs/training_ready.yaml",
                "--only",
                "dedup",
                "--quiet",
            ]
        )
        self.assertEqual(rc, 0)
        # 'write' is downstream of 'dedup' and should NOT have been run
        self.assertFalse(Path("out/training.jsonl").exists())

    def test_incremental_rerun_uses_cache(self):
        main(["examples/configs/training_ready.yaml", "--quiet"])
        # Capture mtime, run again, ensure cache hits short-circuit
        cache_dir = Path(".pipeline_cache")
        before = sorted(p.stat().st_mtime_ns for p in cache_dir.glob("*.pkl"))
        main(["examples/configs/training_ready.yaml", "--quiet"])
        after = sorted(p.stat().st_mtime_ns for p in cache_dir.glob("*.pkl"))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
