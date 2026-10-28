"""Compare pin-marker handling under C and C.UTF-8 without changing sources."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

parser = argparse.ArgumentParser()
parser.add_argument("--bash", type=Path, required=True)
args = parser.parse_args()
source = Path(__file__).resolve().parents[2]
work = source.parent / (".skill-locale-validation-" + uuid.uuid4().hex)
work.mkdir()
results = []
try:
    for mode in ("declared-override", "unmarked-drift"):
        target = work / mode
        shutil.copytree(source / "common/skills", target / "common/skills")
        (target / ".document").mkdir()
        if mode == "declared-override":
            path = target / "common/skills/iteration-planner/SKILL.md"
            text = path.read_text(encoding="utf-8")
            text = text.replace("# 持续迭代", "> 本文件 = framework 基线 + 项目专有项回注；差异仅为末尾一处 📌 fixture。\n\n# 持续迭代", 1)
            text += "\n📌 fixture：用于比较 locale 的显式覆写。\n"
            expected = 0
        else:
            path = target / "common/skills/project-onboarding/SKILL.md"
            text = path.read_text(encoding="utf-8") + "\nUnmarked fixture drift\n"
            expected = 1
        path.write_text(text, encoding="utf-8")
        for locale in ("C", "C.UTF-8"):
            environment = dict(os.environ, LC_ALL=locale, LANG=locale)
            command = [str(args.bash), str(source / "scripts/verify-baseline.sh"),
                       str(target), str(source), "--strict"]
            process = subprocess.run(command, cwd=source, env=environment,
                                     capture_output=True, encoding="utf-8", errors="replace", timeout=120)
            result = {"mode": mode, "locale": locale, "expected_exit": expected,
                      "actual_exit": process.returncode, "matches_expectation": process.returncode == expected,
                      "pin_count_in_file": text.count("📌"), "command": command,
                      "output": process.stdout + process.stderr}
            results.append(result)
            print(json.dumps({key: result[key] for key in ("mode", "locale", "expected_exit", "actual_exit", "matches_expectation")}, ensure_ascii=False), flush=True)
    output = Path(__file__).with_name("locale-results.json")
    output.write_text(json.dumps({"cases": results, "total": len(results),
                                  "matched": sum(result["matches_expectation"] for result in results)},
                                 ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
finally:
    resolved = work.resolve()
    if resolved.parent != source.parent or not resolved.name.startswith(".skill-locale-validation-"):
        raise RuntimeError("Unexpected cleanup path")
    shutil.rmtree(resolved)
    print("Temporary locale-validation fixtures removed.", flush=True)
