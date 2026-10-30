# YZJ 团队共享技能库 · 通用入口

本仓库是团队研发流程与前后端规范的**唯一内容源**：所有 AI 宿主（Claude Code、Codex、其他模型 CLI）读同一份技能内容，不存在按宿主生成的适配层。当前基线见 `README.md`「当前基线」。

> 本文件及本仓库所有入口中的路径均为**相对本文件所在目录**的相对路径；不要写绝对路径（同一父目录常并存多个项目，绝对路径在迁移 / 改名后失效）。

## 目录与加载

- `common/skills/<name>/SKILL.md` — 通用流程技能（研发生命周期、对齐、进度、记忆、提交等），目标项目**根目录**层使用；个别根级路由入口为同栈专用（如 `yzj-dev-workflow` 仅后端同栈项目安装）。
- `backend/<name>/SKILL.md` — 后端规范技能（YZJ 四层 + MyBatis-Flex 同栈适用）。
- `frontend/<name>/SKILL.md` — 前端规范技能（Vue 3 + Naive UI 同栈适用）。
- `templates/` — 目标项目入口与文档骨架模板（`CLAUDE.md.template`、`AGENTS.md.template`、`common/rules/`（协作原则 / 契约速查 / **红线** `red-lines.md`）、`.document/`（含 `plan/context/` 恢复卡））。
- `scripts/verify-baseline.sh` — 校验目标项目技能与本仓库基线对齐（兼容 `.claude/skills`、`common/skills` 与 marketplace 插件三种安装）。
- `scripts/check-skill-layout.sh` — 校验本仓库技能布局：主文件对 `references/` `templates/` 的引用存在、无孤立子文件、带约束卡的技能其子文件带门禁行（阻断）；体积超阈值只告警。拆分技能后、发布前运行。
- 机械兜底脚本随技能源分发：`common/skills/git-commit/scripts/commit_guard.py`（commit 信息 AI 记号 / 进度词检查、主干判定；git 原生 `commit-msg` hook 模板在 `templates/.githooks/`）、`common/skills/dev-session/scripts/restore_context.py`（压缩后恢复）。Claude Code 宿主 hook：插件自带 `common/hooks/hooks.json`；复制安装用 `templates/hooks/claude-settings-hooks.json`。其他宿主的 hook 机制核实后再接。
- marketplace 清单（元数据，非技能副本）：`.claude-plugin/marketplace.json`（Claude Code）、`.agents/plugins/marketplace.json`（Codex）；插件根 `common/`、`backend/`、`frontend/` 各有 `.claude-plugin/plugin.json` + `plugin.json`，对应插件 `yzj-flow` / `yzj-backend` / `yzj-frontend`。`scripts/check-plugin-manifests.sh` 校验清单与技能源、README 基线一致。

加载方式：按各 SKILL.md frontmatter 的 `description` 路由；**使用前读取 SKILL.md 主文件全文**，再按主文件路由读取当前阶段 / 场景对应的 `references/` 子文件与关联技能。不要把所有规范一次性塞入上下文，也不为省事一次读完所有子文件。

## 技能路由

- 开发流程：`dev-session`（12 阶段总入口）→ `pre-dev-alignment`（编码前对齐与文档门禁）；session 开局（"今天做什么 / 接着做"）用 `iteration-planner`；按需加载 `progress-tracker` / `team-memory` / `capability-registry` / `similar-issue-sweep` / `dev-output`。
- 后端业务：`yzj-dev-workflow` 及其引用的 backend 子技能；审查：`backend/reviewer`。前端：`frontend/view-conventions`、`frontend/i18n-automation`；审查：`frontend/reviewer`。同栈才适用，以技能描述为准。
- 跨端契约：`api-contract-checker`——两端接口变更时按技术设计文档「契约」章节逐条校验（dev-session P4 引用）。
- 接入目标项目：`common/skills/project-onboarding`——先只读 dry-run 预演，开发者确认动作清单后才写入目标项目；创建 / 修改团队技能：`common/skills/skill-creator`（其评测脚本依赖 Claude Code CLI，其他宿主仅参考方法论）。
- Git 提交：`common/skills/git-commit`——未获授权不执行 commit / push。
- 知识与规范收尾：`common/skills/neat-freak`——用户点名"洁癖 / neat"，或表达明确的知识收尾意图（"把文档和记忆整理一下"、"收尾把文档同步掉"、"docs 和代码对不上了"）时触发，把文档 / 规则 / 获准维护的记忆 / 工作区残留对齐到代码与运行态；纯编码调试任务和无项目知识上下文的"整理"不触发。dev-session P12 在成果报告后按轻量路径自动引用，形成流程闭环。
- 维护本技能库、只读咨询和小型文档调整无需套用业务项目的完整 12 阶段流程；本仓库不是业务项目，`templates/.document/` 是骨架，不当成真实台账。

## 宿主映射（技能正文的中性表述 ↔ 各宿主实现）

| 技能正文中的表述 | Claude Code | 其他宿主 |
|------------------|-------------|----------|
| 进入计划评审 | `EnterPlanMode` / `ExitPlanMode` | 在当前会话提交计划 / 文档，等待明确批准 |
| 个人 memory | `~/.claude/projects/` | 用户已配置并授权的位置；未配置则跳过，不自建宿主私有目录 |
| 浏览器 / 预览能力 | 内置浏览器与 preview 工具 | 会话实际可用的浏览器 / 预览工具；没有则 build + 类型检查并列出未验证项 |
| 技能目录（目标项目内） | 各级 `.claude/skills/`（自动发现） | 各级 `common/skills/`（由 AGENTS.md 声明，显式读取） |
| marketplace 插件安装 | `.claude/settings.json` 的 `enabledPlugins`（`yzj-*@yzj-skills`） | Codex：`.codex/config.toml` 的 `[plugins."yzj-*@yzj-skills"]`；无 marketplace 的宿主走复制安装 |
| Read / Grep / Glob / Edit | 同名内置工具 | 当前会话真实可用的读取 / 搜索 / 列文件 / 编辑能力；命令行搜索优先 `rg` |

## 执行门禁（任何宿主不得跳过）

1. 执行技能前**读完其 SKILL.md 主文件全文**，再读主文件路由指向当前阶段 / 场景的子文件；禁止仅凭 description 行事。
   上下文被压缩后，按 `templates/common/rules/red-lines.md`「压缩恢复协议」先恢复定位，进入硬门禁前按其指针重读原章节。
2. dev-session 的 P4 审查、P8 开发者确认、P9 台账更新、编码前文档评审等硬门禁，不得以"改动小 / 很有把握"跳过。
3. 审查 / 自测结论必须附文件级依据；grep 零命中**不等于**语义检查通过。
4. 未实际运行命令、未读过文件，不得声称已验证 / 已完成；未覆盖项如实列出。
5. 计划评审、文档确认、Git 提交 / 推送授权须用户明确批准；沉默或普通知会不扩大权限。

## 维护约定

- **单一源**：修改规范直接改 `common/skills/`、`backend/`、`frontend/` 下的源文件，无同步脚本、无生成物。宿主差异一律写成行内映射「（Claude Code：X；其他宿主：Y）」，不复制出宿主专属副本。
- 每个技能 `name` 与目录名一致；frontmatter 以 Agent Skills 开放标准字段为主（`name`/`description` 等）。宿主扩展字段（如 `disable-model-invocation`、`user-invocable`）仅对支持的宿主生效——凡影响触发行为的，必须同时在 description / 正文写明等效文字约束（如"仅在用户显式要求时执行"），让不识别该字段的宿主也按文字执行。
- 修改流程类 skill（dev-session / reviewer / progress-tracker）需团队过目；重大流程变更更新 `README.md`「当前基线」日期。
- **大技能按主文件引导式组织**：`SKILL.md` 主文件放约束卡、路由表与进度判定，细则按阶段 / 场景放 `references/`，文档骨架放 `templates/`，每个 `references/` 子文件开头一行自己的门禁；`references/` 之间不互相引用，只由主文件路由（`templates/` 与其所属阶段子文件可互指门禁行）；搬入子文件的正文里"见下文 / 主文件第 N 章"一类指针须改成目标文件路径。`reviewer` 例外不拆（P4 全文加载）。`bash scripts/check-skill-layout.sh` 校验。
- 插件可带 `hooks/hooks.json`（插件根下，与 `skills/` 平级，不是技能）：命令里只引用插件内脚本（`${CLAUDE_PLUGIN_ROOT}/skills/...`），python 用"逐个试跑 python3 / python / py"的写法（Windows 的 `python3` 可能是商店占位符），全部 fail-open。`check-plugin-manifests.sh` 校验 JSON 与脚本路径。
- 插件清单只是元数据，不复制技能：插件根就是技能源目录。发布新基线时六份 `plugin.json` 的 `version` 同步为基线日期去前导零（`2026-10-29` → `2026.10.29`），跑 `bash scripts/check-plugin-manifests.sh` 与 `claude plugin validate .`；不改 version 的提交不会推送给已安装成员。插件技能目录下只放技能（每个子目录须有 SKILL.md）。
- 不把个人 settings、凭据写入仓库；适配宿主不意味着新增业务规则或假装工具存在。

## 验证命令

```text
bash scripts/verify-baseline.sh <目标项目根> [--show-diff] [--strict]
bash scripts/check-plugin-manifests.sh
bash scripts/check-skill-layout.sh
```

文件校验通过不等于自动触发已实测：从目标项目启动新会话，用"今天做什么"、真实开发与审查请求验证路由。
