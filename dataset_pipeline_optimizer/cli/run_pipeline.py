"""``python -m dataset_pipeline_optimizer`` entry point."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from ..execution.runner import RunOptions, run_pipeline
from ..pipeline.loader import load_pipeline
from .visualize import render_ascii, render_dot


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_pipeline",
        description="Run a YAML-defined dataset pipeline.",
    )
    parser.add_argument("config", help="path to pipeline YAML")
    parser.add_argument(
        "--cache-dir",
        default=".pipeline_cache",
        help="directory for cached intermediates (default: .pipeline_cache)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="dump every stage's output to <cache-dir>/debug",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="ignore cached results and recompute everything",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="parallel workers (default: cpu count)",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="only run the given node ids (and their dependencies)",
    )
    parser.add_argument(
        "--visualize",
        choices=["ascii", "dot"],
        help="print DAG visualization and exit",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="suppress per-node logs"
    )
    return parser


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        pipeline = load_pipeline(args.config)
    except Exception as e:
        print(f"ERROR loading {args.config}: {e}", file=sys.stderr)
        return 2

    if args.visualize:
        if args.visualize == "dot":
            print(render_dot(pipeline))
        else:
            print(render_ascii(pipeline))
        return 0

    cache_dir = Path(args.cache_dir)
    debug_dir = cache_dir / "debug" if args.debug else None

    started = time.perf_counter()
    options = RunOptions(
        cache_dir=cache_dir,
        debug_dir=debug_dir,
        use_cache=not args.no_cache,
        workers=args.workers or RunOptions().workers,
        only=args.only,
        on_event=None if args.quiet else _print_event,
    )
    if not args.quiet:
        print(f"pipeline: {pipeline.name}  ({len(pipeline.nodes)} nodes)")
    try:
        result = run_pipeline(pipeline, options)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not args.quiet:
        elapsed = time.perf_counter() - started
        cached = sum(1 for n in result.nodes if n.cached)
        print(
            f"done in {elapsed:.2f}s — {cached}/{len(result.nodes)} nodes from cache"
        )
    return 0


def _print_event(event: str, payload: dict) -> None:
    if event == "node_started":
        print(f"  > {payload['node']} ({payload['transform']})")
    elif event == "node_finished":
        tag = "cache" if payload["cached"] else f"{payload['duration_s']*1000:.1f}ms"
        print(f"    {payload['node']} [{tag}]")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
