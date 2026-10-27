---
name: yzj-skill-creator
description: "创建或维护 YZJ 团队共享技能，将流程、规范与复用经验组织为 Codex 的 SKILL.md 及必要资源；适用于团队技能沉淀、宿主适配和触发描述优化。"
---

# 团队技能创建与维护

1. 查现有技能、`.agents/catalog.json` 和能力登记册，判断修改既有技能、补 reference 还是新增能力，避免重复入口。
2. 当前环境内置 `skill-creator` 可用时读取并复用它的创作与校验工具，不可用时按本流程继续；不假定其他宿主 CLI、认证或子代理能力存在。
3. 技能名使用小写 kebab-case，少于 64 字符，目录名与 `name` 一致。description 简洁说明能力与触发边界；自动选择不是确定性事件钩子。
4. `.agents/skills/<name>/SKILL.md` 放必要决策与流程。长规范放 `references/` 并从入口明确引用；确定性重复逻辑放 `scripts/`；产物素材放 `assets/`。不为凑结构建空目录。
5. 保留团队分级、审查、契约、进度与沉淀约定，尊重用户已给出的范围和授权。工具用当前实际能力表达，不假设专属计划模式、预览 API 或个人记忆路径。
6. 在本共享库按 AGENTS.md 维护：普通技能改源规范和 `scripts/sync-codex-skills.py` 的转换后生成，两个 Codex 专属入口手工维护；新增技能同步更新目录映射规则。
7. 运行 `python scripts/sync-codex-skills.py --check` 和 `python scripts/verify-codex-skills.py`。脚本变更用实际小样例验证输入、输出及失败情况，结构校验不替代行为测试。
8. 检查一条应采用、一条不应采用和一条边界请求。只有具备并已授权独立评测能力时才做对照实验；没有则报告手工检查，不虚报触发率，不直接调用旧平台 CLI 评测脚本。

跨项目经验去业务专名后反哺共享库；项目专有项留在副本并注明来源和覆写依据。
