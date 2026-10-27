# YZJ 团队技能库 · Codex

本仓库同时维护原有技能源与 Codex 加载目录。源基线为 2026-10-24，Codex 适配日期为 2026-10-26。

## 加载与路由

- 本文件是仓库常驻入口。先读取 [.agents/rules/collaboration.md](.agents/rules/collaboration.md)；`.agents/rules/` 是显式引用的普通文档目录，不依赖自动扫描。
- Codex 技能位于 `.agents/skills/<name>/SKILL.md`，按 description 选择；长规范位于技能自身的 `references/rules.md`，使用时必须读取。不要把所有规范一次性塞入上下文。
- 开发流程：`dev-session` → `pre-dev-alignment`，按需加载进度、记忆和能力登记技能。维护本技能库、只读咨询和小型文档调整无需套用业务项目的完整 12 阶段流程。
- 后端业务入口：`yzj-dev-workflow`；审查：`backend-reviewer`。前端规范：`view-conventions`、`i18n-automation`；审查：`frontend-reviewer`。具体技术栈适用范围以技能描述为准。
- 接入目标项目使用 `project-onboarding`；创建或修改团队技能使用 `yzj-skill-creator`，宿主内置 `skill-creator` 可用时优先复用其创作工具。
- 本仓库不是业务项目；`templates/.document/` 是文档骨架，不当成当前项目进度或真实需求。

## 维护方式

- `.claude/`、`backend/`、`frontend/` 保留为原有来源。`.agents/catalog.json` 记录 Codex 技能与源文件的对应关系。
- `scripts/sync-codex-skills.py` 生成普通技能和随附资源。修改共享规范后运行它，再检查 diff；生成物中的宿主差异应修改脚本的适配规则，不只修改生成物。
- `project-onboarding` 和 `yzj-skill-creator` 是手工维护的 Codex 专属入口，不由同步脚本覆盖。`AGENTS.md`、常驻规范、模板和 README 同样手工维护。
- Codex 技能名与目录名一致。前后端 reviewer 使用不同名称；弃用的 `framework-usage` 不安装。不要复制个人 settings、凭据或原有依赖专用 CLI 的评测脚本到新目录。
- 维持既有需求分级、审查、契约、进度和团队沉淀约定；适配宿主不意味着新增业务规则或假装工具存在。

## 验证命令

```text
python scripts/sync-codex-skills.py --check
python scripts/verify-codex-skills.py
python scripts/verify-codex-skills.py <目标项目根> --strict
```

`python` 指当前会话可用的 Python 3.10+ 解释器，不假定其一定在 PATH。脚本使用标准库。校验目录和元数据通过并不证明自动触发已实测；从本仓库目录启动新会话后再检查技能列表及典型请求。
