"""Merge i18n key updates and write sorted locale files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent))

from _common import find_balanced_block, read_text, ts_object_to_dict, write_text


def set_nested(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set nested value by dotted key."""
    parts = dotted_key.split(".")
    ref = data
    for part in parts[:-1]:
        if part not in ref or not isinstance(ref[part], dict):
            ref[part] = {}
        ref = ref[part]
    ref[parts[-1]] = value


def delete_nested(data: dict[str, Any], dotted_key: str) -> None:
    """Delete nested key by dotted key."""
    parts = dotted_key.split(".")
    ref = data
    for part in parts[:-1]:
        child = ref.get(part)
        if not isinstance(child, dict):
            return
        ref = child
    ref.pop(parts[-1], None)


def sort_nested(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sort keys in dict."""
    sorted_data: dict[str, Any] = {}
    for key in sorted(data.keys()):
        value = data[key]
        sorted_data[key] = sort_nested(value) if isinstance(value, dict) else value
    return sorted_data


def to_ts_object(data: dict[str, Any], indent: int = 0) -> str:
    """Render dict as TypeScript object literal."""
    pad = "  " * indent
    inner_pad = "  " * (indent + 1)
    lines: list[str] = ["{"]
    for key, value in data.items():
        if isinstance(value, dict):
            rendered = to_ts_object(value, indent + 1)
            lines.append(f"{inner_pad}{key}: {rendered},")
        else:
            text = str(value).replace("\\", "\\\\").replace("'", "\\'")
            lines.append(f"{inner_pad}{key}: '{text}',")
    lines.append(f"{pad}}}")
    return "\n".join(lines)


def update_locale_file(path: Path, updates: dict[str, Any], apply_changes: bool) -> dict[str, Any]:
    """Apply add/modify/delete updates into locale file."""
    content = read_text(path)
    obj = ts_object_to_dict(find_balanced_block(content, "const local"))
    added = updates.get("add", {})
    modified = updates.get("modify", {})
    deleted = updates.get("delete", [])

    for key, value in added.items():
        set_nested(obj, key, value)
    for key, value in modified.items():
        set_nested(obj, key, value)
    for key in deleted:
        delete_nested(obj, key)

    sorted_obj = sort_nested(obj)
    if apply_changes:
        replacement = f"const local: App.I18n.Schema = {to_ts_object(sorted_obj)};\n\nexport default local;\n"
        write_text(path, replacement)

    return {
        "added": sorted(list(added.keys())),
        "modified": sorted(list(modified.keys())),
        "deleted": sorted(deleted),
    }


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Merge and sort locale keys")
    parser.add_argument("--langs-dir", required=True, help="Path to locales/langs")
    parser.add_argument("--updates", required=True, help="Path to updates json")
    parser.add_argument("--apply", action="store_true", help="Apply file writes")
    args = parser.parse_args()

    updates = json.loads(read_text(Path(args.updates)))
    langs_dir = Path(args.langs_dir)
    report: dict[str, Any] = {}
    for lang_file, payload in updates.items():
        file_path = langs_dir / lang_file
        if file_path.exists():
            report[lang_file] = update_locale_file(file_path, payload, args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
