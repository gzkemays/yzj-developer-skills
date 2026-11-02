#!/usr/bin/env python3
"""Regression cases for project-local discovery boundaries and shared entries."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("check-skill-discovery.py")
SPEC = importlib.util.spec_from_file_location("skill_discovery", SCRIPT)
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="skill-discovery-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "项目 with spaces"
        self.root.mkdir()

    def skill(self, scope, name, host="codex", *, content=None):
        path = scope / discovery.LAYOUTS[host] / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content or f"---\nname: {name}\ndescription: Run the {name} workflow.\n---\n\nComplete instructions.\n", encoding="utf-8")
        return path

    def full(self, scope=None, host="codex"):
        for name in discovery.REQUIRED:
            self.skill(scope or self.root, name, host)

    def refs(self, scope, host="codex"):
        for name in discovery.REQUIRED:
            self.ref(scope, name, host)

    def ref(self, scope, name, host="codex", *, target=None, link=True, metadata=True):
        target = target or self.root / discovery.LAYOUTS[host] / "skills" / name / "SKILL.md"
        directory = scope / discovery.LAYOUTS[host] / "skills" / name
        ref = Path(os.path.relpath(target, directory)).as_posix()
        field = f"metadata:\n  framework_ref: {ref}\n" if metadata else ""
        description = discovery.frontmatter(target.read_text(encoding="utf-8"))[0].get("description", f"Run {name}.") if target.is_file() else f"Run {name}."
        body = f"先完整读取[共享正文]({ref})，再读取正文路由的资源。" if link else "没有共享链接。"
        return self.skill(scope, name, host, content=f"---\nname: {name}\ndescription: {json.dumps(description)}\n{field}---\n\n{body}\n")

    def repo(self, relative="service"):
        scope = self.root / relative
        (scope / ".git").mkdir(parents=True)
        return scope

    def check(self, hosts=None, cwds=()):
        return discovery.Audit(self.root).run(hosts, list(cwds))

    def assert_error(self, result, text):
        self.assertFalse(result["passed"])
        self.assertTrue(any(text in message for message in result["errors"]), result["errors"])

    def test_common_only_is_not_native(self):
        self.full(host="generic")
        result = self.check(["codex", "claude"])
        self.assert_error(result, "不属于原生技能安装")
        self.assertTrue(all(len(row["missing"]) == len(discovery.REQUIRED) for row in result["matrix"]))

    def test_common_only_default_is_explicitly_manual(self):
        self.full(host="generic")
        result = self.check()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["hosts"], ["generic"])
        self.assertEqual(result["matrix"][0]["mode"], "manual")
        self.assertFalse(result["runtime_discovery_tested"])
        self.assertTrue(result["warnings"])

    def test_expected_host_cannot_be_inferred_away(self):
        self.full()
        result = self.check(["codex", "claude"])
        self.assert_error(result, "[claude]: 缺少")
        self.assertEqual(len(result["matrix"]), 2)

    def test_native_dual_host_passes(self):
        self.full()
        self.full(host="claude")
        result = self.check(["codex", "claude"])
        self.assertTrue(result["passed"], result["errors"])

    def test_independent_git_boundary_does_not_load_parent_skills(self):
        self.full()
        child = self.repo()
        self.skill(child, "service-specific")
        result = self.check(["codex"])
        self.assert_error(result, "缺少可发现")
        row = next(row for row in result["matrix"] if row["cwd"] == str(child))
        self.assertEqual(row["boundary"], str(child))
        self.assertEqual(row["search_paths"], [str(child / ".agents/skills")])

    def test_full_shared_entries_cross_independent_git_boundaries(self):
        child = self.repo()
        for host in ("codex", "claude"):
            self.full(host=host)
            self.refs(child, host)
        result = self.check(["codex", "claude"])
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(len(result["valid_refs"]), 2 * len(discovery.REQUIRED))

    def test_ref_missing_body_link_is_rejected(self):
        self.full()
        child = self.repo()
        self.refs(child)
        self.ref(child, "dev-session", link=False)
        self.assert_error(self.check(["codex"]), "正文缺少")

    def test_ref_description_drift_is_rejected(self):
        self.full()
        child = self.repo()
        self.refs(child)
        entry = child / ".agents/skills/dev-session/SKILL.md"
        text = entry.read_text(encoding="utf-8").replace('description: "Run the dev-session workflow."', 'description: "Unrelated task"')
        entry.write_text(text, encoding="utf-8")
        self.assert_error(self.check(["codex"]), "description 与完整正文不一致")

    def test_ref_missing_target_is_rejected(self):
        self.full()
        child = self.repo()
        self.refs(child)
        (self.root / ".agents/skills/dev-session/SKILL.md").unlink()
        self.assert_error(self.check(["codex"]), "目标无效")

    def test_ref_cannot_cross_hosts(self):
        self.full()
        self.full(host="claude")
        child = self.repo()
        self.refs(child)
        self.ref(child, "dev-session", target=self.root / ".claude/skills/dev-session/SKILL.md")
        self.assert_error(self.check(["codex"]), "共同根同宿主同名")

    def test_ref_cannot_use_an_alias(self):
        self.full()
        child = self.repo()
        self.refs(child)
        self.ref(child, "old-session", target=self.root / ".agents/skills/dev-session/SKILL.md")
        self.assert_error(self.check(["codex"]), "共同根同宿主同名")

    def test_ref_chain_is_rejected(self):
        self.full()
        child = self.repo()
        self.refs(child)
        self.ref(self.root, "dev-session", target=self.root / ".agents/skills/git-commit/SKILL.md")
        self.assert_error(self.check(["codex"]), "引用链或环")

    def test_ref_self_cycle_is_rejected(self):
        self.full()
        self.ref(self.root, "dev-session")
        self.assert_error(self.check(["codex"]), "不能指向自己")

    def test_ref_cannot_leave_old_resources_beside_entry(self):
        self.full()
        child = self.repo()
        self.refs(child)
        stale = child / ".agents/skills/dev-session/references/old.md"
        stale.parent.mkdir()
        stale.write_text("Stale instruction.", encoding="utf-8")
        self.assert_error(self.check(["codex"]), "只允许 SKILL.md")

    def test_ref_outside_project_is_rejected(self):
        self.full()
        child = self.repo()
        self.refs(child)
        self.ref(child, "dev-session", target=Path(self.tmp.name) / "external/SKILL.md")
        self.assert_error(self.check(["codex"]), "共同根同宿主同名")

    def test_monorepo_subfolder_inherits_parent_without_ref(self):
        (self.root / ".git").mkdir()
        self.full()
        child = self.root / "packages/service"
        self.skill(child, "service-specific")
        result = self.check(["codex"])
        self.assertTrue(result["passed"], result["errors"])
        row = next(row for row in result["matrix"] if row["cwd"] == str(child))
        self.assertEqual(row["boundary"], str(self.root))
        self.assertEqual(len(row["skills"]), len(discovery.REQUIRED) + 1)

    def test_monorepo_duplicate_name_is_rejected(self):
        (self.root / ".git").mkdir()
        self.full()
        child = self.root / "packages/service"
        self.skill(child, "dev-session")
        self.assert_error(self.check(["codex"]), "技能重名或插件双装 dev-session")

    def test_codex_native_plus_plugin_is_double_install(self):
        self.full()
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = true\n', encoding="utf-8")
        self.assert_error(self.check(["codex"]), "插件双装")

    def test_claude_native_plus_plugin_is_double_install(self):
        self.full(host="claude")
        config = self.root / ".claude/settings.json"
        config.write_text(json.dumps({"enabledPlugins": {"yzj-flow@yzj-skills": True}}), encoding="utf-8")
        self.assert_error(self.check(["claude"]), "插件双装")

    def test_plugins_have_declaration_status_not_runtime_status(self):
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = true\n', encoding="utf-8")
        result = self.check(["codex"])
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["matrix"][0]["plugins"][0]["installed"], "not-tested")

    def test_false_plugin_does_not_supply_skills(self):
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = false\n', encoding="utf-8")
        self.assert_error(self.check(["codex"]), "缺少可发现")

    def test_codex_ancestor_plugin_and_local_skills_are_double_install(self):
        (self.root / ".git").mkdir()
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = true\n', encoding="utf-8")
        child = self.root / "packages/service"
        self.full(child)
        self.assert_error(self.check(["codex"]), "插件双装")

    def test_codex_nearer_false_overrides_ancestor_plugin(self):
        (self.root / ".git").mkdir()
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = true\n', encoding="utf-8")
        child = self.root / "packages/service"
        self.full(child)
        override = child / ".codex/config.toml"
        override.parent.mkdir()
        override.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = false\n', encoding="utf-8")
        result = self.check(["codex"])
        self.assertTrue(result["passed"], result["errors"])
        row = next(row for row in result["matrix"] if row["cwd"] == str(child))
        self.assertFalse(row["plugins"])

    def test_existing_config_identifies_expected_host_even_if_disabled(self):
        self.full(host="generic")
        config = self.root / ".codex/config.toml"
        config.parent.mkdir()
        config.write_text('[plugins."yzj-flow@yzj-skills"]\nenabled = false\n', encoding="utf-8")
        result = self.check()
        self.assertEqual(result["hosts"], ["codex"])
        self.assert_error(result, "缺少可发现")

    def test_worktree_is_pruned_but_explicit_cwd_checks_it(self):
        self.full()
        worktree = self.root / ".worktree/change/service"
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: ../../../../service/.git/worktrees/service\n", encoding="utf-8")
        result = self.check(["codex"])
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(len(result["matrix"]), 1)
        explicit = self.check(["codex"], [worktree])
        self.assert_error(explicit, "缺少可发现")
        self.assertEqual(explicit["matrix"][0]["boundary"], str(worktree))

    def test_worktree_copied_relative_refs_do_not_fall_back_to_main(self):
        self.full()
        main = self.repo()
        self.refs(main)
        worktree = self.root / ".worktree/change/service"
        worktree.mkdir(parents=True)
        (worktree / ".git").write_text("gitdir: ../../../../service/.git/worktrees/service\n", encoding="utf-8")
        for name in discovery.REQUIRED:
            original = main / ".agents/skills" / name / "SKILL.md"
            self.skill(worktree, name, content=original.read_text(encoding="utf-8"))
        self.assert_error(self.check(["codex"], [worktree]), "共同根同宿主同名")

    def test_prunes_backups_and_avoids_external_symlink(self):
        self.full()
        self.skill(self.root / ".bak-test/nested", "broken", content="not a skill")
        self.skill(self.root / "reports/fixture", "broken", content="not a skill")
        result = self.check(["codex"])
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(len(result["matrix"]), 1)

    def test_symlinked_skill_cannot_escape_project(self):
        self.full()
        external = Path(self.tmp.name) / "external"
        external.mkdir()
        (external / "SKILL.md").write_text("not a skill", encoding="utf-8")
        link = self.root / ".agents/skills/external"
        try:
            link.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("This host cannot create directory symlinks.")
        self.assert_error(self.check(["codex"]), "逃逸项目根")

    def test_manifest_bom_crlf_and_description_block(self):
        self.full()
        self.skill(self.root, "dev-session", content='\ufeff---\r\nname: "dev-session"\r\ndescription: >\r\n  Run development\r\n  workflows.\r\n---\r\nInstructions.\r\n')
        self.assertTrue(self.check(["codex"])["passed"])

    def test_manifest_name_mismatch_is_an_error(self):
        self.full()
        self.skill(self.root, "alias", content="---\nname: dev-session\ndescription: Duplicate\n---\nBody\n")
        self.assert_error(self.check(["codex"]), "与目录名")

    def test_json_and_exit_code_are_usable_by_caller(self):
        self.full(host="generic")
        evidence = Path(self.tmp.name) / "evidence.json"
        proc = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), str(self.root), "--hosts", "codex", "--json", str(evidence)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        data = json.loads(evidence.read_text(encoding="utf-8"))
        self.assertEqual(data["kind"], "static")
        self.assertFalse(data["runtime_discovery_tested"])
        self.assertFalse(data["passed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
