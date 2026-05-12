---
name: framework-usage
description: "[DEPRECATED] 此 skill 已弃用，功能已拆分至独立的组件级 skill。请直接使用：common（通用工具/枚举/异常/SessionContext）、cache（缓存与分布式锁）、mybatis（数据库查询构建）、security（安全认证）。"
---

> **⚠️ DEPRECATED**：此 skill 已弃用，**不要再依赖本文档**。

## 请改用以下 skill

| 历史内容 | 新 skill |
|----------|----------|
| 通用工具类、CommonResult、CommonPage、ApiException、SessionContext、枚举 | `common` |
| 缓存注解（@CacheRead/@CachePut/@CacheEvict）、分布式锁（@DistributedLock） | `cache` |
| IQueryChain 链式查询、CommonQuery、分页排序、@Encryption | `mybatis` |
| JWT / OAuth、SecurityToken、IJwtTokenGenerate、DynamicSecurityAuth | `security` |

> 如果 Agent 命中了此 skill，请立即切换到对应的新 skill 完成任务。本文件保留仅为兼容旧引用，**未来版本将整体删除**。
