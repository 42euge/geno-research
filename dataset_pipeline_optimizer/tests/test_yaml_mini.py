import unittest

from dataset_pipeline_optimizer.pipeline.yaml_mini import parse_yaml


class YamlMiniTests(unittest.TestCase):
    def test_block_mapping_and_sequence(self):
        text = """
name: example
nodes:
  - id: a
    transform: load_jsonl
    params:
      path: foo.jsonl
  - id: b
    transform: filter_records
    deps: [a]
    params:
      where: "len(record.get('x','')) > 0"
""".strip()
        data = parse_yaml(text)
        self.assertEqual(data["name"], "example")
        self.assertEqual(len(data["nodes"]), 2)
        self.assertEqual(data["nodes"][0]["id"], "a")
        self.assertEqual(data["nodes"][1]["deps"], ["a"])
        self.assertEqual(
            data["nodes"][1]["params"]["where"],
            "len(record.get('x','')) > 0",
        )

    def test_flow_collections(self):
        data = parse_yaml("k: [1, 2, 3.5, true, null, 'hi']")
        self.assertEqual(data, {"k": [1, 2, 3.5, True, None, "hi"]})

    def test_inline_mapping(self):
        data = parse_yaml("k: {a: 1, b: 'two'}")
        self.assertEqual(data, {"k": {"a": 1, "b": "two"}})

    def test_comments_stripped(self):
        data = parse_yaml(
            """
# header
key: 1   # inline
other: "url#fragment"   # url-like
""".strip()
        )
        self.assertEqual(data, {"key": 1, "other": "url#fragment"})


if __name__ == "__main__":
    unittest.main()
