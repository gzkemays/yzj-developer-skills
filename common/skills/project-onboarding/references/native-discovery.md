# 原生发现与预演验收

> 门禁：先按宿主和启动目录完成 dry-run 加载矩阵；目录存在、内容一致、宿主发现、任务触发是不同证据，不能互相代替。

## 源码目录和安装目录

本技能库 `common/skills`、`backend`、`frontend` 是维护源。目标项目采用 Claude Code 时安装在 `.claude/skills`，采用 Codex 时安装在 `.agents/skills`（复数）；多宿主分别安装相同正文。`AGENTS.md` 是项目指令入口，不能让任意目录变成宿主自动扫描目录；`.agents/rules` 也只是它显式引用的规则位置。

官方依据（2026-11-03 核对）：[Codex 技能发现](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)、[Claude Code 技能发现](https://code.claude.com/docs/en/skills#load-skills-in-monorepos-and-subdirectories)。宿主先提供技能名称和描述，任务选择技能后才读取正文。升级宿主时重新核对边界，不依赖文档旧版本猜测。

## 每个启动位置都要说明来源

dry-run 必须列下面这张表，不能用一句“按 cwd 自动加载”替代：

| 宿主 / 版本 | 启动 cwd | Git 根 / 非 Git | 原生技能目录 | 通用正文 / 端规范来源 | 验证层级与结果 |
|---|---|---|---|---|---|
| 按实际填写 | 根、端仓、实际要使用的 Worktree 分行 | 以实际检出为准 | 实际路径 | 本地完整包 / 共享入口目标 / 已启用插件 | 静态 / 宿主清单 / 任务触发分别记录 |

- 单仓内，宿主向上扫描到 Git 根；已经能继承的同名技能不再复制到子目录。
- 前后端为独立 Git 仓时，共同父目录在发现边界之外。仅在父目录放技能，或在子仓 AGENTS 写一个路径，都不能证明技能已出现在原生清单。
- Worktree 的 Git 根、相对路径与主仓不同。主仓入口检出到 Worktree 后可能断链；要另行接入、核验该 cwd，不能把构建或任务执行切回主工作区来掩盖问题。未迁移的旧 Worktree 明确列为未接入。
- 插件模式须查本宿主本层启用状态与实际清单，避免用户级同名技能、旧别名、本地副本或插件重复被当成成功。

## 共享技能原生入口

通用正文需要集中在共同根、独立子仓又要原生发现时，可以只在子仓原生技能目录放 `SKILL.md` 入口。它复制完整正文的 `name` / `description`，并明确要求读取共同根全文；不复制 scripts / references，不改写技能规则。

示例：`{root}/{repo}/.agents/skills/dev-session/SKILL.md`：

```yaml
---
name: dev-session
description: 使用共同根完整技能的原始 description，不用此示例描述替代。
metadata:
  framework_ref: ../../../../.agents/skills/dev-session/SKILL.md
---
```

正文须包含指向该相对地址的 Markdown 链接，并要求：执行前完整读取共享 SKILL.md，再以共享技能所在目录解析其中 resources / scripts；共享目录缺失时报告缺失，不临时生成另一份规则。`.claude` 入口同理，目标也使用 `.claude`。

`framework_ref` 是本库静态审计字段，**不是宿主配置**，宿主不会替模型跟随该字段。真正的加载依赖可发现的元数据和正文读取指令。只允许指向共同根同宿主、同名完整技能，不允许链式转发、环、跨宿主或绝对路径；入口目录只含 `SKILL.md`。

共享入口没有 scripts；子仓 hooks 必须定位共同根的完整技能或采用已核验的旁置脚本，不能直接套用“本 cwd 原生技能目录下存在 scripts”的完整安装模板。路径需覆盖普通检出与实际使用的 Worktree；定位共享知识不会改变业务命令的 cwd。

原生完整包迁移到已有 `.agents` 目录时，先辨别原来的旧生成正文、转发入口与项目专有技能，逐文件比较后再替换。备份历史资源到自动发现目录之外，不让废弃别名继续参与路由。

## 验证顺序

1. 在暂存副本中保留实际结构标志，按目标仓边界建立最小 `.git` 标志；运行 `python scripts/check-skill-discovery.py {预演根} --hosts codex,claude`。未接入层、历史 common 安装、错拼 `.agent`、共享断链或重复名称须报错。
2. 运行 `bash scripts/verify-baseline.sh {目标根} --hosts=codex,claude --strict`，核验完整正文、资源、项目回注及原生共享入口。纯通用宿主手动路由才显式选 `--hosts=generic`。
3. 迁移后从每个实际启动 cwd 获取宿主技能清单；记录宿主版本、名称、路径和错误。Codex 可用当前本机 app-server 的 `skills/list`（先核对本机 schema），Claude Code 用该版本提供的技能清单。禁止用正则扫目录结果冒充宿主结果。
4. 用代表性只读任务检查模型是否选择正确技能、读取完整正文。无法执行时列“触发未实测”；不能凭静态检查或技能清单写“全自动触发通过”。

宿主无法运行、所需插件不可用或 Worktree 未迁移时，报告明确的证据缺口。用户已确认本次目录修正时直接在该范围执行；新增的范围或冲突另列，不重复索要已有授权。
