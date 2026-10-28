---
name: yzj-dev-workflow
description: "在 YZJ Framework、Spring Boot 3、MyBatis-Flex 项目中开发业务代码，按 domain、integration、interfaces、support 四层路由到对应规范。"
---

# yzj-dev-workflow

执行时先完整读取 [规范与流程](references/rules.md)，再按任务读取其中引用的技能和项目文档。审查技能须读取全文及漏检史，不只依据入口给出结论。

项目路径、构建命令、契约及授权以当前项目 `AGENTS.md` 和用户指令为准。

编码前按改动读取实际细则：转换读 model-conventions 第四节和同域 ConvertAid；业务编码读 common 第二节和已有枚举/常量；注释读 backend-reviewer 第五节。逐文件确认显式字段映射、类 author/since、方法参数/返回契约、枚举 API；不能等到最后才补规则。
