#!/usr/bin/env python3
"""Check project skill discovery paths statically; this is not a host runtime test.

Usage: python check-skill-discovery.py PROJECT --hosts codex,claude
       [--cwd PROJECT_RELATIVE_OR_ABSOLUTE_PATH ...] [--json FILE]

Requires Python 3.11 or later. Only project files are inspected. User/managed configuration, plugin caches,
trust, and model invocation are outside this check. A framework_ref is a local
audit convention, not a field that a host follows automatically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
import re
import sys
import tomllib


LAYOUTS = {"codex": ".agents", "claude": ".claude", "generic": "common"}
REQUIRED = (
    "dev-session", "pre-dev-alignment", "progress-tracker", "iteration-planner",
    "team-memory", "capability-registry", "similar-issue-sweep", "dev-output", "git-commit",
)
EXCLUDED = {".git", ".worktree", ".scratch", "node_modules", "target", "dist", "reports", "__pycache__"}
FRAMEWORK = Path(__file__).resolve().parent.parent
PLUGIN_AREAS = {"yzj-flow": "common/skills", "yzj-backend": "backend", "yzj-frontend": "frontend"}


def scalar(value: str) -> str:
    """Read the simple YAML string subset used by skill manifests."""
    value = value.strip()
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, str) else ""
        except ValueError:
            return ""
    if value.startswith("'"):
        return value[1:-1].replace("''", "'") if value.endswith("'") and len(value) >= 2 else ""
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    return "" if value.startswith(("[", "{", "&", "*", "!")) or value in {"null", "~"} else value


def frontmatter(text: str) -> tuple[dict, str, list[str]]:
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, ["缺少 frontmatter"]
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text, ["frontmatter 未闭合"]
    fields: dict = {}
    errors: list[str] = []
    fm = lines[1:end]
    for i, line in enumerate(fm):
        match = re.match(r"^(name|description|metadata):\s*(.*)$", line)
        if not match:
            continue
        key, raw = match.groups()
        if key in fields:
            errors.append("frontmatter 字段重复: " + key)
        if key == "metadata":
            fields[key] = True
            if raw.strip() not in {"", "{}"}:
                errors.append("metadata 须使用缩进映射")
            children = []
            for child in fm[i + 1:]:
                if child.strip() and not child.lstrip().startswith("#"):
                    indent = len(child) - len(child.lstrip())
                    if indent == 0:
                        break
                    children.append((indent, child.strip()))
            if children:
                level = min(indent for indent, _ in children)
                for indent, child in children:
                    if indent == level and child.startswith("framework_ref:"):
                        if "framework_ref" in fields:
                            errors.append("metadata.framework_ref 重复")
                        fields["framework_ref"] = scalar(child.split(":", 1)[1])
            continue
        value = scalar(raw)
        if key == "description" and value in {">", "|", ">-", "|-", ">+", "|+"}:
            block = []
            for child in fm[i + 1:]:
                if child.strip() and not child[0].isspace():
                    break
                if child.strip() and not child.lstrip().startswith("#"):
                    block.append(child.strip())
            value = " ".join(block)
        fields[key] = value
    for key in ("name", "description"):
        if not fields.get(key):
            errors.append("缺少有效 " + key)
    return fields, "\n".join(lines[end + 1:]), errors


def is_reparse(path: Path) -> bool:
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


class Audit:
    def __init__(self, project: Path):
        self.project = project.resolve()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.valid_refs: dict[str, dict] = {}
        self.cache: dict[tuple[str, str], dict | None] = {}

    def error(self, message: str) -> None:
        if message not in self.errors:
            self.errors.append(message)

    def within(self, path: Path) -> bool:
        return path.resolve().is_relative_to(self.project)

    def scopes(self) -> list[Path]:
        """Find checkout/start scopes without walking backup or reparse subtrees."""
        found = {self.project}
        pending = [self.project]
        while pending:
            directory = pending.pop()
            try:
                entries = list(directory.iterdir())
            except OSError as exc:
                self.error(f"无法清点目录 {directory}: {exc}")
                continue
            if ((directory / ".git").exists()
                    or any((directory / layout / "skills").exists() for layout in LAYOUTS.values())
                    or (directory / ".codex/config.toml").is_file()
                    or (directory / ".claude/settings.json").is_file()):
                found.add(directory)
            for entry in entries:
                if (entry.name in EXCLUDED or entry.name.startswith(".bak-")
                        or entry.name in {".agents", ".claude", ".codex"}
                        or (entry.name == "common" and (entry / "skills").exists())
                        or is_reparse(entry)):
                    continue
                if entry.is_dir():
                    pending.append(entry)
        return sorted(found, key=lambda p: str(p).casefold())

    def boundary(self, cwd: Path) -> tuple[Path, str]:
        current = cwd
        while True:
            if (current / ".git").exists():
                return current, "git-marker"
            if current == self.project:
                return current, "project-container"
            current = current.parent

    def read_manifest(self, path: Path) -> tuple[dict, str, list[str]]:
        if not self.within(path):
            return {}, "", ["路径通过链接或联接逃逸项目根"]
        try:
            return frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError) as exc:
            return {}, "", ["无法读取技能主文件: " + str(exc)]

    def skill(self, path: Path, host: str) -> dict | None:
        cache_key = (str(path), host)
        if cache_key in self.cache:
            return self.cache[cache_key]
        fields, body, problems = self.read_manifest(path)
        name = fields.get("name", "")
        if name and name != path.parent.name:
            problems.append(f"name={name} 与目录名 {path.parent.name} 不同")
        result = {"name": name, "path": str(path), "description": fields.get("description", "")}
        if "framework_ref" in fields:
            ref = fields["framework_ref"]
            ref_errors = []
            if host == "generic":
                ref_errors.append("framework_ref 只用于原生宿主入口")
            if (not ref or "\\" in ref or Path(ref).is_absolute()
                    or PureWindowsPath(ref).is_absolute() or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", ref)):
                ref_errors.append("framework_ref 必须是使用 / 的相对文件路径")
            else:
                target = (path.parent / ref).resolve()
                expected = self.project / LAYOUTS[host] / "skills" / path.parent.name / "SKILL.md"
                if not self.within(target) or target != expected.resolve():
                    ref_errors.append("framework_ref 必须指向共同根同宿主同名完整技能")
                elif path.resolve() == target:
                    ref_errors.append("framework_ref 不能指向自己")
                else:
                    target_fields, _, target_errors = self.read_manifest(target)
                    if target_errors:
                        ref_errors.append("framework_ref 目标无效: " + "; ".join(target_errors))
                    if target_fields.get("name") != name:
                        ref_errors.append("framework_ref 目标 name 不一致，不允许别名")
                    if " ".join(target_fields.get("description", "").split()) != " ".join(fields.get("description", "").split()):
                        ref_errors.append("共享入口 description 与完整正文不一致，可能改变技能路由")
                    if "framework_ref" in target_fields:
                        ref_errors.append("framework_ref 目标仍是引用，禁止引用链或环")
                    result["target"] = str(target)
            try:
                if {p.name for p in path.parent.iterdir()} != {"SKILL.md"}:
                    ref_errors.append("共享入口目录只允许 SKILL.md，不保留旧 references 或脚本")
            except OSError as exc:
                ref_errors.append("无法清点共享入口目录: " + str(exc))
            visible_body = re.sub(r"(?ms)^\s*```[^\n]*\n.*?^\s*```\s*$", "", body)
            links = re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", visible_body)
            if ref not in links:
                ref_errors.append("正文缺少与 framework_ref 完全一致的相对链接")
            problems.extend(ref_errors)
            result["framework_ref"] = ref
            if not problems:
                self.valid_refs[str(path)] = {
                    "path": str(path), "target": result["target"], "name": name, "host": host,
                }
        for problem in problems:
            self.error(f"{path}: {problem}")
        self.cache[cache_key] = result if name else None
        return self.cache[cache_key]

    def skills_at(self, directory: Path, host: str) -> list[dict]:
        installed = directory / LAYOUTS[host] / "skills"
        if not installed.exists():
            return []
        if not installed.is_dir() or not self.within(installed):
            self.error(f"无效技能目录或逃逸项目根: {installed}")
            return []
        result = []
        try:
            children = sorted(installed.iterdir(), key=lambda p: p.name.casefold())
        except OSError as exc:
            self.error(f"无法清点技能目录 {installed}: {exc}")
            return result
        for child in children:
            if not child.is_dir():
                continue
            if not self.within(child):
                self.error(f"技能链接或联接逃逸项目根: {child}")
                continue
            skill = self.skill(child / "SKILL.md", host)
            if skill:
                result.append(skill)
        return result

    def plugin_states_at(self, directory: Path, host: str) -> dict[str, tuple[bool, str]]:
        if host == "generic":
            return {}
        config = directory / (".codex/config.toml" if host == "codex" else ".claude/settings.json")
        if not config.is_file():
            return {}
        if not self.within(config):
            self.error(f"插件配置逃逸项目根: {config}")
            return {}
        try:
            text = config.read_text(encoding="utf-8-sig")
            values = tomllib.loads(text).get("plugins", {}) if host == "codex" else json.loads(text).get("enabledPlugins", {})
            if not isinstance(values, dict):
                raise ValueError("插件配置不是映射")
        except (OSError, UnicodeError, ValueError, AttributeError) as exc:
            self.error(f"无法解析插件配置 {config}: {exc}")
            return {}
        result = {}
        for key, value in values.items():
            enabled = value.get("enabled") if host == "codex" and isinstance(value, dict) else value
            if not isinstance(enabled, bool) or not key.endswith("@yzj-skills"):
                continue
            name = key.split("@", 1)[0]
            if name not in PLUGIN_AREAS:
                self.error(f"未知框架插件 {key}: {config}")
                continue
            result[name] = (enabled, str(config))
        return result

    def plugins_for(self, directories: list[Path], host: str) -> list[dict]:
        states = {}
        # Codex repository configuration is layered from the repository root
        # to cwd; a nearer enabled=false must suppress a parent declaration.
        # For the other host, inspect only this launch scope's settings.
        config_scopes = reversed(directories) if host == "codex" else directories[:1]
        for directory in config_scopes:
            states.update(self.plugin_states_at(directory, host))
        result = []
        for name, (enabled, config) in states.items():
            if not enabled:
                continue
            names = sorted(p.parent.name for p in (FRAMEWORK / PLUGIN_AREAS[name]).glob("*/SKILL.md"))
            if not names:
                self.error(f"缺少插件技能基线 {name}: {FRAMEWORK / PLUGIN_AREAS[name]}")
            result.append({"name": name, "config": config, "skills": names, "installed": "not-tested"})
        return result

    def matrix_row(self, cwd: Path, host: str) -> dict:
        boundary, boundary_type = self.boundary(cwd)
        directories = []
        current = cwd
        while True:
            directories.append(current)
            if current == boundary:
                break
            current = current.parent
        # Generic is an explicit local route, not a host discovery mechanism.
        if host == "generic":
            directories = [cwd]
        skills = [skill for directory in directories for skill in self.skills_at(directory, host)]
        # Declarations are checked without assuming an installed plugin cache.
        plugins = self.plugins_for(directories, host)
        sources: dict[str, list[str]] = {}
        for skill in skills:
            sources.setdefault(skill["name"], []).append(skill["path"])
        for plugin in plugins:
            for name in plugin["skills"]:
                sources.setdefault(name, []).append(f"plugin:{plugin['name']} ({plugin['config']})")
        duplicates = {name: paths for name, paths in sources.items() if len(paths) > 1}
        for name, paths in duplicates.items():
            self.error(f"{cwd} [{host}]: 技能重名或插件双装 {name}: " + " | ".join(paths))
        missing = sorted(set(REQUIRED) - sources.keys())
        if missing:
            self.error(f"{cwd} [{host}]: 缺少可发现的必需流程技能: " + ", ".join(missing))
        if host != "generic":
            for directory in directories:
                legacy = directory / "common/skills"
                if legacy.is_dir():
                    self.error(f"{cwd} [{host}]: 遗留 {legacy} 不属于原生技能安装，需迁移或明确按 generic 手动读取")
        return {
            "cwd": str(cwd), "host": host, "boundary": str(boundary), "boundary_type": boundary_type,
            "mode": "manual" if host == "generic" else "native-path-static",
            "search_paths": [str(p / LAYOUTS[host] / "skills") for p in directories],
            "skills": skills, "plugins": plugins, "missing": missing, "duplicates": duplicates,
        }

    def run(self, requested_hosts: list[str] | None, requested_cwds: list[Path]) -> dict:
        scopes = self.scopes()
        hosts = requested_hosts
        if hosts is None:
            hosts = []
            for host in ("codex", "claude"):
                config_name = ".codex/config.toml" if host == "codex" else ".claude/settings.json"
                if any((p / LAYOUTS[host] / "skills").exists() or (p / config_name).is_file() for p in scopes):
                    hosts.append(host)
            if not hosts and any((p / "common/skills").exists() for p in scopes):
                hosts = ["generic"]
                self.warnings.append("仅发现 common/skills，按 generic 显式手动读取审计；不代表任何宿主原生发现。")
            if not hosts:
                self.error("未发现技能安装，无法推断宿主；onboarding 应显式传入 --hosts。")
        selected = []
        for item in requested_cwds or scopes:
            cwd = (self.project / item).resolve() if not item.is_absolute() else item.resolve()
            if not cwd.is_dir() or not self.within(cwd):
                self.error(f"启动目录不存在或不在项目根内: {cwd}")
                continue
            if cwd not in selected:
                selected.append(cwd)
        matrix = [self.matrix_row(cwd, host) for cwd in selected for host in hosts]
        return {
            "kind": "static", "runtime_discovery_tested": False,
            "project_root": str(self.project), "hosts": hosts, "required_skills": list(REQUIRED),
            "matrix": matrix, "valid_refs": list(self.valid_refs.values()),
            "errors": self.errors, "warnings": self.warnings, "passed": not self.errors,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--hosts", help="预期宿主，逗号分隔: codex,claude 或 generic；接入时必须显式填写")
    parser.add_argument("--cwd", action="append", type=Path, default=[], help="启动目录，可重复；相对路径基于 PROJECT")
    parser.add_argument("--json", type=Path, dest="json_path", help="写入审计证据 JSON")
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        parser.error("项目目录不存在")
    hosts = None
    if args.hosts is not None:
        hosts = list(dict.fromkeys(h.strip() for h in args.hosts.split(",")))
        if not hosts or any(h not in LAYOUTS for h in hosts) or ("generic" in hosts and len(hosts) > 1):
            parser.error("--hosts 使用 codex、claude、codex,claude 或 generic")
    result = Audit(args.project).run(hosts, args.cwd)
    print("静态技能发现路径检查（未运行宿主发现或模型触发；不包含用户/托管配置覆盖）")
    for row in result["matrix"]:
        print(f"{row['host']:7} {row['cwd']} -> {row['boundary']} | 本地 {len(row['skills'])}，插件声明 {len(row['plugins'])}，缺失 {len(row['missing'])}，重名 {len(row['duplicates'])}")
    for message in result["warnings"]:
        print("提示: " + message)
    for message in result["errors"]:
        print("错误: " + message)
    print(f"合法共享入口 {len(result['valid_refs'])}，错误 {len(result['errors'])}")
    if args.json_path:
        args.json_path.parent.mkdir(parents=True, exist_ok=True)
        args.json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
