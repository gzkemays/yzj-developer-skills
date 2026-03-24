"""Run i18n audit and print standardized report blocks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).parent))

from _common import read_text


def run_python(script: Path, args: list[str]) -> dict[str, Any]:
    """Execute python script and parse JSON stdout."""
    cmd = ["python", str(script), *args]
    completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def print_block(name: str, payload: dict[str, Any]) -> None:
    """Print one standardized output block."""
    print(f"===== {name} =====")
    print(json.dumps(payload, ensure_ascii=True, indent=2))
    print()


def load_updates(path: str | None) -> dict[str, Any]:
    """Read updates json when provided."""
    if not path:
        return {}
    return json.loads(read_text(Path(path)))


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Run i18n audit workflow")
    parser.add_argument("--app-dts", required=True, help="Path to app.d.ts")
    parser.add_argument("--langs-dir", required=True, help="Path to locales/langs")
    parser.add_argument("--src-dir", required=True, help="Path to source directory")
    parser.add_argument("--updates", help="Optional updates json path for language diffs")
    parser.add_argument("--apply-updates", action="store_true", help="Write updates into locale files")
    args = parser.parse_args()

    scripts_dir = Path(__file__).parent

    lang_updates = {}
    updates = load_updates(args.updates)
    if updates:
        temp_path = Path(args.updates)
        lang_updates = run_python(
            scripts_dir / "sort_and_merge_keys.py",
            ["--langs-dir", args.langs_dir, "--updates", str(temp_path), *(["--apply"] if args.apply_updates else [])],
        )

    validation = run_python(
        scripts_dir / "validate_i18n_integrity.py",
        ["--app-dts", args.app_dts, "--langs-dir", args.langs_dir],
    )
    hardcoded = run_python(
        scripts_dir / "detect_hardcoded_literals.py",
        ["--src-dir", args.src_dir],
    )

    print_block("LANG_FILE_UPDATES", lang_updates)
    print_block("I18N_VALIDATION", validation)
    print_block("HARD_CODED_REPORT", hardcoded)


if __name__ == "__main__":
    main()
