---
name: backend-reviewer
description: "审查 YZJ 后端 Java 和 proto 变更，执行完整七步流程、逐文件维度检查、漏检史与安全金融测试专项；适用于后端自审或用户要求审查。"
---

# backend-reviewer

执行时先完整读取 [规范与流程](references/rules.md)，再按任务读取其中引用的技能和项目文档。审查技能须读取全文及漏检史，不只依据入口给出结论。

项目路径、构建命令、契约及授权以当前项目 `AGENTS.md` 和用户指令为准。

每次审查单列三项并给出文件依据或合理例外：转换的字段/null/敏感边界；类 author/since 与方法 param/return（覆写需核对上游契约）；业务枚举/常量在比较、查询、赋值和测试中的复用。覆盖本次所有 Java 文件；grep 仅找候选，零命中不是语义检查通过。
