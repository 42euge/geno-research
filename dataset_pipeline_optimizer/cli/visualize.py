"""DAG visualization helpers (ASCII + Graphviz DOT)."""

from __future__ import annotations

from typing import List

from ..pipeline.dag import Pipeline


def render_dot(pipeline: Pipeline) -> str:
    lines: List[str] = [f'digraph "{pipeline.name}" {{', "  rankdir=LR;"]
    for node in pipeline.nodes:
        label = f"{node.id}\\n[{node.transform}]"
        lines.append(f'  "{node.id}" [label="{label}", shape=box];')
    for node in pipeline.nodes:
        for dep in node.deps:
            lines.append(f'  "{dep}" -> "{node.id}";')
    lines.append("}")
    return "\n".join(lines)


def render_ascii(pipeline: Pipeline) -> str:
    """Render the DAG as a simple layered ASCII diagram."""
    by_id = {n.id: n for n in pipeline.nodes}
    layer_of: dict = {}
    for node in pipeline.topological_order():
        layer_of[node.id] = (
            0 if not node.deps else 1 + max(layer_of[d] for d in node.deps)
        )
    layers: List[List[str]] = []
    for node_id, layer in layer_of.items():
        while len(layers) <= layer:
            layers.append([])
        layers[layer].append(node_id)

    out: List[str] = [f"pipeline: {pipeline.name}"]
    for i, layer in enumerate(layers):
        out.append(f"  layer {i}:")
        for node_id in layer:
            node = by_id[node_id]
            deps = ", ".join(node.deps) if node.deps else "(source)"
            out.append(f"    - {node_id}  [{node.transform}]   <- {deps}")
    return "\n".join(out)
