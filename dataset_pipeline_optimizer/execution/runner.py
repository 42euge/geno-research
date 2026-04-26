"""Pipeline runner: parallel scheduler with caching and debug dumps."""

from __future__ import annotations

import json
import os
import pickle
import threading
import time
import traceback
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..pipeline.dag import Node, Pipeline
from ..transforms.registry import REGISTRY
from .cache import Cache


@dataclass
class RunOptions:
    cache_dir: Path = Path(".pipeline_cache")
    debug_dir: Optional[Path] = None
    use_cache: bool = True
    workers: int = max(1, os.cpu_count() or 1)
    only: Optional[List[str]] = None
    on_event: Optional[Callable[[str, Dict[str, Any]], None]] = None


@dataclass
class NodeResult:
    node_id: str
    transform: str
    cache_key: str
    cached: bool
    duration_s: float
    output_summary: Dict[str, Any]


@dataclass
class RunResult:
    pipeline: str
    nodes: List[NodeResult] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    total_duration_s: float = 0.0


def _summarize(value: Any) -> Dict[str, Any]:
    if isinstance(value, list):
        sample = value[0] if value else None
        return {"type": "list", "length": len(value), "sample_keys": list(sample.keys()) if isinstance(sample, dict) else None}
    if isinstance(value, dict):
        return {"type": "dict", "keys": sorted(value.keys())}
    if isinstance(value, str):
        return {"type": "str", "length": len(value)}
    return {"type": type(value).__name__}


def _emit(opts: RunOptions, event: str, payload: Dict[str, Any]) -> None:
    if opts.on_event:
        opts.on_event(event, payload)


def run_pipeline(pipeline: Pipeline, options: Optional[RunOptions] = None) -> RunResult:
    opts = options or RunOptions()
    if opts.only:
        pipeline = pipeline.subgraph(opts.only)
    cache = Cache(opts.cache_dir)
    if opts.debug_dir is not None:
        opts.debug_dir.mkdir(parents=True, exist_ok=True)

    by_id = {n.id: n for n in pipeline.nodes}
    order = pipeline.topological_order()
    pending: Dict[str, Node] = {n.id: n for n in order}
    keys: Dict[str, str] = {}
    values: Dict[str, Any] = {}
    results: Dict[str, NodeResult] = {}
    in_flight: Dict[str, Future] = {}
    lock = threading.Lock()
    errors: List[Exception] = []

    started = time.perf_counter()

    def execute(node: Node) -> NodeResult:
        transform = REGISTRY.get(node.transform)
        if transform is None:
            raise KeyError(
                f"unknown transform {node.transform!r}; "
                f"registered: {sorted(REGISTRY)}"
            )
        upstream_keys = [keys[d] for d in node.deps]
        cache_key = Cache.compute_key(
            transform.name, transform.version, dict(node.params), upstream_keys
        )

        cached = False
        value: Any
        if opts.use_cache:
            value = cache.get(cache_key)
            if value is not None:
                cached = True
        if not cached:
            inputs = [values[d] for d in node.deps]
            t0 = time.perf_counter()
            try:
                value = transform.run(inputs, dict(node.params))
            except Exception as e:
                raise RuntimeError(
                    f"node {node.id!r} (transform {node.transform!r}) failed: {e}"
                ) from e
            duration = time.perf_counter() - t0
            cache.put(cache_key, value)
        else:
            duration = 0.0

        if opts.debug_dir is not None:
            _dump_debug(opts.debug_dir, node, cache_key, value)

        result = NodeResult(
            node_id=node.id,
            transform=node.transform,
            cache_key=cache_key,
            cached=cached,
            duration_s=duration,
            output_summary=_summarize(value),
        )
        with lock:
            keys[node.id] = cache_key
            values[node.id] = value
            results[node.id] = result
        _emit(opts, "node_finished", {"node": node.id, "cached": cached, "duration_s": duration})
        return result

    def ready_nodes() -> List[Node]:
        ready = []
        for node_id, node in list(pending.items()):
            if node_id in in_flight:
                continue
            if all(d in values for d in node.deps):
                ready.append(node)
        return ready

    with ThreadPoolExecutor(max_workers=opts.workers) as pool:
        while pending:
            for node in ready_nodes():
                _emit(opts, "node_started", {"node": node.id, "transform": node.transform})
                in_flight[node.id] = pool.submit(execute, node)
            if not in_flight:
                # Nothing scheduled — must be a dep error
                raise RuntimeError(
                    f"deadlock: cannot make progress on {sorted(pending)}"
                )
            done_ids: List[str] = []
            for node_id, fut in list(in_flight.items()):
                if fut.done():
                    done_ids.append(node_id)
            if not done_ids:
                # Wait for at least one to finish
                next(iter(in_flight.values())).result()
                continue
            for node_id in done_ids:
                fut = in_flight.pop(node_id)
                try:
                    fut.result()
                except Exception as e:
                    errors.append(e)
                pending.pop(node_id, None)
            if errors:
                raise errors[0]

    total = time.perf_counter() - started
    leaf_outputs = {n.id: values[n.id] for n in pipeline.leaf_nodes()}
    return RunResult(
        pipeline=pipeline.name,
        nodes=[results[n.id] for n in order if n.id in results],
        outputs=leaf_outputs,
        total_duration_s=total,
    )


def _dump_debug(debug_dir: Path, node: Node, cache_key: str, value: Any) -> None:
    node_dir = debug_dir / node.id
    node_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "id": node.id,
        "transform": node.transform,
        "params": node.params,
        "deps": node.deps,
        "cache_key": cache_key,
    }
    with open(node_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, sort_keys=True, default=str)
    try:
        if isinstance(value, list):
            preview = value[:20]
        else:
            preview = value
        with open(node_dir / "output.json", "w", encoding="utf-8") as f:
            json.dump(preview, f, indent=2, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        with open(node_dir / "output.pkl", "wb") as f:
            pickle.dump(value, f)
