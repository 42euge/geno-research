"""Pipeline DAG: nodes, edges, validation, topological order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Set


class PipelineError(Exception):
    """Raised for malformed pipelines (missing deps, cycles, duplicates)."""


@dataclass
class Node:
    id: str
    transform: str
    params: Dict[str, object] = field(default_factory=dict)
    deps: List[str] = field(default_factory=list)


@dataclass
class Pipeline:
    name: str
    nodes: List[Node]

    def __post_init__(self) -> None:
        seen: Set[str] = set()
        for node in self.nodes:
            if node.id in seen:
                raise PipelineError(f"duplicate node id: {node.id}")
            seen.add(node.id)
        ids = {n.id for n in self.nodes}
        for node in self.nodes:
            for dep in node.deps:
                if dep not in ids:
                    raise PipelineError(
                        f"node {node.id!r} depends on unknown node {dep!r}"
                    )
        self._detect_cycles()

    def _detect_cycles(self) -> None:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {n.id: WHITE for n in self.nodes}
        by_id = {n.id: n for n in self.nodes}

        def visit(node_id: str, path: List[str]) -> None:
            if color[node_id] == GRAY:
                cycle = " -> ".join(path + [node_id])
                raise PipelineError(f"cycle detected: {cycle}")
            if color[node_id] == BLACK:
                return
            color[node_id] = GRAY
            for dep in by_id[node_id].deps:
                visit(dep, path + [node_id])
            color[node_id] = BLACK

        for node in self.nodes:
            visit(node.id, [])

    def topological_order(self) -> List[Node]:
        by_id = {n.id: n for n in self.nodes}
        order: List[Node] = []
        visited: Set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            for dep in by_id[node_id].deps:
                visit(dep)
            order.append(by_id[node_id])

        for node in self.nodes:
            visit(node.id)
        return order

    def subgraph(self, target_ids: Iterable[str]) -> "Pipeline":
        """Return a sub-pipeline containing the targets and their ancestors."""
        by_id = {n.id: n for n in self.nodes}
        keep: Set[str] = set()

        def collect(node_id: str) -> None:
            if node_id in keep:
                return
            if node_id not in by_id:
                raise PipelineError(f"unknown node {node_id!r}")
            keep.add(node_id)
            for dep in by_id[node_id].deps:
                collect(dep)

        for tid in target_ids:
            collect(tid)
        return Pipeline(
            name=f"{self.name}:subset",
            nodes=[n for n in self.nodes if n.id in keep],
        )

    def leaf_nodes(self) -> List[Node]:
        consumed: Set[str] = set()
        for n in self.nodes:
            consumed.update(n.deps)
        return [n for n in self.nodes if n.id not in consumed]
