"""Check boundaries introduced or touched by 7cded4d in disposable fixtures.

Only boundary-results.json is retained. The verifier and skill source stay unchanged.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    work = source.parent / (".skill-boundary-validation-" + uuid.uuid4().hex)
    inspected = sorted([*source.glob("common/skills/*/SKILL.md"),
                        *source.glob("backend/*/SKILL.md"),
                        *source.glob("frontend/*/SKILL.md"),
                        *source.glob("templates/common/rules/*.md"),
                        source / "AGENTS.md", source / "scripts/verify-baseline.sh"])

    def hashes():
        return {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in inspected}

    before = hashes()
    revision = subprocess.run(["git", "-c", "safe.directory=" + source.as_posix(),
                               "-C", str(source), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    cases = []
    results = []
    work.mkdir()

    def remove(path):
        resolved = path.resolve()
        if work.resolve() not in resolved.parents:
            raise RuntimeError("Refusing deletion outside fixture tree")
        shutil.rmtree(resolved) if resolved.is_dir() else resolved.unlink()

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def mutate(path, operation):
        write(path, operation(path.read_text(encoding="utf-8")))

    try:
        baseline = work / "baseline"
        for area in ("common", "backend", "frontend", "templates", "scripts"):
            shutil.copytree(source / area, baseline / area)
        control = work / "control"
        shutil.copytree(baseline / "common/skills", control / "common/skills")
        shutil.copytree(baseline / "templates/common/rules", control / "common/rules")
        shutil.copytree(baseline / "backend", control / "apps/api/common/skills")
        shutil.copytree(baseline / "frontend", control / "apps/web/common/skills")
        (control / ".document").mkdir()
        (control / "apps/web/src/views").mkdir(parents=True)
        write(control / "apps/api/pom.xml", "<project />\n")

        def add(name, expected="nonzero", note="", fw=None):
            target = work / name
            shutil.copytree(control, target)
            cases.append({"id": name, "target": target, "expected": expected,
                          "fw": fw or baseline, "note": note})
            return target

        cache = Path("apps/api/common/skills/cache/SKILL.md")
        flow = Path("common/skills/iteration-planner/SKILL.md")
        add("valid-control", 0, "Unmodified split installation.")

        for name, value in (("empty-description-null", ""),
                            ("empty-description-quoted", '""'),
                            ("empty-description-folded", ">")):
            target = add(name, note="A required description must contain nonempty text.")
            mutate(target / cache, lambda text, v=value:
                   re.sub(r"^description:.*$", "description: " + v, text, count=1, flags=re.M))

        target = add("no-frontmatter", note="Metadata-like body lines do not form YAML frontmatter.")
        mutate(target / cache, lambda text: text.replace("---\n", "", 2))

        target = add("metadata-only-in-body", note="Fields missing from frontmatter occur only in a body code example.")
        def body_fields(text):
            updated = re.sub(r"^name:.*\n", "", text, count=1, flags=re.M)
            updated = re.sub(r"^description:.*\n", "", updated, count=1, flags=re.M)
            return updated + "\n```yaml\nname: cache\ndescription: Example only, outside frontmatter.\n```\n"
        mutate(target / cache, body_fields)

        target = add("quoted-valid-name", 0, "Quoted YAML scalar still has the value cache.")
        mutate(target / cache, lambda text: text.replace("name: cache", 'name: "cache"', 1))

        empty_baseline = work / "baseline-empty-regions"
        for region in ("common/skills", "backend", "frontend"):
            (empty_baseline / region).mkdir(parents=True)
        add("empty-baseline-regions", fw=empty_baseline,
            note="All region directories exist but contain zero baseline skill files.")
        partial_baseline = work / "baseline-missing-region"
        shutil.copytree(baseline / "common", partial_baseline / "common")
        shutil.copytree(baseline / "backend", partial_baseline / "backend")
        add("missing-baseline-region", fw=partial_baseline,
            note="Frontend baseline region absent; a configuration error is expected.")

        target = add("missing-root-layout", note="Only child layouts remain; root workflows are absent.")
        remove(target / "common/skills")

        target = add("frontend-contaminated", note="Frontend skill directory also receives backend skills.")
        shutil.copytree(baseline / "backend", target / "apps/web/common/skills", dirs_exist_ok=True)

        target = add("anchor-only-in-description",
                     note="Anchor phrase is descriptive metadata, not a declaration after frontmatter.")
        mutate(target / flow, lambda text: text.replace(
            "description: >\n",
            "description: >\n  文档术语示例：本文件 = framework 基线；此处仅为描述文字。\n", 1))

        target = add("override-after-line-20", note="Declaration is outside the newly documented first-20-line boundary.")
        mutate(target / flow, lambda text: text +
               "\n> 本文件 = framework 基线 + 项目专有项回注；差异仅限本段。\n📌 fixture：测试覆写。\n")

        target = add("valid-override-header", 0, "Declared diff list immediately follows frontmatter.")
        def declared(text):
            end = text.index("\n---", 4) + len("\n---")
            return (text[:end] + "\n\n> 本文件 = framework 基线 + 项目专有项回注；差异仅限末尾一处 📌 fixture。\n"
                    + text[end:] + "\n📌 fixture：测试覆写。\n")
        mutate(target / flow, declared)

        target = add("dual-missing-claude-flow", note="Common copy cannot cover missing Claude root workflow.")
        for host in (target, target / "apps/api", target / "apps/web"):
            shutil.copytree(host / "common", host / ".claude")
        remove(target / ".claude/skills/dev-session")

        def run(case):
            command = [str(args.bash), str(baseline / "scripts/verify-baseline.sh"),
                       str(case["target"]), str(case["fw"]), "--strict"]
            process = subprocess.run(command, cwd=baseline, capture_output=True,
                                     encoding="utf-8", errors="replace", timeout=240)
            log = process.stdout + process.stderr
            matched = (process.returncode != 0 if case["expected"] == "nonzero"
                       else process.returncode == case["expected"])
            match = re.search(r"✓ 一致 (\d+).*?ℹ 项目专有差异 (\d+).*?📌 项目覆写 (\d+).*?Δ 流程漂移\(需确认\) (\d+).*?✗ 结构错误 (\d+)", log)
            counts = dict(zip(("consistent", "specific", "override", "drift", "errors"),
                              map(int, match.groups()))) if match else None
            if case["id"] in ("valid-control", "quoted-valid-name", "valid-override-header"):
                expected_count = 34 if case["id"] == "valid-control" else 33
                matched = matched and counts is not None and counts["consistent"] == expected_count
            return {"id": case["id"], "expected_exit": case["expected"],
                    "actual_exit": process.returncode, "matches_expectation": matched,
                    "counts": counts, "note": case["note"], "command": command, "output": log}

        print(json.dumps({"stage": "fixtures_ready", "cases": len(cases), "revision": revision}), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run, case) for case in cases]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                print(json.dumps({k: result[k] for k in ("id", "actual_exit", "matches_expectation", "counts")},
                                 ensure_ascii=False), flush=True)
        order = {case["id"]: i for i, case in enumerate(cases)}
        results.sort(key=lambda result: order[result["id"]])
        payload = {"revision": revision, "environment": {k: os.environ.get(k) for k in ("LANG", "LC_ALL")},
                   "source_unchanged": before == hashes(), "source_hashes": before,
                   "total": len(results), "matched": sum(r["matches_expectation"] for r in results),
                   "mismatched": sum(not r["matches_expectation"] for r in results), "cases": results}
        output = Path(__file__).with_name("boundary-results.json")
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: payload[k] for k in ("total", "matched", "mismatched", "source_unchanged")}), flush=True)
    finally:
        resolved = work.resolve()
        if resolved.parent != source.parent or not resolved.name.startswith(".skill-boundary-validation-"):
            raise RuntimeError("Refusing unexpected cleanup path")
        shutil.rmtree(resolved)
        print("Temporary boundary fixtures removed.", flush=True)


if __name__ == "__main__":
    main()
