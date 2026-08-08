"""End-to-end + unit tests for the data quality flywheel.

Run with:
    python -m unittest discover -s data_quality_flywheel/tests
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from data_quality_flywheel.analysis import score_dataset, score_transcript
from data_quality_flywheel.curation import (
    apply_fixes,
    load_fixes,
    suggest_fixes,
    write_fixes_template,
)
from data_quality_flywheel.feedback import build_iteration_report, reinsert
from data_quality_flywheel.ingestion import load_dataset, normalize, save_dataset
from data_quality_flywheel.issues import (
    detect_all,
    detect_ambiguity,
    detect_duplicates,
    detect_low_quality,
    detect_redundancy,
)
from data_quality_flywheel.types import Fix, Transcript
from data_quality_flywheel.versioning import VersionStore


SAMPLE = Path(__file__).resolve().parent.parent / "data" / "sample_transcripts.jsonl"


class IngestionTests(unittest.TestCase):
    def test_load_jsonl(self) -> None:
        ts = load_dataset(SAMPLE)
        self.assertEqual(len(ts), 12)
        self.assertEqual(ts[0].prompt, "What is the capital of France?")

    def test_normalize_drops_empty(self) -> None:
        ts = [
            Transcript(id="a", prompt="  ", response=""),
            Transcript(id="b", prompt="hi   there", response="ok\n\nthen"),
        ]
        out = normalize(ts)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].prompt, "hi there")
        self.assertEqual(out[0].response, "ok then")

    def test_normalize_dedupes_ids(self) -> None:
        ts = [
            Transcript(id="x", prompt="p1", response="r1"),
            Transcript(id="x", prompt="p2", response="r2"),
        ]
        out = normalize(ts)
        self.assertEqual([t.id for t in out], ["x", "x#1"])

    def test_save_roundtrip_jsonl(self) -> None:
        ts = load_dataset(SAMPLE)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "out.jsonl"
            save_dataset(ts, p)
            again = load_dataset(p)
            self.assertEqual(len(ts), len(again))
            self.assertEqual(ts[3].response, again[3].response)


class ScoringTests(unittest.TestCase):
    def test_high_quality_scores_higher_than_low(self) -> None:
        good = Transcript(
            id="g",
            prompt="Explain photosynthesis briefly.",
            response="Photosynthesis is the process by which plants convert sunlight, water, and carbon dioxide into glucose and oxygen.",
        )
        bad = Transcript(id="b", prompt="What's 2+2?", response="I don't know.")
        self.assertGreater(score_transcript(good).score, score_transcript(bad).score)

    def test_model_scorer_integrates(self) -> None:
        t = Transcript(id="m", prompt="hi", response="hello there")
        s_default = score_transcript(t)
        s_with_judge = score_transcript(t, model_scorer=lambda p, r: 1.0)
        self.assertIn("model", s_with_judge.components)
        self.assertGreaterEqual(s_with_judge.score, s_default.score - 1e-9)

    def test_scores_in_unit_interval(self) -> None:
        ts = load_dataset(SAMPLE)
        for s in score_dataset(ts):
            self.assertGreaterEqual(s.score, 0.0)
            self.assertLessEqual(s.score, 1.0)


class IssueTests(unittest.TestCase):
    def test_redundant_prompts_flagged(self) -> None:
        ts = normalize(load_dataset(SAMPLE))
        red = detect_redundancy(ts)
        self.assertTrue(any(i.transcript_id == "t002" for i in red))
        self.assertTrue(any(i.transcript_id == "t011" for i in red))

    def test_duplicates_flagged(self) -> None:
        ts = normalize(load_dataset(SAMPLE))
        dups = detect_duplicates(ts, threshold=0.6)
        self.assertTrue(dups, "expected near-duplicates in sample")

    def test_ambiguity_flags_short_open_question(self) -> None:
        ts = normalize(load_dataset(SAMPLE))
        amb = detect_ambiguity(ts)
        self.assertTrue(any(i.transcript_id == "t005" for i in amb))
        self.assertTrue(any(i.transcript_id == "t010" for i in amb))

    def test_low_quality_uses_threshold(self) -> None:
        ts = normalize(load_dataset(SAMPLE))
        scores = score_dataset(ts)
        low = detect_low_quality(ts, scores, threshold=0.6)
        flagged_ids = {i.transcript_id for i in low}
        self.assertIn("t004", flagged_ids)  # "I don't know"
        self.assertIn("t009", flagged_ids)  # token repetition

    def test_detect_all_returns_multiple_types(self) -> None:
        ts = normalize(load_dataset(SAMPLE))
        scores = score_dataset(ts)
        issues = detect_all(ts, scores)
        types = {i.issue_type for i in issues}
        self.assertGreaterEqual(len(types), 3)


class CurationTests(unittest.TestCase):
    def test_suggest_and_apply_remove(self) -> None:
        ts = [
            Transcript(id="a", prompt="hello world", response="hi"),
            Transcript(id="b", prompt="hello world", response="hi"),
        ]
        ts = normalize(ts)
        scores = score_dataset(ts)
        issues = detect_all(ts, scores)
        fixes = suggest_fixes(ts, issues)
        cleaned, log = apply_fixes(ts, fixes)
        self.assertLessEqual(len(cleaned), len(ts))
        self.assertTrue(log)

    def test_apply_explicit_edit(self) -> None:
        ts = [Transcript(id="x", prompt="p", response="r")]
        fixes = [Fix(transcript_id="x", action="edit", new_response="better", reason="fix")]
        cleaned, log = apply_fixes(ts, fixes)
        self.assertEqual(cleaned[0].response, "better")
        self.assertEqual(log[0]["action"], "edit")

    def test_rewrite_without_text_drops(self) -> None:
        ts = [Transcript(id="x", prompt="p", response="r")]
        fixes = [Fix(transcript_id="x", action="rewrite_response", reason="missing")]
        cleaned, log = apply_fixes(ts, fixes)
        self.assertEqual(cleaned, [])
        self.assertEqual(log[0]["action"], "drop_pending_rewrite")

    def test_template_roundtrip(self) -> None:
        fixes = [Fix(transcript_id="a", action="keep", reason="ok")]
        with tempfile.TemporaryDirectory() as d:
            p = write_fixes_template(fixes, Path(d) / "fixes.jsonl")
            again = load_fixes(p)
            self.assertEqual(again[0].transcript_id, "a")


class FeedbackTests(unittest.TestCase):
    def test_reinsert_replaces_by_id(self) -> None:
        base = [Transcript(id="a", prompt="p", response="r")]
        improved = [Transcript(id="a", prompt="p", response="better")]
        merged = reinsert(base, improved)
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].response, "better")

    def test_iteration_report_tracks_improvement(self) -> None:
        before = normalize(load_dataset(SAMPLE))
        # remove the worst offenders (t004 "I don't know", t009 repetition)
        keep_ids = {t.id for t in before} - {"t004", "t009"}
        after = [t for t in before if t.id in keep_ids]
        log = [
            {"id": "t004", "action": "remove", "reason": "low signal"},
            {"id": "t009", "action": "remove", "reason": "repetition"},
        ]
        report = build_iteration_report(1, before, after, log)
        self.assertEqual(report.removed, 2)
        self.assertEqual(report.size_after, len(after))
        self.assertGreaterEqual(report.avg_score_after, report.avg_score_before)


class VersionStoreTests(unittest.TestCase):
    def test_commit_and_reload(self) -> None:
        ts = [Transcript(id="a", prompt="p", response="r")]
        with tempfile.TemporaryDirectory() as d:
            store = VersionStore(d)
            v1 = store.commit(ts, "initial")
            v2 = store.commit(ts + [Transcript(id="b", prompt="p2", response="r2")], "added b")
            self.assertNotEqual(v1, v2)
            history = store.history()
            self.assertEqual([h["version_id"] for h in history], [v1, v2])
            self.assertEqual(len(store.load(v1)), 1)
            self.assertEqual(len(store.load(v2)), 2)


class CliTests(unittest.TestCase):
    def test_analyze_writes_outputs(self) -> None:
        from data_quality_flywheel.cli import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            rc = cli_main(["analyze_dataset", str(SAMPLE), "--out", d])
            self.assertEqual(rc, 0)
            for name in ("summary.json", "scores.json", "issues.json"):
                self.assertTrue((Path(d) / name).exists(), name)

    def test_export_then_apply(self) -> None:
        from data_quality_flywheel.cli import main as cli_main

        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(
                cli_main(["export_issues", str(SAMPLE), "--out", d]), 0
            )
            fixes_path = Path(d) / "fixes.jsonl"
            self.assertTrue(fixes_path.exists())
            store_dir = Path(d) / "vs"
            rc = cli_main(
                [
                    "apply_fixes",
                    str(SAMPLE),
                    str(fixes_path),
                    "--out",
                    d,
                    "--version-store",
                    str(store_dir),
                    "--message",
                    "test",
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue((Path(d) / "cleaned.jsonl").exists())
            self.assertTrue((Path(d) / "iteration_report.json").exists())
            history = json.loads((store_dir / "log.jsonl").read_text().splitlines()[0])
            self.assertEqual(history["message"], "test")


if __name__ == "__main__":
    unittest.main()
