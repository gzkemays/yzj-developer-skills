"""Parse locale files into flattened key-value maps."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent))

from _common import find_balanced_block, flatten_dict, read_text, ts_object_to_dict


def extract_local_object(file_content: str) -> dict[str, Any]:
    """Extract `const local = { ... }` object as dict."""
    block = find_balanced_block(file_content, "const local")
    return ts_object_to_dict(block)


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Parse locale files")
    parser.add_argument("--langs-dir", required=True, help="Path to src/locales/langs")
    args = parser.parse_args()

    langs_dir = Path(args.langs_dir)
    result: dict[str, dict[str, Any]] = {}
    for file_path in sorted(langs_dir.glob("*.ts")):
        data = extract_local_object(read_text(file_path))
        result[file_path.name] = flatten_dict(data)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
