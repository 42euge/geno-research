import json
import os
import tempfile
import unittest

from dataset_pipeline_optimizer.transforms.registry import REGISTRY


def _run(name, *inputs, **params):
    return REGISTRY[name].run(list(inputs), params)


class FilteringTests(unittest.TestCase):
    def test_filter_records_safe_eval(self):
        recs = [{"text": "x"}, {"text": "longer text"}, {"text": ""}]
        out = _run("filter_records", recs, where="len(record['text']) > 1")
        self.assertEqual(out, [{"text": "longer text"}])

    def test_filter_records_blocks_builtins(self):
        with self.assertRaises(NameError):
            _run("filter_records", [{"x": 1}], where="__import__('os').name")

    def test_min_length(self):
        recs = [{"t": "hi"}, {"t": "hello"}]
        out = _run("filter_min_length", recs, field="t", min_length=3)
        self.assertEqual(out, [{"t": "hello"}])

    def test_drop_and_keep_fields(self):
        recs = [{"a": 1, "b": 2, "c": 3}]
        self.assertEqual(_run("drop_fields", recs, fields=["b"]), [{"a": 1, "c": 3}])
        self.assertEqual(_run("keep_fields", recs, fields=["a", "c"]), [{"a": 1, "c": 3}])


class DedupTests(unittest.TestCase):
    def test_exact_dedup_first(self):
        recs = [{"k": 1, "v": "a"}, {"k": 1, "v": "b"}, {"k": 2, "v": "c"}]
        out = _run("deduplicate", recs, key="k")
        self.assertEqual(out, [{"k": 1, "v": "a"}, {"k": 2, "v": "c"}])

    def test_normalized_dedup(self):
        recs = [{"t": "Hello, world!"}, {"t": "hello world"}, {"t": "different"}]
        out = _run("deduplicate_normalized", recs, field="t")
        self.assertEqual(len(out), 2)


class FormattingTests(unittest.TestCase):
    def test_format_chat(self):
        recs = [{"q": "hi"}]
        out = _run("format_chat", recs, prompt_field="q", system="sys")
        self.assertEqual(
            out,
            [{"messages": [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]}],
        )

    def test_format_template(self):
        recs = [{"name": "Ada", "topic": "math"}]
        out = _run("format_template", recs, template="{name} likes {topic}", output_field="text")
        self.assertEqual(out[0]["text"], "Ada likes math")

    def test_concat_fan_in(self):
        out = _run("concat", [{"a": 1}], [{"a": 2}, {"a": 3}])
        self.assertEqual(out, [{"a": 1}, {"a": 2}, {"a": 3}])


class IOTests(unittest.TestCase):
    def test_jsonl_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.jsonl")
            with open(inp, "w") as f:
                f.write('{"a": 1}\n{"a": 2}\n')
            recs = _run("load_jsonl", path=inp)
            out_path = os.path.join(tmp, "sub", "out.jsonl")
            res = _run("write_jsonl", recs, path=out_path)
            self.assertEqual(res, {"path": out_path, "count": 2})
            roundtripped = [json.loads(l) for l in open(out_path)]
            self.assertEqual(roundtripped, [{"a": 1}, {"a": 2}])


class ValidationTransformTests(unittest.TestCase):
    def test_schema_required_and_types(self):
        recs = [{"id": 1, "name": "x"}]
        out = _run("validate_schema", recs, required=["id"], types={"id": "int", "name": "str"})
        self.assertEqual(out, recs)

    def test_schema_failure(self):
        from dataset_pipeline_optimizer.validation.errors import ValidationError
        with self.assertRaises(ValidationError):
            _run("validate_schema", [{"id": "oops"}], types={"id": "int"})

    def test_assert_min_count(self):
        from dataset_pipeline_optimizer.validation.errors import ValidationError
        _run("assert_min_count", [{"a": 1}], min_count=1)
        with self.assertRaises(ValidationError):
            _run("assert_min_count", [], min_count=1)


if __name__ == "__main__":
    unittest.main()
