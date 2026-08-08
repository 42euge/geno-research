"""CLI entry point for the data quality flywheel.

Subcommands:
    analyze_dataset  -- score + detect issues, write report
    export_issues    -- write issues + suggested fixes for human review
    apply_fixes      -- apply a (possibly hand-edited) fixes file, version it
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from ..analysis import score_dataset
from ..curation import apply_fixes as _apply_fixes
from ..curation import load_fixes, suggest_fixes, write_fixes_template
from ..feedback import build_iteration_report
from ..ingestion import load_dataset, normalize, save_dataset
from ..issues import detect_all
from ..versioning import VersionStore


def _write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def _cmd_analyze(args: argparse.Namespace) -> int:
    transcripts = normalize(load_dataset(args.dataset))
    scores = score_dataset(transcripts)
    issues = detect_all(
        transcripts,
        scores,
        duplicate_threshold=args.duplicate_threshold,
        low_quality_threshold=args.low_quality_threshold,
    )
    report = {
        "dataset": str(args.dataset),
        "size": len(transcripts),
        "avg_score": round(sum(s.score for s in scores) / len(scores), 4) if scores else 0.0,
        "score_distribution": _bucketize([s.score for s in scores]),
        "issue_counts": dict(Counter(i.issue_type for i in issues)),
        "issues_per_transcript": round(len(issues) / max(1, len(transcripts)), 3),
    }
    out_dir = Path(args.out)
    _write_json(report, out_dir / "summary.json")
    _write_json([s.to_dict() for s in scores], out_dir / "scores.json")
    _write_json([i.to_dict() for i in issues], out_dir / "issues.json")

    print(f"Analyzed {len(transcripts)} transcripts -> {out_dir}/summary.json")
    print(f"  avg_score = {report['avg_score']}")
    print(f"  issues    = {report['issue_counts']}")
    return 0


def _cmd_export_issues(args: argparse.Namespace) -> int:
    transcripts = normalize(load_dataset(args.dataset))
    scores = score_dataset(transcripts)
    issues = detect_all(transcripts, scores)
    fixes = suggest_fixes(transcripts, issues)

    out_dir = Path(args.out)
    _write_json([i.to_dict() for i in issues], out_dir / "issues.json")
    fixes_path = write_fixes_template(fixes, out_dir / "fixes.jsonl")
    print(f"Wrote {len(issues)} issues -> {out_dir}/issues.json")
    print(f"Wrote {len(fixes)} suggested fixes -> {fixes_path}")
    print("Edit the fixes file (action / new_response) and run `apply_fixes`.")
    return 0


def _cmd_apply_fixes(args: argparse.Namespace) -> int:
    transcripts = normalize(load_dataset(args.dataset))
    fixes = load_fixes(args.fixes)
    cleaned, log = _apply_fixes(transcripts, fixes)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = out_dir / args.cleaned_name
    save_dataset(cleaned, cleaned_path)
    _write_json(log, out_dir / "curation_log.json")

    report = build_iteration_report(
        iteration=args.iteration,
        before=transcripts,
        after=cleaned,
        curation_log=log,
    )
    _write_json(report.to_dict(), out_dir / "iteration_report.json")

    version_id = None
    if args.version_store:
        store = VersionStore(args.version_store)
        version_id = store.commit(
            cleaned,
            message=args.message or f"iteration {args.iteration}",
            meta={"iteration_report": report.to_dict()},
        )

    print(f"Wrote cleaned dataset -> {cleaned_path}")
    print(
        "  before={size_before} after={size_after} "
        "removed={removed} edited={edited} rewritten={rewritten}".format(**report.to_dict())
    )
    print(
        f"  avg_score: {report.avg_score_before} -> {report.avg_score_after}"
    )
    if version_id:
        print(f"Versioned as {version_id} in {args.version_store}")
    return 0


def _bucketize(values: list[float], n: int = 10) -> dict[str, int]:
    buckets: dict[str, int] = {}
    for v in values:
        idx = min(n - 1, max(0, int(v * n)))
        lo = idx / n
        hi = (idx + 1) / n
        key = f"{lo:.1f}-{hi:.1f}"
        buckets[key] = buckets.get(key, 0) + 1
    return dict(sorted(buckets.items()))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dqf",
        description="Data quality flywheel for training transcripts.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_an = sub.add_parser("analyze_dataset", help="Score + detect issues")
    p_an.add_argument("dataset", help="Path to dataset (.json/.jsonl/.csv)")
    p_an.add_argument("--out", default="reports", help="Output directory")
    p_an.add_argument("--duplicate-threshold", type=float, default=0.85)
    p_an.add_argument("--low-quality-threshold", type=float, default=0.5)
    p_an.set_defaults(func=_cmd_analyze)

    p_ex = sub.add_parser(
        "export_issues",
        help="Write issues + suggested fixes for human review",
    )
    p_ex.add_argument("dataset")
    p_ex.add_argument("--out", default="reports")
    p_ex.set_defaults(func=_cmd_export_issues)

    p_ap = sub.add_parser(
        "apply_fixes",
        help="Apply a fixes JSONL to produce a cleaned dataset",
    )
    p_ap.add_argument("dataset")
    p_ap.add_argument("fixes", help="Path to fixes.jsonl")
    p_ap.add_argument("--out", default="reports")
    p_ap.add_argument("--cleaned-name", default="cleaned.jsonl")
    p_ap.add_argument("--iteration", type=int, default=1)
    p_ap.add_argument(
        "--version-store",
        default=None,
        help="Optional path to a version store directory",
    )
    p_ap.add_argument("--message", default=None, help="Version commit message")
    p_ap.set_defaults(func=_cmd_apply_fixes)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
