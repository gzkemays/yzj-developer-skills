# {项目名} 开发计划总览

> 最后更新: {yyyy-MM-dd}
> 实时进度看 [STATUS.md](STATUS.md) 需求台账；本文件管阶段与模块的全景。

## 目标

{交付目标，如：交付 MVP (V1.0)，覆盖 XX 核心功能}

## 阶段规划

| 阶段 | 内容 | 预估周期 | 状态 |
|------|------|----------|------|
| **P0 - {阶段名}** | {模块列表} | {N 周} | `未开始` |
| **P1 - {阶段名}** | {模块列表} | {N 周} | `未开始` |

> 状态：`未开始` / `进行中` / `已完成`（规则见 `progress-tracker` skill）

## 模块文档索引

### P0 - {阶段名}
- [01-{module}.md](01-{module}.md) - {模块说明}

## 协作模式

- **后端**: {如 AI 编码，开发者 Review + 架构决策}
- **前端**: {如 AI 全权开发与架构调整}
- **流程**: Claude Code + dev-session 12 阶段 + 本计划文档驱动迭代

## 关键约束

1. {如 后端遵循 YZJ 四层架构（domain / integration / interfaces / support）}
2. {如 前端技术栈 Vue 3 + Naive UI + Pinia}
3. {如 多租户：共享 DB + organization_id 行级隔离}
4. {如 API 规范：RESTful，统一响应体 CommonResult}
