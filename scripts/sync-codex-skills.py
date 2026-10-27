"""Build the Codex adapter from shared sources; --check never writes files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
CUSTOM = {"project-onboarding", "skill-creator", "framework-usage"}
DESCRIPTIONS = {
    "dev-session": "编排项目功能开发与迭代：需求分级、沉淀复用、实现、自审、自测、开发者验收和进度维护。只读咨询和技能库维护不强制启动完整研发流程。",
    "pre-dev-alignment": "在功能开发、重构或存在方案选择的修复前澄清需求，按 L1/L2/L3 产出计划、技术设计及接口契约，处理必要的评审门禁。明显的小修改直接执行。",
    "git-commit": "在用户授权提交或推送时执行团队 Git 分支、提交信息、安全暂存和 Worktree 约定；仅询问提交规范不授权执行 Git 写操作。",
    "api-contract-checker": "检查 YZJ 后端与 Vue 前端的接口契约，包括返回类型、ID、分页、字段、表单校验和敏感字段；涉及两端接口变更时使用。",
    "yzj-dev-workflow": "在 YZJ Framework、Spring Boot 3、MyBatis-Flex 项目中开发业务代码，按 domain、integration、interfaces、support 四层路由到对应规范。",
    "backend-reviewer": "审查 YZJ 后端 Java 和 proto 变更，执行完整七步流程、逐文件维度检查、漏检史与安全金融测试专项；适用于后端自审或用户要求审查。",
    "frontend-reviewer": "审查 Vue 3、Naive UI 前端变更，执行七步流程以及接口契约、国际化、设计 token、交互检查；适用于前端自审或用户要求审查。",
}
WORKTREE = """### 8.2 Worktree 的目录与加载入口

优先使用当前宿主提供的托管 Worktree 能力，并遵守其创建和回收规则。手动管理时可采用 `{project-root}/.worktree/{business}/{repo}`，前后端分仓保持同名任务分支。

- Worktree 是独立检出，其 Git 根是技能和项目指令发现的重要边界。不能因为物理路径位于外层项目内，就假定外层 `AGENTS.md` 和 `.agents/skills/` 自动加载。
- 开始前检查树内 `AGENTS.md` 和 `.agents/skills/`。已纳入版本控制的入口会随检出出现；缺失时在授权范围内补齐必要入口，或明确读取共享规范的绝对路径，并验证引用可访问。
- 多仓根与各独立 Git 仓库分别检查加载入口；流程 skill 如需在子仓新会话使用，也要在该仓可发现的位置部署。
- 仅手动布局时将 `.worktree/` 加入所在仓 `.gitignore`，避免整棵树被当成未跟踪文件。
- 构建、测试、校验一律以本次 Worktree 的仓目录为 cwd，跨仓引用解析到同一任务的另一棵树。

"""


def adapt(text: str, area: str, name: str) -> str:
    """Translate host-specific instructions without changing domain examples."""
    replacements = {
        "CLAUDE.md": "AGENTS.md",
        ".claude/skills": ".agents/skills",
        ".claude/rules": ".agents/rules",
        "~/.claude/projects/": "用户明确配置的个人记忆位置",
        "framework `skills/backend/`": "framework `skills/.agents/skills/` 中对应后端 skill",
        "framework `skills/frontend/`": "framework `skills/.agents/skills/` 中对应前端 skill",
        "`skill-creator`": "`yzj-skill-creator`",
        "backend `reviewer`": "`backend-reviewer`",
        "frontend `reviewer`": "`frontend-reviewer`",
        "`frontend/reviewer`": "`frontend-reviewer`",
        "`backend/reviewer`": "`backend-reviewer`",
        "进入 Plan 模式（`EnterPlanMode`）": "先写出可审阅的技术方案",
        "调用 `ExitPlanMode`": "通过当前会话提交文档并在需要时等待确认",
        "`ExitPlanMode`": "明确的文档评审确认",
        "进入 Plan 模式": "在当前会话提交计划或文档供评审",
        "Plan 模式中 approve": "对当前计划明确批准",
        "推荐使用 Claude Preview MCP（`preview_start` / `preview_snapshot` / `preview_console_logs` / `preview_network` 等）；项目无 preview 工具时退化为 `build + 类型检查 + 手动验证指引`。": "先检查当前会话可用的浏览器或预览能力，按其工具说明验证渲染、交互、控制台与网络；没有可用工具时执行 `build + 类型检查`，并列出尚未验证的交互与手动验证指引。",
        "推荐用 Claude Preview MCP 做渲染/交互/网络验证（dev-session P5 两轮机制）": "使用当前会话可用的浏览器或预览工具做渲染/交互/网络验证；工具不可用时报告未验证项（dev-session P5 两轮机制）",
        "Claude Code": "Codex",
        "Claude": "Codex",
        "`claude`": "`codex`",
        "`Opus`": "`模型名`",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    if area in ("backend", "frontend") or name == "yzj-dev-workflow":
        reviewer = "frontend-reviewer" if area == "frontend" else "backend-reviewer"
        text = re.sub(r"(?<![\w-])reviewer(?![\w-])", reviewer, text)
    if name == "pre-dev-alignment":
        text = text.replace("| 代码审查 | `reviewer` |", "| 代码审查 | `backend-reviewer` |", 1)
        text = text.replace("| 代码审查 | `reviewer` |", "| 代码审查 | `frontend-reviewer` |", 1)
    if name == "iteration-planner":
        text = text.replace("logging / reviewer）", "logging / backend-reviewer）")
        text = text.replace("i18n-automation / reviewer）", "i18n-automation / frontend-reviewer）")
    if name == "dev-session":
        text = text.replace("4. 读取个人 memory（`用户明确配置的个人记忆位置` 下）", "4. 仅在用户已配置并允许读取时加载个人记忆；未配置则跳过，不假定固定记忆目录")
        text = text.replace("NORMAL 级在 P6 知会确认中合并完成，不再二次询问。", "NORMAL 级可合并评审确认，但普通知会确认不自动授权 commit 或 push；按用户已明确授权的操作范围执行，不重复索要相同授权。")
    if name == "team-memory":
        text = text.replace("个人偏好请存入 `用户明确配置的个人记忆位置` 个人 memory。", "个人偏好仅存入用户已配置并授权的位置；未配置时不创建宿主私有目录。")
    if name == "git-commit" and "### 8.2 " in text:
        start, end = text.index("### 8.2 "), text.index("### 8.3 ")
        text = text[:start] + WORKTREE + text[end:]
        text = re.sub(r"- \*\*个人 memory 不跨树\*\*：.*", "- **不依赖个人记忆跨树传递上下文**：团队需求、纠正与踩坑写入项目约定的共享 `.document/developer/memory/`，位置由项目 AGENTS.md 明确记录。", text)
        text = text.replace("**这是唯一无需额外授权即可原地提交的情形**", "**仍须已获本次提交与推送授权；分支合规不构成授权**")
    if name == "i18n-automation":
        text = text.replace("优先执行以下脚本（位于本 Skill 的 `scripts/`）：", "优先执行以下脚本（位于本 Skill 的 `scripts/`）。将脚本路径解析为本技能目录下的绝对路径，在目标前端仓 cwd 运行；`python` 指当前会话可用的 Python 解释器：")
    return text


def generated_files() -> dict[Path, bytes]:
    """Return deterministic output, including resources used by the skills."""
    files: dict[Path, bytes] = {}
    catalog = {}
    for area, directory in (("general", ".claude/skills"), ("backend", "backend"), ("frontend", "frontend")):
        for source in sorted((ROOT / directory).iterdir()):
            manifest = source / "SKILL.md"
            if not manifest.is_file() or source.name in CUSTOM:
                continue
            name = area + "-reviewer" if source.name == "reviewer" else source.name
            _, front, body = manifest.read_text(encoding="utf-8").split("---", 2)
            description = front.split("description:", 1)[1].split("\nuser-invocable:", 1)[0].strip()
            if description.startswith(">"):
                description = " ".join(line.strip() for line in description[1:].strip().splitlines())
            elif description.startswith('"'):
                description = json.loads(description)
            description = adapt(DESCRIPTIONS.get(name, description), area, name)
            body = adapt(body.strip(), area, name)
            folder = Path(".agents/skills") / name
            header = f"---\nname: {name}\ndescription: {json.dumps(description, ensure_ascii=False)}\n---\n\n"
            if len(body) > 6500:
                files[folder / "references/rules.md"] = (body + "\n").encode("utf-8")
                body = f"# {name}\n\n执行时先完整读取 [规范与流程](references/rules.md)，再按任务读取其中引用的技能和项目文档。审查技能须读取全文及漏检史，不只依据入口给出结论。\n\n项目路径、构建命令、契约及授权以当前项目 `AGENTS.md` 和用户指令为准。"
            files[folder / "SKILL.md"] = (header + body + "\n").encode("utf-8")
            for resource in sorted(source.rglob("*")):
                relative = resource.relative_to(source)
                if not resource.is_file() or relative.parts[0] not in ("scripts", "evals", "assets", "references") or "__pycache__" in relative.parts or resource.suffix == ".pyc":
                    continue
                data = resource.read_bytes()
                if name == "i18n-automation" and resource.name == "run_i18n_audit.py":
                    data = resource.read_text(encoding="utf-8").replace('cmd = ["python",', 'cmd = [sys.executable,').encode("utf-8")
                if resource.suffix == ".py":
                    data = data.rstrip(b"\r\n") + b"\n"
                files[folder / relative] = data
            catalog[name] = {"area": area, "source": manifest.relative_to(ROOT).as_posix()}
    for name, source in (("project-onboarding", "project-onboarding"), ("yzj-skill-creator", "skill-creator")):
        catalog[name] = {"area": "general", "source": f".claude/skills/{source}/SKILL.md"}
    files[Path(".agents/catalog.json")] = (json.dumps({"source_baseline": "2026-10-24", "adapted_on": "2026-10-26", "skills": dict(sorted(catalog.items()))}, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Report stale generated files without writing")
    args = parser.parse_args()
    changed = 0
    for relative, data in generated_files().items():
        target = ROOT / relative
        # Text line endings do not affect the generated baseline.
        current = target.read_bytes().replace(b"\r\n", b"\n") if target.is_file() else None
        if current == data.replace(b"\r\n", b"\n"):
            continue
        changed += 1
        if args.check:
            print(f"STALE {relative.as_posix()}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(f"{'Stale' if args.check else 'Updated'} files: {changed}")
    return int(args.check and changed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
