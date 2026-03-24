"""i18n skill shared helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def read_text(path: Path) -> str:
    """Read utf-8 text from file path."""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    """Write utf-8 text to file path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def find_balanced_block(text: str, start_token: str) -> str:
    """Extract balanced braces block after a token."""
    start = text.find(start_token)
    if start < 0:
        raise ValueError(f"token not found: {start_token}")
    brace_start = text.find("{", start)
    if brace_start < 0:
        raise ValueError(f"no '{{' found after token: {start_token}")
    depth = 0
    for idx in range(brace_start, len(text)):
        ch = text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[brace_start : idx + 1]
    raise ValueError(f"unbalanced braces after token: {start_token}")


def strip_ts_comments(content: str) -> str:
    """Remove TypeScript single/multi-line comments."""
    no_block = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return re.sub(r"//.*", "", no_block)


def quote_object_keys(content: str) -> str:
    """Quote js object keys before JSON parsing."""
    return re.sub(r"([,{]\s*)([A-Za-z_][A-Za-z0-9_-]*)(\s*:)", r'\1"\2"\3', content)


def normalize_single_quote(content: str) -> str:
    """Convert ts single quotes into JSON double quotes."""
    return re.sub(r"'((?:[^'\\\\]|\\\\.)*)'", lambda m: json.dumps(m.group(1)), content)


def remove_trailing_commas(content: str) -> str:
    """Remove trailing commas before closing braces/brackets."""
    return re.sub(r",\s*([}\]])", r"\1", content)


def ts_object_to_dict(raw_object: str) -> dict[str, Any]:
    """Convert a TS object-literal like content into dict."""
    text = strip_ts_comments(raw_object)
    text = normalize_single_quote(text)
    text = quote_object_keys(text)
    text = remove_trailing_commas(text)
    return json.loads(text)


def flatten_dict(data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten nested dict with dot separated keys."""
    result: dict[str, Any] = {}
    for key, value in data.items():
        current = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_dict(value, current))
        else:
            result[current] = value
    return result

