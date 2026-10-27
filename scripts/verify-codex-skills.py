"""Validate Codex skill packages and compare a project with this repository."""

from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = {
    "dev-session", "pre-dev-alignment", "progress-tracker", "iteration-planner",
    "team-memory", "capability-registry", "similar-issue-sweep", "dev-output", "git-commit",
}
SKIP = {".git", ".claude", ".idea", "node_modules", "__pycache__", ".worktree", ".worktrees"}
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".html"}


def skill_directories(project: Path) -> list[Path]:
    """Find discoverable skill locations, without traversing dependencies or trees."""
    found = []
    for current, directories, _ in os.walk(project, followlinks=False):
        directories[:] = sorted(d for d in directories if d not in SKIP and not d.startswith(".bak-"))
        current_path = Path(current)
        if current_path.name == "skills" and current_path.parent.name == ".agents":
            found.append(current_path)
            directories[:] = []
    return sorted(found)


def metadata(path: Path) -> tuple[str, str]:
    """Read required scalar metadata; support quoted scalars and YAML blocks."""
    text = path.read_text(encoding="utf-8-sig")
    front = re.match(r"\A---\s*\n(.*?)\n---(?:\n|$)", text, re.S)
    if not front:
        raise ValueError("missing YAML frontmatter")
    values = {}
    for key in ("name", "description"):
        match = re.search(rf"^{key}:\s*([^\n]*)", front[1], re.M)
        if not match:
            raise ValueError(f"missing {key}")
        value = match[1].strip()
        if value in ("|", ">", "|-", ">-", "|+", ">+"):
            rest = front[1][match.end():]
            value = " ".join(re.findall(r"^\s+([^\n]+)", rest, re.M))
        elif value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"empty or invalid {key}")
        values[key] = value
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", values["name"]) or len(values["name"]) > 64:
        raise ValueError("invalid skill name")
    if len(values["description"]) > 1024:
        raise ValueError("description longer than 1024 characters")
    return values["name"], values["description"]


def package_files(folder: Path) -> dict[Path, bytes]:
    files = {}
    for path in folder.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        if path.suffix in TEXT_SUFFIXES:
            data = data.replace(b"\r\n", b"\n")
        files[path.relative_to(folder)] = data
    return files


def local_links(path: Path) -> list[Path]:
    """Return local Markdown link targets; external URLs and templates are skipped."""
    text = path.read_text(encoding="utf-8")
    # A document skeleton inside a fenced example is not a package reference.
    text = re.sub(r"(?ms)^```[^\n]*\n.*?^```[ \t]*$", "", text)
    links = []
    for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
        if "://" in target or target.startswith("#") or "{" in target:
            continue
        target = target.split("#", 1)[0].strip("<>")
        if target:
            links.append(path.parent / target)
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", nargs="?", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true", help="Fail on any known-package drift, including project overrides")
    parser.add_argument("--show-diff", action="store_true")
    parser.add_argument("--require-area", action="append", choices=("general", "backend", "frontend"), default=[])
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error(f"project does not exist: {project}")
    catalog = json.loads((ROOT / ".agents/catalog.json").read_text(encoding="utf-8"))["skills"]
    locations = skill_directories(project)
    errors = drift = checked = 0

    def error(message: str) -> None:
        nonlocal errors
        errors += 1
        print(f"ERROR {message}")

    if not locations:
        error("no .agents/skills directory found")
    root_skills = project / ".agents/skills"
    required = set(REQUIRED)
    if project == ROOT:
        required.update(catalog)
    for name, item in catalog.items():
        if item["area"] in args.require_area:
            required.add(name)
    installed = {folder.name for location in locations for folder in location.iterdir() if folder.is_dir()}
    for name in sorted(required - installed):
        error(f"missing required skill: {name}")
    for name in sorted(REQUIRED):
        if not (root_skills / name / "SKILL.md").is_file():
            error(f"project-root flow entry missing: {name}")
    agents = project / "AGENTS.md"
    if not agents.is_file():
        error("project root missing AGENTS.md")
    elif project != ROOT:
        text = agents.read_text(encoding="utf-8")
        for placeholder in ("{项目名}", "{framework skills 仓库绝对路径}", "{实际 .document 位置}", "{实际编译和测试命令}"):
            if placeholder in text:
                error(f"AGENTS.md has unfilled placeholder: {placeholder}")
        if ".agents/rules/collaboration.md" not in text:
            print("WARN AGENTS.md does not explicitly reference collaboration rules; inspect project-specific guidance")
    if not (project / ".agents/rules/collaboration.md").is_file():
        error("missing .agents/rules/collaboration.md")

    for location in locations:
        for folder in sorted(location.iterdir()):
            if not folder.is_dir() or folder.name == "__pycache__":
                continue
            manifest = folder / "SKILL.md"
            try:
                name, _ = metadata(manifest)
                if name != folder.name:
                    error(f"{manifest}: name does not match directory: {name}")
            except (OSError, ValueError) as exc:
                error(f"{manifest}: {exc}")
                continue
            checked += 1
            for markdown in folder.rglob("*.md"):
                for target in local_links(markdown):
                    if not target.exists():
                        error(f"{markdown}: broken reference {target}")
            if name not in catalog:
                print(f"PROJECT {folder.relative_to(project)}")
                continue
            expected = package_files(ROOT / ".agents/skills" / name)
            actual = package_files(folder)
            for relative in sorted(expected.keys() - actual.keys()):
                error(f"{folder}: missing resource {relative.as_posix()}")
            differences = sorted(relative for relative in expected.keys() & actual.keys() if expected[relative] != actual[relative])
            extras = actual.keys() - expected.keys()
            if differences or extras:
                drift += 1
                print(f"DRIFT {folder.relative_to(project)}: {len(differences)} changed, {len(extras)} project resources; inspect overrides")
                if args.show_diff:
                    for relative in differences:
                        if relative.suffix in TEXT_SUFFIXES:
                            print("".join(difflib.unified_diff(expected[relative].decode("utf-8").splitlines(True), actual[relative].decode("utf-8").splitlines(True), fromfile=f"baseline/{name}/{relative}", tofile=str(folder / relative))))
            else:
                print(f"OK {folder.relative_to(project)}")
    if agents.is_file():
        for target in local_links(agents):
            if not target.exists():
                error(f"AGENTS.md: broken reference {target}")
    print(f"Checked {checked} skills; drift {drift}; errors {errors}")
    return int(errors > 0 or (args.strict and drift > 0))


if __name__ == "__main__":
    raise SystemExit(main())
