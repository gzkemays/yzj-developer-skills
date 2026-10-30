# git-commit · 机械兜底 commit_guard.py

> 门禁：脚本只拦"能用正则说清"的部分（署名尾注 / 模型名 / 进度词 / 主干判定），概述是否有信息量、是否三分法仍按第三章（主文件路由表「编写 message」）与第七章（「提交前自检」）人工自检；脚本故障放行，不等于规则放行。

**机械兜底 `scripts/commit_guard.py`**（规则不靠记忆；对**已执行 `git config core.hooksPath .githooks` 的成员**，人和 AI 的提交同样生效；脚本故障时放行不阻塞）：

| 模式 | 用途 | 接法 |
|------|------|------|
| `commit-msg <file>` | git 原生 `commit-msg` hook：命中 AI 记号 / 进度词 → 退出 1 拦截并说明。编辑器提交时忽略 git 生成的 `#` 注释块；`-m` / `-F` 提交不忽略（git 不会剥掉这些行） | 项目提交 `.githooks/commit-msg`（模板 `templates/.githooks/commit-msg`），各 git 仓 `git config core.hooksPath .githooks`——**本地配置，每位成员 clone 后执行一次**（写在入口文件「开始工作时」）；`--no-verify` 可绕过，属开发者自觉 |
| `check-text <file>` | 对 MR / PR 标题、描述等文本做同一检查（不忽略 `#` 行） | 创建 MR 前对 UTF-8 文件跑一次 |
| `precheck` | 打印当前分支判定（开发分支 / 主干 / 其他 / 无法判定）与 2.5 授权提醒 | 任何宿主提交前运行，输出贴进回执 |
| `pretooluse` | Claude Code `PreToolUse`（Bash）hook：`git commit` 带 AI 记号 → 拒绝；在主干 → 弹窗确认（单次授权的机械形态）；分支既非主干也不合命名规则 → 弹窗确认；开发分支放行。命令解析不了时退化为全文扫描，宁可误拒不静默放行 | 插件安装自带（`yzj-flow` `hooks/hooks.json`）；复制安装把 `templates/hooks/claude-settings-hooks.json` 合并进 `.claude/settings.json` |

- **主干名**：默认 `master` / `main` / `develop` / `release/*`；项目主干另有名字时在该仓 `git config --add yzj.trunk {name}`（本地配置，随 `core.hooksPath` 一起执行）或设 `YZJ_TRUNK_BRANCHES=a,b`，脚本据此判定。
- **拦截范围**：`Co-Authored-By` 尾注（**不区分 AI 或人**——铁律 3 不加任何协作者尾注）、`Generated with` / `Generated-with`、`Claude` / `Claude Code` / `Anthropic` / `Opus` / `Sonnet` / `Haiku`（首字母大写；路径与文件名如 `.claude/`、`claude-settings-hooks.json` 不算）、🤖、句尾的"由 AI 生成 / AI 辅助"、`FIXED` / `Step N` / `Phase N` / `Px 已过`。
- **`pretooluse` 已知盲区**（git 原生 hook 兜底）：`-F -` / heredoc 经 stdin 传入的消息、`--trailer`、`--amend --no-edit` 与 `-C <commit>` 复用旧消息——这些在 commit-msg hook 层仍会被检查。

> 机械检查只覆盖"能用正则说清"的部分（署名尾注、模型名、进度词、主干判定）；概述是否有信息量、是否三分法仍按第三、七章人工自检。
