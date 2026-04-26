"""Load Pipeline objects from YAML.

Uses a tiny built-in YAML subset parser so the package has no third-party
dependencies. The subset covers the constructs used by the example configs:
mappings, sequences (block and flow), strings, numbers, booleans, null.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from .dag import Node, Pipeline, PipelineError
from .yaml_mini import parse_yaml


def load_pipeline(source: Union[str, Path]) -> Pipeline:
    path = Path(source)
    text = path.read_text(encoding="utf-8")
    data = parse_yaml(text)
    if not isinstance(data, dict):
        raise PipelineError(f"{path}: top-level YAML must be a mapping")
    if "nodes" not in data:
        raise PipelineError(f"{path}: missing 'nodes' key")
    name = str(data.get("name", path.stem))
    raw_nodes = data["nodes"]
    if not isinstance(raw_nodes, list):
        raise PipelineError(f"{path}: 'nodes' must be a list")
    nodes: List[Node] = []
    for i, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            raise PipelineError(f"{path}: node #{i} must be a mapping")
        if "id" not in raw or "transform" not in raw:
            raise PipelineError(
                f"{path}: node #{i} requires 'id' and 'transform'"
            )
        deps = raw.get("deps", []) or []
        if isinstance(deps, str):
            deps = [deps]
        params = raw.get("params", {}) or {}
        if not isinstance(params, dict):
            raise PipelineError(
                f"{path}: node {raw['id']!r} params must be a mapping"
            )
        nodes.append(
            Node(
                id=str(raw["id"]),
                transform=str(raw["transform"]),
                params=params,
                deps=[str(d) for d in deps],
            )
        )
    return Pipeline(name=name, nodes=nodes)
