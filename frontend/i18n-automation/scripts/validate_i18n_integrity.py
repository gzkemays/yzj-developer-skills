"""Validate schema coverage and locale completeness."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
import re

sys.path.append(str(Path(__file__).parent))

from _common import read_text
from extract_schema_keys import extract_schema_block, parse_keys, tokenize


KEY_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$")
START_PATTERN = re.compile(r"^\s*const\s+local\b")


def extract_locale_flat(text: str) -> tuple[dict[str, str], Counter[str], set[str]]:
    """Extract dotted keys from locale ts file with line parser."""
    lines = text.splitlines()
    in_local = False
    path_stack: list[str] = []
    key_values: dict[str, str] = {}
    counter: Counter[str] = Counter()
    empty_keys: set[str] = set()

    for raw in lines:
        line = raw.strip()
        if not in_local:
            if START_PATTERN.search(line):
                in_local = True
            continue
        if line.startswith("export default"):
            break

        # pop scopes by `}` count
        close_count = line.count("}")
        for _ in range(close_count):
            if path_stack:
                path_stack.pop()

        match = KEY_PATTERN.match(line)
        if not match:
            continue
        key, tail = match.group(1), match.group(2).strip()
        dotted = ".".join([*path_stack, key]) if path_stack else key
        counter[dotted] += 1

        if tail.startswith("{"):
            path_stack.append(key)
            continue

        # scalar value
        value = tail.rstrip(",")
        key_values[dotted] = value
        if value in {"''", '""'}:
            empty_keys.add(dotted)

    return key_values, counter, empty_keys


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Validate i18n consistency")
    parser.add_argument("--app-dts", required=True, help="Path to app.d.ts")
    parser.add_argument("--langs-dir", required=True, help="Path to locales/langs")
    args = parser.parse_args()

    schema_content = read_text(Path(args.app_dts))
    schema_keys = set(parse_keys(tokenize(extract_schema_block(schema_content))))

    langs_dir = Path(args.langs_dir)
    locales: dict[str, dict[str, str]] = {}
    duplicates: dict[str, list[str]] = {}
    empties_by_file: dict[str, list[str]] = {}
    for file_path in sorted(langs_dir.glob("*.ts")):
        mapping, counter, empty_keys = extract_locale_flat(read_text(file_path))
        locales[file_path.name] = mapping
        duplicates[file_path.name] = sorted([k for k, v in counter.items() if v > 1])
        empties_by_file[file_path.name] = sorted(empty_keys)

    zh_name = "zh-cn.ts"
    base_keys = set(locales.get(zh_name, {}).keys())
    missing_in_schema = sorted(base_keys - schema_keys)

    missing_translation: dict[str, list[str]] = {}
    empty_values: dict[str, list[str]] = {}
    for lang_file, mapping in locales.items():
        if lang_file == zh_name:
            continue
        missing_translation[lang_file] = sorted(base_keys - set(mapping.keys()))
        empty_values[lang_file] = empties_by_file.get(lang_file, [])

    report = {
        "missing_in_schema": missing_in_schema,
        "missing_translation": missing_translation,
        "duplicate_keys": duplicates,
        "empty_values": empty_values,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
