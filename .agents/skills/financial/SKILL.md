---
name: financial
description: "YZJ 后端金融级规范。当代码涉及金额、余额、交易、支付、转账、结算、对账、账户流水、退款、优惠抵扣等资金语义，或 pre-dev-alignment 命中「支付/资金」风险关键词时使用此 skill。覆盖金额类型与运算（BigDecimal）、写操作幂等（业务唯一键 + @DistributedLock）、事务边界与异常、余额扣减一致性（行锁 / 乐观锁）、审计流水、脱敏展示；backend-reviewer 金融维度据此审查。"
---

# financial

执行时先完整读取 [规范与流程](references/rules.md)，再按任务读取其中引用的技能和项目文档。审查技能须读取全文及漏检史，不只依据入口给出结论。

项目路径、构建命令、契约及授权以当前项目 `AGENTS.md` 和用户指令为准。
