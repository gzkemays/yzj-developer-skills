@AGENTS.md

## Claude Code 专属补充（仅本仓库维护会话）

本仓库的技能源放在 `common/skills/`（模型无关目录），**不在 `.claude/skills/` 下，Claude Code 不会自动发现**。维护会话按下表路由，命中后**读取对应 SKILL.md 全文再执行**：

| 用户请求 | 读取并执行 |
|----------|-----------|
| "把这套规范 / skills 引入到 XX 项目"、"新项目接入"、"旧项目融入" | `common/skills/project-onboarding/SKILL.md` |
| "创建 / 修改 / 评测技能" | `common/skills/skill-creator/SKILL.md` |
| "提交吧 / commit / push" | `common/skills/git-commit/SKILL.md` |
| "洁癖 / neat / 把文档和记忆同步到现状"（知识与规范收尾） | `common/skills/neat-freak/SKILL.md` |
| 修改某个流程 / 规范技能本身 | 该技能的 SKILL.md 全文（`common/skills/` 或 `backend/` / `frontend/`） |

- 目标项目里 Claude Code 仍使用 `.claude/skills/` + `.claude/rules/` + CLAUDE.md（宿主硬约束），由 project-onboarding 从本仓库 `common/` 复制安装；**本仓库内不维护 `.claude/skills/` 副本**，以免双源漂移。
- 本文件与 AGENTS.md 中的引用均为相对路径；新增引用时不要写绝对路径。
