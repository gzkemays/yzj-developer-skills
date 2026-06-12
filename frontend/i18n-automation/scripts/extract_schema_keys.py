"""Extract i18n keys from App.I18n.Schema in app.d.ts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from _common import find_balanced_block, read_text


def extract_schema_block(content: str) -> str:
    """Extract `type Schema = { ... }` block from app.d.ts."""
    marker = "type Schema ="
    start = content.find(marker)
    if start < 0:
        raise ValueError("cannot find `type Schema =` in app.d.ts")
    return find_balanced_block(content[start:], "{")


def tokenize(block: str) -> list[str]:
    """Tokenize a TS type block."""
    pattern = r'"[^"]+"|\'[^\']+\'|[A-Za-z_][A-Za-z0-9_-]*|[{}:;]'
    return re.findall(pattern, block)


def parse_keys(tokens: list[str]) -> set[str]:
    """Parse object-style type block and return dot keys."""
    idx = 0
    paths: set[str] = set()

    def parse_object(prefix: str = "") -> None:
        nonlocal idx
        if idx >= len(tokens) or tokens[idx] != "{":
            return
        idx += 1
        while idx < len(tokens) and tokens[idx] != "}":
            token = tokens[idx]
            if token in {";", ":"}:
                idx += 1
                continue
            key = token.strip("\"'")
            idx += 1
            if idx < len(tokens) and tokens[idx] == ":":
                idx += 1
            full_key = f"{prefix}.{key}" if prefix else key
            if idx < len(tokens) and tokens[idx] == "{":
                parse_object(full_key)
            else:
                paths.add(full_key)
                while idx < len(tokens) and tokens[idx] not in {";", "}"}:
                    idx += 1
            if idx < len(tokens) and tokens[idx] == ";":
                idx += 1
        if idx < len(tokens) and tokens[idx] == "}":
            idx += 1

    parse_object()
    return paths


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Extract i18n schema keys")
    parser.add_argument("--app-dts", required=True, help="Path to src/typings/app.d.ts")
    args = parser.parse_args()

    content = read_text(Path(args.app_dts))
    schema_block = extract_schema_block(content)
    keys = sorted(parse_keys(tokenize(schema_block)))
    print(json.dumps({"count": len(keys), "keys": keys}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
