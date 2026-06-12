"""Detect hardcoded user-facing literals and propose i18n keys."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TEXT_FILE_PATTERNS = ("*.vue", "*.ts", "*.tsx", "*.js", "*.jsx")
IGNORE_DIRS = {"node_modules", "dist", "dist-electron", ".git", ".claude"}


def is_chinese_text(text: str) -> bool:
    """Check whether text contains Chinese chars."""
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def normalize_key_segment(text: str) -> str:
    """Convert text to key segment."""
    clean = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text.strip().lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean or "text"


def suggest_key(file_path: Path, literal: str) -> str:
    """Generate a deterministic key by file + literal."""
    stem = normalize_key_segment(file_path.stem)
    segment = normalize_key_segment(literal)[:32]
    return f"page.{stem}.{segment}"


def scan_file(path: Path) -> list[dict[str, str | int]]:
    """Scan one source file for hardcoded literals."""
    findings: list[dict[str, str | int]] = []
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    # Match quoted Chinese strings and template text nodes containing Chinese.
    patterns = [
        re.compile(r"['\"]([^'\"]*[\u4e00-\u9fff][^'\"]*)['\"]"),
        re.compile(r">([^<]*[\u4e00-\u9fff][^<]*)<"),
    ]
    for line_num, line in enumerate(lines, start=1):
        if "$t(" in line:
            continue
        for pattern in patterns:
            for match in pattern.finditer(line):
                literal = match.group(1).strip()
                if not literal or len(literal) < 2:
                    continue
                findings.append(
                    {
                        "file": str(path).replace("\\", "/"),
                        "line": line_num,
                        "literal": literal,
                        "snippet": line.strip(),
                        "suggested_key": suggest_key(path, literal),
                    }
                )
    return findings


def should_skip(path: Path) -> bool:
    """Ignore generated and dependency directories."""
    return any(part in IGNORE_DIRS for part in path.parts)


def main() -> None:
    """CLI entry."""
    parser = argparse.ArgumentParser(description="Detect hardcoded literals")
    parser.add_argument("--src-dir", required=True, help="Path to source directory")
    args = parser.parse_args()

    src_dir = Path(args.src_dir)
    all_findings: list[dict[str, str | int]] = []
    for pattern in TEXT_FILE_PATTERNS:
        for path in src_dir.rglob(pattern):
            if should_skip(path):
                continue
            if path.is_file():
                all_findings.extend(scan_file(path))

    # Keep unique by file-line-literal.
    unique = {(f["file"], f["line"], f["literal"]): f for f in all_findings}
    findings = sorted(unique.values(), key=lambda item: (item["file"], int(item["line"])))
    print(json.dumps({"count": len(findings), "items": findings}, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
