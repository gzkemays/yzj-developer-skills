"""Reproduce file-based skill-loading checks in disposable Windows fixtures.

Run with a Python 3 runtime and --bash pointing to Git Bash. No skills, rules,
or baseline scripts are modified. Only results.json is retained beside this file.
"""
import argparse
import concurrent.futures
import hashlib
import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    source = args.source.resolve()
    output = Path(__file__).resolve().with_name("results.json")
    work = source.parent / (".skill-full-validation-" + uuid.uuid4().hex)
    cases = []
    results = []

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    inspected = sorted([*source.glob("common/skills/*/SKILL.md"),
                        *source.glob("backend/*/SKILL.md"),
                        *source.glob("frontend/*/SKILL.md"),
                        source / "scripts/verify-baseline.sh", source / "AGENTS.md",
                        source / "templates/AGENTS.md.template"])
    before = {p.relative_to(source).as_posix(): digest(p) for p in inspected}
    revision = subprocess.run(["git", "-c", "safe.directory=" + source.as_posix(),
                               "-C", str(source), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    work.mkdir()
    baseline = work / "baseline"
    baseline.mkdir()
    for directory in ("common", "backend", "frontend", "templates", "scripts"):
        shutil.copytree(source / directory, baseline / directory)

    def safe_remove(path):
        resolved = path.resolve()
        if work.resolve() not in resolved.parents or resolved == work.resolve():
            raise RuntimeError("Refusing removal outside fixture tree: " + str(path))
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def copy_skills(area, target):
        target.mkdir(parents=True, exist_ok=True)
        for item in (baseline / area).iterdir():
            if item.is_dir():
                shutil.copytree(item, target / item.name, dirs_exist_ok=True)

    def root(name, layout="common"):
        target = work / name
        target.mkdir()
        copy_skills("common/skills", target / layout / "skills")
        shutil.copytree(baseline / "templates/common/rules", target / layout / "rules")
        shutil.copytree(baseline / "templates/.document", target / ".document")
        entry = "AGENTS.md" if layout == "common" else "CLAUDE.md"
        refs = [f"{layout}/rules/collaboration.md", f"{layout}/rules/api-contract.md",
                f"{layout}/skills/dev-session/SKILL.md",
                f"{layout}/skills/iteration-planner/SKILL.md", ".document/plan/STATUS.md"]
        write(target / entry, "# Validation fixture\n\n" + "\n".join(f"- [{p}]({p})" for p in refs))
        return target

    def split(name, layout="common"):
        target = root(name, layout)
        copy_skills("backend", target / "apps/api" / layout / "skills")
        copy_skills("frontend", target / "apps/web" / layout / "skills")
        write(target / "apps/api/pom.xml", "<project />\n")
        (target / "apps/web/src/views").mkdir(parents=True)
        return target

    def clone(template, name):
        target = work / name
        shutil.copytree(template, target)
        return target

    def single(name, area, marker):
        target = root(name)
        copy_skills(area, target / "common/skills")
        if marker == "pom":
            write(target / "pom.xml", "<project />\n")
        elif marker == "gradle":
            write(target / "build.gradle.kts", "// fixture\n")
        elif marker == "java":
            (target / "src/main/java").mkdir(parents=True)
        elif marker == "domain":
            (target / "domain").mkdir()
            (target / "integration").mkdir()
        elif marker == "views":
            (target / "src/views").mkdir(parents=True)
        elif marker == "package":
            write(target / "package.json", '{"dependencies":{"vue":"3.0.0"}}\n')
        return target

    def add(case_id, target, expected=0, ok=None, strict=True, fw=None,
            required=None, extra=None, script=None, omit_fw=False, note=""):
        cases.append(dict(id=case_id, target=target, expected=expected, ok=ok,
                          strict=strict, fw=fw or baseline, required=required,
                          extra=extra or [], script=script or baseline / "scripts/verify-baseline.sh",
                          omit_fw=omit_fw, note=note))

    def mutate(path, fn):
        path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")

    static = {"skill_count": 0, "metadata_errors": [], "resource_references": [],
              "reference_errors": [], "source_hashes": before}
    for path in inspected:
        if path.name != "SKILL.md":
            continue
        static["skill_count"] += 1
        text = path.read_text(encoding="utf-8")
        fm = re.match(r"\A---\r?\n(.*?)\r?\n---", text, re.S)
        name = re.search(r"^name:\s*([^\r\n]+)", fm[1], re.M) if fm else None
        description = re.search(r"^description:\s*\S", fm[1], re.M) if fm else None
        if not fm or not name or name[1].strip() != path.parent.name or not description:
            static["metadata_errors"].append(path.relative_to(source).as_posix())
        # Only concrete resources packaged with the skill, not project examples.
        for ref in sorted(set(re.findall(r"(?:scripts|references|agents|assets|eval-viewer)/[\w.-]+\.(?:py|md|json|html)", text))):
            record = {"skill": path.relative_to(source).as_posix(), "reference": ref,
                      "exists": (path.parent / ref).is_file()}
            static["resource_references"].append(record)
            if not record["exists"]:
                static["reference_errors"].append(record)

    try:
        common = split("split-common")
        claude = split("split-claude", ".claude")
        add("split-common", common, ok=34)
        add("split-claude", claude, ok=34)
        dual = clone(common, "dual-host")
        for host in (dual, dual / "apps/api", dual / "apps/web"):
            shutil.copytree(host / "common", host / ".claude")
        add("dual-host", dual, ok=68)

        backend = single("single-backend-pom", "backend", "pom")
        frontend = single("single-frontend-views", "frontend", "views")
        add("single-backend-pom", backend, ok=31)
        add("single-frontend-views", frontend, ok=16)
        for marker in ("gradle", "java", "domain"):
            add("single-backend-" + marker, single("single-backend-" + marker, "backend", marker), ok=31)
        add("single-frontend-package", single("single-frontend-package", "frontend", "package"), ok=16)
        nested = clone(common, "nested-backend")
        safe_remove(nested / "apps/api/pom.xml")
        write(nested / "apps/api/server/pom.xml", "<project />\n")
        add("nested-backend", nested, ok=34)

        for area, relative, original in (
            ("backend", "apps/api/common/skills/reviewer", common),
            ("frontend", "apps/web/common/skills/reviewer", common),
            ("single-backend", "common/skills/reviewer", backend),
            ("single-frontend", "common/skills/reviewer", frontend)):
            target = clone(original, "missing-" + area + "-reviewer")
            safe_remove(target / relative)
            add("missing-" + area + "-reviewer", target, expected="nonzero", required="缺必备审查技能")

        flat = root("flat-no-markers")
        copy_skills("backend", flat / "common/skills")
        copy_skills("frontend", flat / "common/skills")
        add("flat-no-markers", flat, expected="nonzero", required="来源歧义")
        mixed = clone(flat, "flat-dual-markers")
        write(mixed / "pom.xml", "<project />\n")
        (mixed / "src/views").mkdir(parents=True)
        add("flat-dual-markers", mixed, expected="nonzero", note="Both direct stack markers; previous flat reproduction.")
        contaminated = clone(backend, "single-backend-contaminated")
        copy_skills("frontend", contaminated / "common/skills")
        add("single-backend-contaminated", contaminated, expected="nonzero",
            note="Known script limitation: opposite reviewer is classified as an ordinary local difference.")

        drift = clone(common, "flow-drift")
        mutate(drift / "common/skills/iteration-planner/SKILL.md", lambda text: text + "\nValidation fixture drift\n")
        add("flow-drift-strict", drift, expected="nonzero", required="流程 skill 与基线")
        add("flow-drift-default", drift, ok=33, strict=False, required="流程 skill 与基线")
        add("show-diff", drift, expected="nonzero", extra=["--show-diff"], required="Validation fixture drift")
        override = clone(common, "declared-override")
        mutate(override / "common/skills/iteration-planner/SKILL.md",
               lambda text: text.replace("# 持续迭代", "> 本文件 = framework 基线 + 项目专有项回注；差异仅为末尾一处 📌 fixture。\n\n# 持续迭代", 1) + "\n📌 fixture：测试样例的显式覆写。\n")
        add("declared-override", override, ok=33, required="项目覆写")
        implicit = clone(common, "drift-intrinsic-marker")
        mutate(implicit / "common/skills/project-onboarding/SKILL.md", lambda text: text + "\nUnmarked fixture drift\n")
        add("drift-intrinsic-marker", implicit, expected="nonzero",
            note="The source already contains pin emojis; appended difference has no project override declaration.")

        custom = clone(common, "unknown-project-skill")
        write(custom / "common/skills/fixture-custom/SKILL.md", "---\nname: fixture-custom\ndescription: A project-specific validation fixture.\n---\n")
        add("unknown-project-skill", custom, ok=34, required="项目专有，跳过")
        custom_only = root("custom-only-backend")
        write(custom_only / "apps/api/pom.xml", "<project />\n")
        write(custom_only / "apps/api/common/skills/fixture-custom/SKILL.md", "---\nname: fixture-custom\ndescription: Project-specific fixture.\n---\n")
        add("custom-only-backend", custom_only, ok=13)

        missing_file = clone(common, "missing-skill-file")
        safe_remove(missing_file / "apps/api/common/skills/cache/SKILL.md")
        add("missing-skill-file", missing_file, expected="nonzero", required="项目内缺 SKILL.md")
        for field, replacement, expected in (
            ("mismatch-name", lambda text: text.replace("name: cache", "name: wrong-name", 1), "nonzero"),
            ("missing-name", lambda text: re.sub(r"^name:.*\n", "", text, count=1, flags=re.M), "nonzero"),
            ("missing-description", lambda text: re.sub(r"^description:.*\n", "", text, count=1, flags=re.M), "nonzero")):
            target = clone(common, field)
            mutate(target / "apps/api/common/skills/cache/SKILL.md", replacement)
            add(field, target, expected=expected)
        missing_flow = clone(common, "missing-root-flow")
        safe_remove(missing_flow / "common/skills/dev-session")
        add("missing-root-flow", missing_flow, expected="nonzero", required="root 缺流程 skill")
        dual_missing = clone(dual, "dual-missing-root-flow")
        safe_remove(dual_missing / "common/skills/dev-session")
        add("dual-missing-root-flow", dual_missing, expected="nonzero",
            note="AGENTS common layout is incomplete even though the Claude copy is present.")

        excluded = clone(dual, "excluded-copies")
        for relative in (".scratch", ".claude/worktrees", ".worktree", ".bak-fixture", "node_modules", ".git"):
            (excluded / relative / "reference/common/skills/broken-skill").mkdir(parents=True)
        add("excluded-copies", excluded, ok=68)
        relocated = clone(common, "迁移后的项目 with spaces")
        add("relocated-target", relocated, ok=34)
        entry = relocated / "AGENTS.md"
        refs = re.findall(r"\]\(([^)]+)\)", entry.read_text(encoding="utf-8"))
        static["relocated_entry"] = {"links": len(refs), "all_relative": all(not Path(x).is_absolute() for x in refs),
                                     "all_exist": all((entry.parent / x).is_file() for x in refs)}
        spaced_source = work / "baseline with spaces"
        shutil.copytree(baseline, spaced_source)
        add("baseline-path-spaces", common, ok=34, fw=spaced_source)
        add("baseline-path-spaces-default", common, ok=34, script=spaced_source / "scripts/verify-baseline.sh", omit_fw=True)
        add("missing-framework-path", common, expected="nonzero", fw=work / "missing-baseline")
        empty = work / "empty-project"
        empty.mkdir()
        add("no-skills", empty, expected="nonzero")
        add("invalid-target", work / "does-not-exist", expected=2)
        add("unknown-option", common, expected=2, extra=["--invalid-option"])

        def run(case):
            command = [str(args.bash), str(case["script"]), str(case["target"])]
            if not case["omit_fw"]:
                command.append(str(case["fw"]))
            if case["strict"]:
                command.append("--strict")
            command.extend(case["extra"])
            started = time.monotonic()
            try:
                process = subprocess.run(command, cwd=baseline, capture_output=True,
                                         encoding="utf-8", errors="replace", timeout=240)
                log = process.stdout + process.stderr
                code = process.returncode
            except subprocess.TimeoutExpired as error:
                code, log = None, "TIMEOUT: " + str(error)
            passed = (code not in (None, 0)) if case["expected"] == "nonzero" else code == case["expected"]
            match = re.search(r"✓ 一致 (\d+).*?ℹ 项目专有差异 (\d+).*?📌 项目覆写 (\d+).*?Δ 流程漂移\(需确认\) (\d+).*?✗ 结构错误 (\d+)", log)
            counts = dict(zip(("consistent", "specific", "override", "drift", "errors"), map(int, match.groups()))) if match else None
            if case["ok"] is not None:
                passed = passed and counts is not None and counts["consistent"] == case["ok"]
            if case["required"]:
                passed = passed and case["required"] in log
            result = {"id": case["id"], "expected_exit": case["expected"], "actual_exit": code,
                      "expected_consistent": case["ok"], "matches_expectation": bool(passed),
                      "counts": counts, "duration_seconds": round(time.monotonic() - started, 2),
                      "note": case["note"], "command": command, "output": log}
            return result

        print(json.dumps({"stage": "fixtures_ready", "cases": len(cases), "revision": revision,
                          "static_skill_count": static["skill_count"]}, ensure_ascii=False), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run, case) for case in cases]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                print(json.dumps({key: result[key] for key in ("id", "actual_exit", "matches_expectation", "counts")}, ensure_ascii=False), flush=True)
        order = {case["id"]: i for i, case in enumerate(cases)}
        results.sort(key=lambda result: order[result["id"]])
        after = {p.relative_to(source).as_posix(): digest(p) for p in inspected}
        payload = {"revision": revision, "source_unchanged": before == after, "static": static,
                   "cases": results, "total": len(results),
                   "matched": sum(result["matches_expectation"] for result in results),
                   "mismatched": sum(not result["matches_expectation"] for result in results)}
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"result_file": str(output), "total": payload["total"], "matched": payload["matched"],
                          "mismatched": payload["mismatched"], "source_unchanged": payload["source_unchanged"]}, ensure_ascii=False), flush=True)
    finally:
        resolved = work.resolve()
        if resolved.parent != source.parent or not resolved.name.startswith(".skill-full-validation-"):
            raise RuntimeError("Refusing cleanup of unexpected path: " + str(resolved))
        shutil.rmtree(resolved)
        print("Temporary full-validation fixtures removed.", flush=True)


if __name__ == "__main__":
    main()
