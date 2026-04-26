"""Formatting transforms (templating, chat conversion, normalization)."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .registry import register


_TEMPLATE_RE = re.compile(r"\{(\w+)\}")


@register("format_template")
def format_template(inputs, template: str, output_field: str = "text") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in inputs[0]:
        rendered = _TEMPLATE_RE.sub(lambda m: str(r.get(m.group(1), "")), template)
        out.append({**r, output_field: rendered})
    return out


@register("format_chat")
def format_chat(
    inputs,
    prompt_field: str = "prompt",
    response_field: str = None,
    role: str = "user",
    system: str = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in inputs[0]:
        messages: List[Dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": role, "content": str(r.get(prompt_field, ""))})
        if response_field and r.get(response_field) is not None:
            messages.append({"role": "assistant", "content": str(r[response_field])})
        out.append({"messages": messages})
    return out


@register("rename_fields")
def rename_fields(inputs, mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    return [
        {mapping.get(k, k): v for k, v in r.items()}
        for r in inputs[0]
    ]


@register("lowercase_field")
def lowercase_field(inputs, field: str) -> List[Dict[str, Any]]:
    out = []
    for r in inputs[0]:
        new = dict(r)
        if field in new and new[field] is not None:
            new[field] = str(new[field]).lower()
        out.append(new)
    return out


@register("strip_field")
def strip_field(inputs, field: str) -> List[Dict[str, Any]]:
    out = []
    for r in inputs[0]:
        new = dict(r)
        if field in new and new[field] is not None:
            new[field] = str(new[field]).strip()
        out.append(new)
    return out


@register("concat")
def concat(inputs) -> List[Any]:
    """Concatenate multiple upstream record lists in order."""
    out: List[Any] = []
    for upstream in inputs:
        out.extend(upstream)
    return out
