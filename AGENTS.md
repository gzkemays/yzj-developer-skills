# YZJ 团队共享技能库 · 通用入口

本仓库是团队研发流程与前后端规范的**唯一内容源**：所有 AI 宿主（Claude Code、Codex、其他模型 CLI）读同一份技能内容，不存在按宿主生成的适配层。当前基线见 `README.md`「当前基线」。

> 本文件及本仓库所有入口中的路径均为**相对本文件所在目录**的相对路径；不要写绝对路径（同一父目录常并存多个项目，绝对路径在迁移 / 改名后失效）。

## 目录与加载

- `common/skills/<name>/SKILL.md` — 通用流程技能（研发生命周期、对齐、进度、记忆、提交等），目标项目**根目录**层使用；个别根级路由入口为同栈专用（如 `yzj-dev-workflow` 仅后端同栈项目安装）。
- `backend/<name>/SKILL.md` — 后端规范技能（YZJ 四层 + MyBatis-Flex 同栈适用）。
- `frontend/<name>/SKILL.md` — 前端规范技能（Vue 3 + Naive UI 同栈适用）。
- `templates/` — 目标项目入口与文档骨架模板（`CLAUDE.md.template`、`AGENTS.md.template`、`common/rules/`、`.document/`）。
- `scripts/verify-baseline.sh` — 校验目标项目技能与本仓库基线对齐（兼容 `.claude/skills` 与 `common/skills` 两种目标布局）。

加载方式：按各 SKILL.md frontmatter 的 `description` 路由；**使用前读取 SKILL.md 全文**，入口引用 `references/` 或其他技能时继续读完再执行。不要把所有规范一次性塞入上下文。

## 技能路由

- 开发流程：`dev-session`（12 阶段总入口）→ `pre-dev-alignment`（编码前对齐与文档门禁）；session 开局（"今天做什么 / 接着做"）用 `iteration-planner`；按需加载 `progress-tracker` / `team-memory` / `capability-registry` / `similar-issue-sweep` / `dev-output`。
- 后端业务：`yzj-dev-workflow` 及其引用的 backend 子技能；审查：`backend/reviewer`。前端：`frontend/view-conventions`、`frontend/i18n-automation`；审查：`frontend/reviewer`。同栈才适用，以技能描述为准。
- 跨端契约：`api-contract-checker`——两端接口变更时按技术设计文档「契约」章节逐条校验（dev-session P4 引用）。
- 接入目标项目：`common/skills/project-onboarding`；创建 / 修改团队技能：`common/skills/skill-creator`（其评测脚本依赖 Claude Code CLI，其他宿主仅参考方法论）。
- Git 提交：`common/skills/git-commit`——未获授权不执行 commit / push。
- 维护本技能库、只读咨询和小型文档调整无需套用业务项目的完整 12 阶段流程；本仓库不是业务项目，`templates/.document/` 是骨架，不当成真实台账。

## 宿主映射（技能正文的中性表述 ↔ 各宿主实现）

| 技能正文中的表述 | Claude Code | 其他宿主 |
|------------------|-------------|----------|
| 进入计划评审 | `EnterPlanMode` / `ExitPlanMode` | 在当前会话提交计划 / 文档，等待明确批准 |
| 个人 memory | `~/.claude/projects/` | 用户已配置并授权的位置；未配置则跳过，不自建宿主私有目录 |
| 浏览器 / 预览能力 | 内置浏览器与 preview 工具 | 会话实际可用的浏览器 / 预览工具；没有则 build + 类型检查并列出未验证项 |
| 技能目录（目标项目内） | 各级 `.claude/skills/`（自动发现） | 各级 `common/skills/`（由 AGENTS.md 声明，显式读取） |
| Read / Grep / Glob / Edit | 同名内置工具 | 当前会话真实可用的读取 / 搜索 / 列文件 / 编辑能力；命令行搜索优先 `rg` |

## 执行门禁（任何宿主不得跳过）

1. 执行技能前**读完其 SKILL.md 全文**；禁止仅凭 description 行事。
2. dev-session 的 P4 审查、P8 开发者确认、P9 台账更新、编码前文档评审等硬门禁，不得以"改动小 / 很有把握"跳过。
3. 审查 / 自测结论必须附文件级依据；grep 零命中**不等于**语义检查通过。
4. 未实际运行命令、未读过文件，不得声称已验证 / 已完成；未覆盖项如实列出。
5. 计划评审、文档确认、Git 提交 / 推送授权须用户明确批准；沉默或普通知会不扩大权限。

## 维护约定

- **单一源**：修改规范直接改 `common/skills/`、`backend/`、`frontend/` 下的源文件，无同步脚本、无生成物。宿主差异一律写成行内映射「（Claude Code：X；其他宿主：Y）」，不复制出宿主专属副本。
- 每个技能 `name` 与目录名一致；frontmatter 以 Agent Skills 开放标准字段为主（`name`/`description` 等）。宿主扩展字段（如 `disable-model-invocation`、`user-invocable`）仅对支持的宿主生效——凡影响触发行为的，必须同时在 description / 正文写明等效文字约束（如"仅在用户显式要求时执行"），让不识别该字段的宿主也按文字执行。
- 修改流程类 skill（dev-session / reviewer / progress-tracker）需团队过目；重大流程变更更新 `README.md`「当前基线」日期。
- 不把个人 settings、凭据写入仓库；适配宿主不意味着新增业务规则或假装工具存在。

## 验证命令

```text
bash scripts/verify-baseline.sh <目标项目根> [--show-diff] [--strict]
```

文件校验通过不等于自动触发已实测：从目标项目启动新会话，用"今天做什么"、真实开发与审查请求验证路由。
