#!/usr/bin/env python3
"""Exercise the real Bash verifier together with its discovery preflight.

Uses small temporary framework/project fixtures, never an installed project.
Set YZJ_TEST_BASH to a Bash executable; on Windows use Git Bash. Python 3.11+
is required, and the current interpreter is added to the subprocess PATH only.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
REQUIRED = (
    "dev-session", "pre-dev-alignment", "progress-tracker", "iteration-planner",
    "team-memory", "capability-registry", "similar-issue-sweep", "dev-output", "git-commit",
)


class BaselineDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.version_info < (3, 11):
            raise RuntimeError("These integration tests require Python 3.11+.")
        cls.bash = os.environ.get("YZJ_TEST_BASH") or shutil.which("bash")
        if not cls.bash:
            raise RuntimeError("Bash is required; set YZJ_TEST_BASH to its executable.")
        probe = subprocess.run([cls.bash, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        if probe.returncode or "bash" not in probe.stdout.lower():
            raise RuntimeError("Cannot run Bash: " + probe.stderr)
        cls.payload = {name: (SCRIPTS / name).read_bytes() for name in ("verify-baseline.sh", "check-skill-discovery.py")}
        if b"\r\n" in cls.payload["verify-baseline.sh"]:
            raise RuntimeError("verify-baseline.sh must use LF before it is executed by Bash.")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="baseline-discovery-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.framework = self.base / "framework source"
        self.project = self.base / "native skills 项目"
        self.project.mkdir()
        (self.project / ".document").mkdir()
        for name, data in self.payload.items():
            path = self.framework / "scripts" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for name in REQUIRED:
            self.write_skill(self.framework / "common/skills" / name, name)
        for area in ("backend", "frontend"):
            self.write_skill(self.framework / area / "reviewer", "reviewer")
        resource = self.framework / "common/skills/dev-session/references/process.md"
        resource.parent.mkdir()
        resource.write_text("Keep the complete development process.\n", encoding="utf-8", newline="\n")

    @staticmethod
    def write_skill(directory, name, *, description=None, body="Baseline instructions."):
        directory.mkdir(parents=True, exist_ok=True)
        description = description or f"Run the {name} workflow."
        path = directory / "SKILL.md"
        path.write_text(f"---\nname: {name}\ndescription: {json.dumps(description)}\n---\n\n# {name}\n\n{body}\n", encoding="utf-8", newline="\n")
        return path

    def install(self, scope=None, layout=".agents"):
        destination = (scope or self.project) / layout / "skills"
        shutil.copytree(self.framework / "common/skills", destination)
        return destination

    def shared_entries(self, layout=".agents"):
        child = self.project / "app checkout"
        (child / ".git").mkdir(parents=True, exist_ok=True)
        for name in REQUIRED:
            path = child / layout / "skills" / name / "SKILL.md"
            target = self.project / layout / "skills" / name / "SKILL.md"
            relative = Path(os.path.relpath(target, path.parent)).as_posix()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"---\nname: {name}\ndescription: {json.dumps(f'Run the {name} workflow.')}\n"
                f"metadata:\n  framework_ref: {relative}\n---\n\n"
                f"执行前完整读取[共享正文]({relative})，并按共享正文的目录解析资源。\n",
                encoding="utf-8", newline="\n",
            )
        return child

    def verify(self, *options):
        env = os.environ.copy()
        env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        result = subprocess.run(
            [self.bash, str(self.framework / "scripts/verify-baseline.sh"), str(self.project), str(self.framework), "--strict", *options],
            cwd=self.base, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
        )
        return result.returncode, result.stdout + result.stderr

    def test_native_codex_install_passes(self):
        self.install()
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 0, output)
        self.assertIn("一致 9", output)
        self.assertIn("结构错误 0", output)

    def test_common_only_cannot_pass_as_codex(self):
        self.install(layout="common")
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 1, output)
        self.assertIn("不属于原生技能安装", output)
        self.assertNotIn("──────── 小结", output)

    def test_native_codex_does_not_hide_missing_expected_claude(self):
        self.install()
        status, output = self.verify("--hosts", "codex,claude")
        self.assertEqual(status, 1, output)
        self.assertIn("[claude]: 缺少可发现", output)

    def test_shared_refs_in_spaced_windows_paths_are_not_body_drift(self):
        self.install()
        self.shared_entries()
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 0, output)
        self.assertIn("共享入口 9", output)
        self.assertIn("一致 9", output)
        self.assertIn("流程漂移(需确认) 0", output)
        self.assertNotIn("项目内缺失（主文件路由", output)

    def test_shared_refs_do_not_skip_complete_root_body_comparison(self):
        self.install()
        self.shared_entries()
        root_skill = self.project / ".agents/skills/dev-session/SKILL.md"
        root_skill.write_text(root_skill.read_text(encoding="utf-8") + "\nChanged root process.\n", encoding="utf-8", newline="\n")
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 1, output)
        self.assertIn("共享入口 9", output)
        self.assertIn("Δ  dev-session", output)

    def test_shared_refs_do_not_skip_complete_root_resource_comparison(self):
        self.install()
        self.shared_entries()
        (self.project / ".agents/skills/dev-session/references/process.md").unlink()
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 1, output)
        self.assertIn("共享入口 9", output)
        self.assertIn("dev-session/references/process.md  项目内缺失", output)

    def test_framework_ref_in_description_is_not_a_valid_ref(self):
        self.install()
        path = self.project / ".agents/skills/dev-session/SKILL.md"
        path.write_text(
            "---\nname: dev-session\ndescription: >\n  Run the development workflow.\n"
            "  framework_ref: ../../../../missing/SKILL.md\n---\n\nChanged process.\n",
            encoding="utf-8", newline="\n",
        )
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 1, output)
        self.assertIn("Δ  dev-session", output)
        self.assertIn("共享入口 0", output)

    def test_uninspected_claude_ref_is_not_claimed_valid_in_codex_run(self):
        self.install()
        self.install(layout=".claude")
        path = self.project / ".claude/skills/dev-session/SKILL.md"
        path.write_text(
            '---\nname: dev-session\ndescription: "Run the dev-session workflow."\n'
            "metadata:\n  framework_ref: ../../../../missing/SKILL.md\n---\n\n"
            "执行前读取[不存在的正文](../../../../missing/SKILL.md)。\n",
            encoding="utf-8", newline="\n",
        )
        status, output = self.verify("--hosts=codex")
        self.assertEqual(status, 1, output)
        self.assertIn("Δ  dev-session", output)
        self.assertIn("共享入口 0", output)
        self.assertNotIn("原生共享入口（目标已通过", output)

    def test_generic_root_requirement_is_not_bypassed_by_plugin_default(self):
        self.install(layout="common")
        shutil.rmtree(self.project / "common/skills/git-commit")
        child = self.project / "manual checkout"
        child.mkdir()
        self.install(child, layout="common")
        # Preflight intentionally covers the complete child only. The Bash
        # verifier must still enforce its own project-root baseline contract.
        status, output = self.verify("--hosts=generic", "--cwd", str(child))
        self.assertEqual(status, 1, output)
        self.assertIn("root 缺流程 skill: common/skills/git-commit", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
