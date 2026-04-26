"""A tiny YAML subset parser used to load pipeline configs.

Supports exactly what the example configs need:

  - block mappings: ``key: value``
  - block sequences: ``- item``
  - flow mappings: ``{a: 1, b: 2}``
  - flow sequences: ``[1, 2, 3]``
  - quoted strings (single or double, with backslash escapes in double)
  - bare scalars: int, float, true/false, null, plain string
  - comments starting with ``#``

This is intentionally not a full YAML implementation. It exists so the
package has zero runtime dependencies; for richer use-cases swap in PyYAML.
"""

from __future__ import annotations

from typing import Any, List, Tuple


class YamlError(Exception):
    pass


def parse_yaml(text: str) -> Any:
    raw_lines = text.splitlines()
    lines: List[Tuple[int, str]] = []  # (indent, content)
    for raw in raw_lines:
        stripped = _strip_comment(raw).rstrip()
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        lines.append((indent, stripped.lstrip(" ")))
    if not lines:
        return None
    value, idx = _parse_block(lines, 0, lines[0][0])
    if idx != len(lines):
        raise YamlError(f"unexpected trailing content at line {idx}")
    return value


def _strip_comment(line: str) -> str:
    out: List[str] = []
    in_single = False
    in_double = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            if i > 0 and line[i - 1] == "\\":
                pass
            else:
                in_double = not in_double
        elif ch == "#" and not in_single and not in_double:
            break
        out.append(ch)
        i += 1
    return "".join(out)


def _parse_block(lines: List[Tuple[int, str]], idx: int, indent: int) -> Tuple[Any, int]:
    if idx >= len(lines):
        return None, idx
    cur_indent, cur = lines[idx]
    if cur.startswith("- "):
        return _parse_sequence(lines, idx, indent)
    if cur == "-":
        return _parse_sequence(lines, idx, indent)
    return _parse_mapping(lines, idx, indent)


def _parse_sequence(lines, idx, indent):
    items: List[Any] = []
    while idx < len(lines):
        cur_indent, cur = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlError(f"unexpected indent at line {idx}: {cur!r}")
        if not (cur.startswith("- ") or cur == "-"):
            break
        rest = cur[2:] if cur.startswith("- ") else ""
        idx += 1
        if not rest.strip():
            # nested block follows
            if idx < len(lines) and lines[idx][0] > indent:
                child_indent = lines[idx][0]
                value, idx = _parse_block(lines, idx, child_indent)
                items.append(value)
            else:
                items.append(None)
            continue
        if ":" in rest and not _looks_like_scalar(rest):
            # inline mapping start, e.g. "- id: foo"
            synth = [(indent + 2, rest)]
            extra_idx = idx
            while extra_idx < len(lines) and lines[extra_idx][0] > indent:
                synth.append(lines[extra_idx])
                extra_idx += 1
            value, consumed = _parse_mapping(synth, 0, indent + 2)
            if consumed != len(synth):
                raise YamlError(
                    f"failed to parse inline mapping starting at line {idx - 1}"
                )
            idx = extra_idx
            items.append(value)
        else:
            items.append(_parse_scalar(rest))
    return items, idx


def _parse_mapping(lines, idx, indent):
    mapping: dict = {}
    while idx < len(lines):
        cur_indent, cur = lines[idx]
        if cur_indent < indent:
            break
        if cur_indent > indent:
            raise YamlError(f"unexpected indent at line {idx}: {cur!r}")
        if cur.startswith("- ") or cur == "-":
            break
        key, sep, rest = _split_key(cur)
        if not sep:
            raise YamlError(f"expected mapping at line {idx}: {cur!r}")
        idx += 1
        rest = rest.strip()
        if rest:
            mapping[key] = _parse_scalar(rest)
            continue
        # nested block
        if idx < len(lines) and lines[idx][0] > indent:
            child_indent = lines[idx][0]
            value, idx = _parse_block(lines, idx, child_indent)
            mapping[key] = value
        else:
            mapping[key] = None
    return mapping, idx


def _split_key(line: str) -> Tuple[str, bool, str]:
    in_single = False
    in_double = False
    for i, ch in enumerate(line):
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif ch == ":" and not in_single and not in_double:
            if i + 1 == len(line) or line[i + 1] in (" ", "\t"):
                return _unquote(line[:i].strip()), True, line[i + 1 :]
    return line, False, ""


def _looks_like_scalar(s: str) -> bool:
    s = s.strip()
    if not s:
        return True
    if s[0] in "[{\"'":
        return True
    if ":" not in s:
        return True
    return False


def _parse_scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if text[0] == "[":
        return _parse_flow_sequence(text)
    if text[0] == "{":
        return _parse_flow_mapping(text)
    if text[0] in ("'", '"'):
        return _unquote(text)
    low = text.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        if "." in text or "e" in text.lower():
            return float(text)
        return int(text)
    except ValueError:
        return text


def _unquote(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        body = text[1:-1]
        if text[0] == '"':
            return bytes(body, "utf-8").decode("unicode_escape")
        return body
    return text


def _parse_flow_sequence(text: str) -> list:
    items, end = _consume_flow(text, 0)
    if end != len(text.strip()):
        raise YamlError(f"trailing garbage in flow sequence: {text!r}")
    return items


def _parse_flow_mapping(text: str) -> dict:
    items, end = _consume_flow(text, 0)
    if end != len(text.strip()):
        raise YamlError(f"trailing garbage in flow mapping: {text!r}")
    return items


def _consume_flow(text: str, idx: int):
    text = text.strip()
    if text[idx] == "[":
        return _consume_flow_seq(text, idx)
    if text[idx] == "{":
        return _consume_flow_map(text, idx)
    raise YamlError(f"expected flow start at {idx}: {text!r}")


def _consume_flow_seq(text, idx):
    assert text[idx] == "["
    idx += 1
    items: List[Any] = []
    while True:
        idx = _skip_ws(text, idx)
        if idx >= len(text):
            raise YamlError("unterminated flow sequence")
        if text[idx] == "]":
            return items, idx + 1
        value, idx = _consume_flow_value(text, idx)
        items.append(value)
        idx = _skip_ws(text, idx)
        if idx < len(text) and text[idx] == ",":
            idx += 1
            continue
        if idx < len(text) and text[idx] == "]":
            return items, idx + 1
        raise YamlError(f"expected ',' or ']' at {idx} in {text!r}")


def _consume_flow_map(text, idx):
    assert text[idx] == "{"
    idx += 1
    out: dict = {}
    while True:
        idx = _skip_ws(text, idx)
        if idx >= len(text):
            raise YamlError("unterminated flow mapping")
        if text[idx] == "}":
            return out, idx + 1
        key, idx = _consume_flow_token(text, idx, stop=":")
        idx = _skip_ws(text, idx)
        if idx >= len(text) or text[idx] != ":":
            raise YamlError(f"expected ':' in flow mapping at {idx}")
        idx += 1
        idx = _skip_ws(text, idx)
        value, idx = _consume_flow_value(text, idx)
        out[_unquote(key)] = value
        idx = _skip_ws(text, idx)
        if idx < len(text) and text[idx] == ",":
            idx += 1
            continue
        if idx < len(text) and text[idx] == "}":
            return out, idx + 1
        raise YamlError(f"expected ',' or '}}' at {idx} in {text!r}")


def _consume_flow_value(text, idx):
    if text[idx] == "[":
        return _consume_flow_seq(text, idx)
    if text[idx] == "{":
        return _consume_flow_map(text, idx)
    token, idx = _consume_flow_token(text, idx, stop=",]}")
    return _parse_scalar(token), idx


def _consume_flow_token(text, idx, stop):
    in_single = False
    in_double = False
    start = idx
    while idx < len(text):
        ch = text[idx]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double and ch in stop:
            break
        idx += 1
    return text[start:idx].strip(), idx


def _skip_ws(text, idx):
    while idx < len(text) and text[idx] in " \t":
        idx += 1
    return idx
