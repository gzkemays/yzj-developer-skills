---
name: project-onboarding
description: "将 YZJ 团队技能库接入或同步到用户指定项目的 Codex 加载目录，生成 AGENTS.md、.agents/skills 和文档骨架；支持新项目初始化及保留专有规范的合并。"
---

# Codex 项目引入与同步

## 识别来源与目标

1. 定位源技能库：同时存在 `.agents/catalog.json`、`templates/AGENTS.md.template` 和 `scripts/verify-codex-skills.py`。安装后的技能不一定在源库内，先查目标 AGENTS.md 记录的来源，不要从技能位置猜源库。不能确定才问用户。
2. 获取目标路径，读取现有 AGENTS.md、技能、团队记忆与 Git 状态。用户未给路径且上下文不能确定时先问，不覆盖已有文件来“初始化”。
3. 用可用文件搜索工具定位各 Git 根。后端标志为 Maven/Gradle、`src/main/java` 或 `domain` + `integration`；前端为 Vue 依赖或 `src/views`。读取构建文件确认栈，提取实际路径、构建命令、设计 token、契约与租户约定，不将示例强加到异栈项目。

## 选择技能与加载位置

- 源目录是 `.agents/skills/`，分类见 `.agents/catalog.json` 的 `area`。复制整个技能目录，包含 `references/`、`scripts/` 等资源，不只拷入口。
- 项目根 `.agents/skills/` 放通用技能，同栈项目加对应 backend/frontend 技能。两端审查名称分别是 `backend-reviewer`、`frontend-reviewer`。
- `yzj-dev-workflow` 和 `api-contract-checker` 虽列在 general 组，也仅用于同栈项目。`project-onboarding`、`yzj-skill-creator` 是可选维护技能。弃用的 `framework-usage` 不安装。
- 单 Git 仓或 monorepo 可统一放根目录；按模块隔离时将栈技能放模块 `.agents/skills/`，从根进行跨端开发时显式读取模块技能。
- 多个独立 Git 仓不能依赖共同父目录跨 Git 边界加载。在会单独打开的每个仓内放必要的流程/规范入口和 AGENTS.md，写清共享文档的实际位置。Worktree 同样逐仓验证。
- 不复制个人 settings、凭据或原平台 CLI 评测器，不自动修改用户全局配置。

## 新项目

1. 用 `templates/AGENTS.md.template` 生成 AGENTS.md，填写来源、基线、布局、构建命令、共享文档根及实际采用技能，删除不适用项。
2. 复制 `templates/.agents/rules/`，填写契约模板。AGENTS.md 明确引用规则；`.agents/rules/` 是普通文档目录，不自动扫描。
3. 从 `templates/.document/` 补齐 plan、design、adr、memory、capability；已有共享文档体系则沿用，不创建第二套台账。
4. 复制所选技能与资源，验证各实际启动目录能发现必需技能。

## 既有项目合并

- 先确认可恢复方式，逐文件对比 Codex 基线，不盲目覆盖项目副本；不移动或删除原平台目录。
- 无专有内容的旧流程可更新。reviewer 保留漏检史、鉴权注解、命名、设计 token 和额外检查；项目独有技能保留。
- 必要覆写在文件头列差异，正文标 `📌 项目名`、理由和依据。`references/` 中的覆写同样保留，不能更新入口后丢失正文。
- AGENTS.md 和契约规则合并项目约束，文档骨架只补缺失文件。不因接入技能而改变 Git 操作授权或业务数据。

## 验证与交接

在源库运行（python 指当前可用的 Python 3.10+ 解释器）：

```text
python scripts/verify-codex-skills.py <目标项目根> --strict --show-diff
```

核对已选技能、目录/name、完整资源、常驻指令及引用、未填占位符。`📌` 仅表示需复核，不能自动视作合格；`--strict` 要求已知基线文件一致。

从目标项目启动新会话，检查技能列表，用“今天做什么”、真实开发及审查请求验证路由。只做文件校验时只报告结构与基线通过，不声称自动触发已实测；未出现更新时重启会话再检查。

交接列出实际位置、源基线、已选技术栈、保留的差异与未验证项。接入授权不包含 commit/push。
