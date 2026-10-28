"""Exercise the new lightweight metadata reader and post-frontmatter window.

This checks the stated lightweight contract, not general YAML conformance.
Only isolated fixtures and edge-results.json are written.
"""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bash", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[2]
    output = Path(__file__).with_name("edge-results.json")
    manifest = json.loads(Path(__file__).with_name("source-manifest.json").read_text(encoding="utf-8"))
    before = {p: hashlib.sha256((source / p).read_bytes()).hexdigest()
              for p in manifest["source_hashes"]}
    if before != manifest["source_hashes"]:
        raise RuntimeError("Source changed since the captured working-tree manifest")
    work = source.parent / (".skill-edge-validation-" + uuid.uuid4().hex)
    work.mkdir()
    cases, results = [], []

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def mutate(path, operation):
        write(path, operation(path.read_text(encoding="utf-8")))

    def safe_remove(path):
        resolved = path.resolve()
        if work.resolve() not in resolved.parents:
            raise RuntimeError("Refusing removal outside fixture tree")
        shutil.rmtree(resolved) if resolved.is_dir() else resolved.unlink()

    def declare(text, body_line=2, long_header=False):
        header, body = text.split("\n---", 1)
        if long_header:
            header += "\n  Additional fixture routing context." * 25
        return (header + "\n---\n" + "\n" * (body_line - 1)
                + "> 本文件 = framework 基线 + 项目专有项回注；差异仅为末尾一处 📌 fixture。\n"
                + body.lstrip("\n") + "\n📌 fixture：验证覆写声明的所在位置。\n")

    try:
        baseline = work / "baseline"
        for area in ("common", "backend", "frontend", "scripts"):
            shutil.copytree(source / area, baseline / area)
        control = work / "control-template"
        shutil.copytree(baseline / "common/skills", control / "common/skills")
        for name in ("cache", "reviewer"):
            shutil.copytree(baseline / "backend" / name, control / "apps/api/common/skills" / name)
        (control / ".document").mkdir()
        write(control / "apps/api/pom.xml", "<project />\n")

        def add(name, expected, note, fw=None):
            target = work / name
            shutil.copytree(control, target)
            cases.append({"id": name, "target": target, "fw": fw or baseline,
                          "expected": expected, "note": note})
            return target

        cache = Path("apps/api/common/skills/cache/SKILL.md")
        flow = Path("common/skills/iteration-planner/SKILL.md")
        add("control", 0, "13 common skills plus cache and backend reviewer.")

        target = add("unclosed-frontmatter", "nonzero", "Opening delimiter is present; closing delimiter is absent even at EOF.")
        write(target / cache, "---\nname: cache\ndescription: Fixture description without closing boundary.\n")

        target = add("whitespace-only-quoted-description", "nonzero", "A double-quoted description contains whitespace only.")
        mutate(target / cache, lambda text: re.sub(r"^description:.*$", 'description: "   "', text, count=1, flags=re.M))

        target = add("quoted-name-trailing-spaces", 0, "Supported double-quoted name followed by ordinary trailing whitespace.")
        mutate(target / cache, lambda text: text.replace("name: cache", 'name: "cache"   ', 1))

        target = add("bom-metadata", 0, "The lightweight reader explicitly attempts to support a UTF-8 BOM.")
        mutate(target / cache, lambda text: "\ufeff" + text)

        target = add("bom-declared-override", 0, "UTF-8 BOM plus the same valid override declaration as the normal case.")
        mutate(target / flow, lambda text: "\ufeff" + declare(text))

        target = add("declaration-post-fm-line-20", 0, "Declaration at exactly the new inclusive upper bound.")
        mutate(target / flow, lambda text: declare(text, body_line=20))

        target = add("declaration-post-fm-line-21", "nonzero", "Declaration just beyond the documented new window.")
        mutate(target / flow, lambda text: declare(text, body_line=21))

        target = add("long-frontmatter-valid-declaration", 0, "Long frontmatter must not consume the separate 20-line body window.")
        mutate(target / flow, lambda text: declare(text, long_header=True))

        for label, relative in (("common", "common/skills/dev-session/SKILL.md"),
                                ("backend", "backend/reviewer/SKILL.md"),
                                ("frontend", "frontend/reviewer/SKILL.md")):
            missing = work / ("baseline-without-" + label)
            shutil.copytree(baseline, missing)
            safe_remove(missing / relative)
            add("missing-sentinel-" + label, 2, "Only the selected sentinel is missing from the baseline.", fw=missing)

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
            if case["expected"] == 0:
                matched = matched and counts is not None and counts["consistent"] == (15 if case["id"] == "control" else 14)
            return {"id": case["id"], "expected_exit": case["expected"],
                    "actual_exit": process.returncode, "matches_expectation": matched,
                    "counts": counts, "note": case["note"], "command": command, "output": log}

        print(json.dumps({"stage": "fixtures_ready", "cases": len(cases)}), flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(run, case) for case in cases]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                print(json.dumps({k: result[k] for k in ("id", "actual_exit", "matches_expectation", "counts")},
                                 ensure_ascii=False), flush=True)
        order = {case["id"]: i for i, case in enumerate(cases)}
        results.sort(key=lambda result: order[result["id"]])
        after = {p: hashlib.sha256((source / p).read_bytes()).hexdigest() for p in before}
        payload = {"base_commit": manifest["base_commit"], "working_tree_modified": True,
                   "tested_script_sha256": before["scripts/verify-baseline.sh"],
                   "source_unchanged": before == after, "total": len(results),
                   "matched": sum(r["matches_expectation"] for r in results),
                   "mismatched": sum(not r["matches_expectation"] for r in results), "cases": results}
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: payload[k] for k in ("total", "matched", "mismatched", "source_unchanged")}), flush=True)
    finally:
        resolved = work.resolve()
        if resolved.parent != source.parent or not resolved.name.startswith(".skill-edge-validation-"):
            raise RuntimeError("Refusing unexpected cleanup path")
        shutil.rmtree(resolved)
        print("Temporary edge fixtures removed.", flush=True)


if __name__ == "__main__":
    main()
