# 恢复卡（plan/context/）

> 一个需求一张 `{yyyy-MM-dd}_{stage}_{slug}.md`（与 STATUS 条目、output 报告同名；**slug = 分支 business 段 = worktree 目录名**，否则脚本无法自动定位）。由负责该需求的 AI 会话在 dev-session P1 建立、每次阶段迁移时更新（与台账同步，当下写、不等收尾）；P12 完成后删除，**搁置保留**（恢复时据此续作），**取消时删除**。
> 用途：上下文被压缩后，会话按本卡 + STATUS 对应行重新定位，只恢复自己这个需求的内容，不与并行需求混淆。
> 存放：只在项目根 `.document/plan/context/`，worktree 会话同样写根目录（`git-commit` 8.4）。各会话只写自己的卡。
> **不记录任何授权状态**（提交 / 主干直提 / 计划批准）——授权单次有效，压缩后一律重新确认。

## 模板（复制后删除本节以上内容）

```markdown
# 恢复卡：{yyyy-MM-dd}_{stage}_{slug}

> 阶段迁移时更新；压缩恢复时首先读本卡。不记录授权。

- 需求：{一句话}
- 变更分级：ARCH / NORMAL
- 当前阶段：P{N}
- 下一步：{具体动作，如"按用例文档执行 TC-1～TC-3 自测"}
- 已过门禁：对齐✅(design/{yyyy-MM-dd}_{slug}.md)　P4✅(design/{yyyy-MM-dd}_{slug}-review.md)　P6✅　P8✅
- 工作位置：分支 {feat|opt|fix}/{yyyy.MM.dd}-{business}；{主工作区 | .worktree/{business}/{repo}}；涉及仓 {backend-repo} / {frontend-repo}

## 需重读（压缩后按此清单重读；写技能名 + 章节，路径由 restore_context.py 按本项目安装位置解析）
- dev-session（当前阶段章节）
- pre-dev-alignment（P3 对齐阶段）
- backend/reviewer 全文（P4 阶段）
- git-commit（P11 阶段）

## 关键决策与开发者纠正（一行一条）
- {yyyy-MM-dd} {结论}（已沉淀：developer/memory/{文件}.md）

## 未完成 / 待确认
- {项}
```
