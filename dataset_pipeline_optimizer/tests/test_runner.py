import json
import os
import tempfile
import unittest
from pathlib import Path

from dataset_pipeline_optimizer.execution.runner import RunOptions, run_pipeline
from dataset_pipeline_optimizer.pipeline.dag import Node, Pipeline
from dataset_pipeline_optimizer.transforms.registry import REGISTRY, register


# Helper transforms registered just for these tests.
_call_log: list = []


def _ensure_test_transforms():
    if "test_const" in REGISTRY:
        return

    @register("test_const")
    def _const(_inputs, value):
        _call_log.append(("const", value))
        return value

    @register("test_add")
    def _add(inputs, addend=0):
        _call_log.append(("add",))
        return [v + addend for v in inputs[0]]

    @register("test_sum")
    def _sum(inputs):
        _call_log.append(("sum",))
        return sum(sum(branch) for branch in inputs)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        _ensure_test_transforms()
        _call_log.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache_dir = Path(self.tmp.name) / "cache"

    def _run(self, pipeline, **kwargs):
        opts = RunOptions(cache_dir=self.cache_dir, **kwargs)
        return run_pipeline(pipeline, opts)

    def test_basic_chain(self):
        pipe = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1, 2, 3]}),
                Node(id="b", transform="test_add", deps=["a"], params={"addend": 10}),
            ],
        )
        result = self._run(pipe)
        self.assertEqual(result.outputs["b"], [11, 12, 13])

    def test_caching_skips_recompute(self):
        pipe = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1, 2]}),
                Node(id="b", transform="test_add", deps=["a"], params={"addend": 5}),
            ],
        )
        self._run(pipe)
        first_calls = list(_call_log)
        _call_log.clear()
        result2 = self._run(pipe)
        self.assertEqual(_call_log, [], "no transforms should re-execute on second run")
        self.assertEqual(result2.outputs["b"], [6, 7])
        self.assertTrue(all(n.cached for n in result2.nodes))
        # First run should have invoked both
        self.assertEqual(len(first_calls), 2)

    def test_param_change_invalidates_downstream_only(self):
        pipe = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1, 2]}),
                Node(id="b", transform="test_add", deps=["a"], params={"addend": 5}),
            ],
        )
        self._run(pipe)
        _call_log.clear()
        # Change only b's params
        pipe2 = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1, 2]}),
                Node(id="b", transform="test_add", deps=["a"], params={"addend": 7}),
            ],
        )
        result = self._run(pipe2)
        # 'a' should be cached, 'b' should re-run
        a_res = next(n for n in result.nodes if n.node_id == "a")
        b_res = next(n for n in result.nodes if n.node_id == "b")
        self.assertTrue(a_res.cached)
        self.assertFalse(b_res.cached)
        self.assertEqual(_call_log, [("add",)])
        self.assertEqual(result.outputs["b"], [8, 9])

    def test_fan_in_parallel(self):
        pipe = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1, 2]}),
                Node(id="b", transform="test_const", params={"value": [10, 20]}),
                Node(id="c", transform="test_sum", deps=["a", "b"]),
            ],
        )
        result = self._run(pipe, workers=2)
        self.assertEqual(result.outputs["c"], 33)

    def test_only_runs_subset(self):
        pipe = Pipeline(
            name="t",
            nodes=[
                Node(id="a", transform="test_const", params={"value": [1]}),
                Node(id="b", transform="test_add", deps=["a"], params={"addend": 1}),
                Node(id="c", transform="test_add", deps=["b"], params={"addend": 1}),
            ],
        )
        result = self._run(pipe, only=["b"])
        self.assertIn("b", result.outputs)
        self.assertNotIn("c", result.outputs)

    def test_debug_dump(self):
        pipe = Pipeline(
            name="t",
            nodes=[Node(id="a", transform="test_const", params={"value": [1, 2]})],
        )
        debug = self.cache_dir / "debug"
        self._run(pipe, debug_dir=debug)
        meta = json.loads((debug / "a" / "meta.json").read_text())
        self.assertEqual(meta["transform"], "test_const")
        out = json.loads((debug / "a" / "output.json").read_text())
        self.assertEqual(out, [1, 2])

    def test_no_cache_forces_recompute(self):
        pipe = Pipeline(
            name="t",
            nodes=[Node(id="a", transform="test_const", params={"value": [1]})],
        )
        self._run(pipe)
        _call_log.clear()
        self._run(pipe, use_cache=False)
        self.assertEqual(len(_call_log), 1)


if __name__ == "__main__":
    unittest.main()
