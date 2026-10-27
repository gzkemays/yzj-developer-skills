---
name: security
description: "yzj-security 安全认证使用指南 + 安全编码红线。当需要配置 JWT/OAuth 认证、使用 SecurityTokenContext 获取 Token 信息、实现 DynamicSecurityAuth 接口、配置 SecurityFilterChain、编写 UserDetailService 实现时使用此 skill；当代码涉及 auth / token / password / encrypt / key / card / pan / cvv / pin / permission / role 等安全关键词，或 backend-reviewer 走安全维度时，按第八节红线（持卡人数据、密码学、注入、越权、SSRF、安全日志、生产禁止项）与 8.8 自检清单逐条核对。"
---

# security

执行时先完整读取 [规范与流程](references/rules.md)，再按任务读取其中引用的技能和项目文档。审查技能须读取全文及漏检史，不只依据入口给出结论。

项目路径、构建命令、契约及授权以当前项目 `AGENTS.md` 和用户指令为准。
