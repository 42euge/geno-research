import unittest

from dataset_pipeline_optimizer.pipeline.dag import Node, Pipeline, PipelineError


def _p(*nodes):
    return Pipeline(name="t", nodes=list(nodes))


class DagTests(unittest.TestCase):
    def test_topological_order(self):
        pipe = _p(
            Node(id="c", transform="x", deps=["b"]),
            Node(id="a", transform="x"),
            Node(id="b", transform="x", deps=["a"]),
        )
        order = [n.id for n in pipe.topological_order()]
        self.assertEqual(order, ["a", "b", "c"])

    def test_cycle_detected(self):
        with self.assertRaises(PipelineError):
            _p(
                Node(id="a", transform="x", deps=["b"]),
                Node(id="b", transform="x", deps=["a"]),
            )

    def test_unknown_dep(self):
        with self.assertRaises(PipelineError):
            _p(Node(id="a", transform="x", deps=["nope"]))

    def test_duplicate_id(self):
        with self.assertRaises(PipelineError):
            _p(Node(id="a", transform="x"), Node(id="a", transform="y"))

    def test_subgraph(self):
        pipe = _p(
            Node(id="a", transform="x"),
            Node(id="b", transform="x", deps=["a"]),
            Node(id="c", transform="x", deps=["a"]),
            Node(id="d", transform="x", deps=["b", "c"]),
        )
        sub = pipe.subgraph(["b"])
        self.assertEqual(sorted(n.id for n in sub.nodes), ["a", "b"])

    def test_leaf_nodes(self):
        pipe = _p(
            Node(id="a", transform="x"),
            Node(id="b", transform="x", deps=["a"]),
            Node(id="c", transform="x", deps=["a"]),
        )
        self.assertEqual(sorted(n.id for n in pipe.leaf_nodes()), ["b", "c"])


if __name__ == "__main__":
    unittest.main()
