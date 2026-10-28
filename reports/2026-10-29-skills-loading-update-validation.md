# 技能库更新复验报告

验证日期：2026-10-29（Asia/Tokyo）  
验证版本：`7cded4dce4b37ec1058679157ad2f777ec79b997`  
对照版本：`25da6d2c62da99c689e9788ff0de2695a4e6ebb5`  
上轮报告：[技能库加载与规则完整验证报告](2026-10-29-skills-loading-full-validation.md)

## 复验结论

本次更新通过了上轮全部 38 个主场景和 4 个语言环境对照场景，原有正常安装场景未出现回归。上轮提出的三处文字歧义也已澄清。

针对新实现增加 15 个边界场景，其中 7 个符合预期、8 个不符合，归为三类问题：frontmatter 没有按结构和字段值校验、空基线目录仍可通过、描述文字仍可被识别为覆写声明。因此，上轮具体复现已经修复，但严格模式仍不能作为完整的接入验收依据。

当前源库的 34 份技能均可发现和读取，所检查的名称、描述及资源引用未发现缺失。新增问题影响目标副本或基线路径出现异常时的识别能力；不同模型在目标项目新会话中的自动触发，仍需真实宿主验证。

## 验证范围与结果

| 检查 | 结果 |
|---|---|
| 上轮主场景原样复跑 | 38 / 38 符合预期；上轮为 29 / 38 |
| C 与 C.UTF-8 对照 | 4 / 4 符合预期；上轮为 2 / 4 |
| 新增边界场景 | 7 / 15 符合预期，8 个不符合归为三类问题 |
| 源库技能 | 通用 13、后端 18、前端 3，共 34 份；必需字段检查无异常 |
| 具体资源引用 | 12 个提取到的具体文件引用全部存在 |
| 辅助 Python 文件 | 17 个通过 AST 语法解析；未执行其业务流程和外部依赖 |
| 来源稳定性 | 主测试、边界测试前后所记录的源文件哈希均未变化 |

共运行 57 个场景，49 个符合预期、8 个不符合。失败指输出不符合验收预期：错误样例被正确拒绝，也算符合预期。静态字段检查只覆盖本库当前写法，不等同于完整 YAML 模式认证。

所有目标项目及异常基线均为临时副本，执行后已清理。回归脚本与上轮逐字相同，旧报告和旧结果保持完整；脚本中的历史 note 不替代本轮退出码和日志。

## 上轮问题复核

| 上轮问题 | 本轮对应结果 |
|---|---|
| 双栈标志混装误通过 | 严格模式返回 1，报告来源歧义及混装；单后端混入整套前端技能也返回 1 |
| 基线路径含空格 | 显式路径与脚本默认路径均返回 0，34 份一致 |
| 不存在的基线路径 | 返回 2；新增的缺少一个基线区域场景也返回 2 |
| 删除 name 或 description 行 | 两种情况均返回 1；正常元数据不受影响 |
| 双宿主一侧缺核心流程 | common 侧或 Claude 侧缺 dev-session 均返回 1 |
| 覆写识别受语言环境影响、原文符号误触发 | 两种语言环境下，合法声明均返回 0，未声明漂移均返回 1 |

以上结论限定于对应复现场景。元数据、基线有效性和覆写声明的进一步边界见下文。

| 上轮文字歧义 | 本轮文本依据 |
|---|---|
| 预演前先写目标入口 | [project-onboarding](../common/skills/project-onboarding/SKILL.md) 第 46 行明确先记入 dry-run 报告，确认后才写目标入口 |
| 创建接口与 ID 字段类型不一致 | [api-contract](../templates/common/rules/api-contract.md) 第 12、21 行统一 ID 为 string；[api-contract-checker](../common/skills/api-contract-checker/SKILL.md) 第 101 行区分 ID 类 Long 与普通数值 Long |
| DDL 检查项与迁移技能触发条件冲突 | [yzj-dev-workflow](../common/skills/yzj-dev-workflow/SKILL.md) 第 66 行明确仅用户显式要求时生成迁移脚本 |

## 剩余问题一 frontmatter 只做全文文本匹配

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 130 至 138 行。name 用 sed 从全文取值，description 只判断全文是否有以 `description:` 开头的行。

六个场景不符合预期：

| 目标 cache 技能的变动 | 预期 | 实际 |
|---|---|---|
| description 只有键，没有值 | 拒绝 | 返回 0 |
| description 的值为空字符串 `""` | 拒绝 | 返回 0 |
| description 使用 `>`，但没有文本内容 | 拒绝 | 返回 0 |
| 删除 frontmatter 的两条边界，保留正文中的字段行 | 拒绝 | 返回 0 |
| frontmatter 缺字段，只在正文代码块中写 name 和 description | 拒绝 | 返回 0 |
| 合法名称写为 `name: "cache"` | 接受 | 返回 1，误报名称与目录不符 |

前五种无效元数据均被记为普通项目差异，严格模式没有阻止通过；最后一种则把 YAML 引号当成名称的一部分。没有有效描述，模型无法按描述可靠路由；没有 frontmatter 边界，字段也不能作为技能元数据加载。

建议先解析文件开头完整的 frontmatter，再校验 name、description 都是非空字符串，并使用解析后的 name 与目录比较。正文示例不得补齐头部缺失字段。仓库现有 [quick_validate.py](../common/skills/skill-creator/scripts/quick_validate.py) 也采用提取 frontmatter 后解析 YAML 的路线，但不能据此假定其现有检查已覆盖本报告所有空值场景。

## 剩余问题二 三个空目录仍被视为有效基线

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 40 至 42、140 行。

构造仅含 `common/skills/`、`backend/`、`frontend/` 三个空目录的基线，对完整分层项目运行严格校验，实际返回 0：一致 0、结构错误 0，34 份目标技能全部被当作项目专有技能跳过。

本轮新增的目录存在检查修复了路径不存在或缺区域的问题，但没有确认目录内存在可比较的技能内容。空目录不能提供任何基线保证，却显示校验成功。

建议在比较前核对基线必要文件或基线清单，明确拒绝空的、无法形成有效比较来源的基线；不能只依据三个目录名存在就放行。配置错误应在逐技能比较前返回非零。

## 剩余问题三 描述中的锚点文字会被误认作覆写声明

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 154 行；声明格式依据为 [project-onboarding](../common/skills/project-onboarding/SKILL.md) 第 129 至 135 行。

在 iteration-planner 的 description 块中添加下面一行，没有在 frontmatter 之后添加覆写引用块或差异清单：

```yaml
  文档术语示例：本文件 = framework 基线；此处仅为描述文字。
```

严格模式仍返回 0，统计为项目覆写 1、流程漂移 0。原因是前 20 行内只要包含固定短语就匹配，没有检查它是否位于 frontmatter 之外，以及是否确实为要求的声明引用块。

控制场景表明，真正位于 frontmatter 之后的合法声明能通过，放到第 20 行之后的声明会按漂移拒绝；语言环境问题也已修复。剩余缺口是声明所处位置和结构的识别。

建议在 frontmatter 解析完成后，仅识别约定位置的声明引用块。具体差异是否与清单一致、是否保留执行门禁，继续按接入流程人工核对。

## 新增边界场景明细

| 场景与证据 ID | 预期退出码 | 实际退出码 | 结论 |
|---|---|---|---|
| 未修改的完整分层项目<br>`valid-control` | 0 | 0 | 符合 |
| description 没有值<br>`empty-description-null` | 非零 | 0 | **不符合** |
| description 为空字符串<br>`empty-description-quoted` | 非零 | 0 | **不符合** |
| description 块没有内容<br>`empty-description-folded` | 非零 | 0 | **不符合** |
| 移除 frontmatter 边界<br>`no-frontmatter` | 非零 | 0 | **不符合** |
| 字段只存在于正文代码示例<br>`metadata-only-in-body` | 非零 | 0 | **不符合** |
| 合法名称加 YAML 引号<br>`quoted-valid-name` | 0 | 1 | **不符合** |
| 三个基线区域均为空目录<br>`empty-baseline-regions` | 非零 | 0 | **不符合** |
| 基线缺 frontend 区域<br>`missing-baseline-region` | 非零 | 2 | 符合 |
| 仅子项目有技能，根目录缺流程<br>`missing-root-layout` | 非零 | 1 | 符合 |
| 前端目录混入后端技能<br>`frontend-contaminated` | 非零 | 1 | 符合 |
| 锚点短语只出现在 description<br>`anchor-only-in-description` | 非零 | 0 | **不符合** |
| 覆写声明在第 20 行之后<br>`override-after-line-20` | 非零 | 1 | 符合 |
| frontmatter 后紧跟合法覆写声明<br>`valid-override-header` | 0 | 0 | 符合 |
| 双宿主中 Claude 一侧缺流程技能<br>`dual-missing-claude-flow` | 非零 | 1 | 符合 |

## 证据与复现

| 文件 | 内容 |
|---|---|
| [results.json](validation-2026-10-29-update-7cded4d/results.json) | 38 个主场景的命令、退出码、计数、完整输出和源文件哈希 |
| [locale-results.json](validation-2026-10-29-update-7cded4d/locale-results.json) | 4 个语言环境对照结果 |
| [boundary-results.json](validation-2026-10-29-update-7cded4d/boundary-results.json) | 15 个边界场景、验收预期、原始输出及来源哈希 |
| [static-results.json](validation-2026-10-29-update-7cded4d/static-results.json) | 34 份技能清单、资源引用、语法检查及回归脚本一致性 |
| [validate.py](validation-2026-10-29-update-7cded4d/validate.py) | 上轮 38 个场景的原样回归脚本 |
| [check_locale.py](validation-2026-10-29-update-7cded4d/check_locale.py) | 语言环境对照脚本 |
| [check_boundaries.py](validation-2026-10-29-update-7cded4d/check_boundaries.py) | 本轮新增边界验证脚本 |

在仓库根目录使用 Python 3 与 Git Bash，可分别运行：

```text
python reports/validation-2026-10-29-update-7cded4d/validate.py --bash <bash.exe路径> --jobs 4
python reports/validation-2026-10-29-update-7cded4d/check_locale.py --bash <bash.exe路径>
python reports/validation-2026-10-29-update-7cded4d/check_boundaries.py --bash <bash.exe路径> --jobs 4
```

脚本将覆盖各自的结果 JSON，复跑前如需保留本轮证据应先复制。验收看 JSON 中的 `matches_expectation` 和原始输出，验证脚本自身退出成功不代表所有样例符合预期。

本轮仅新增报告、验证脚本和结果文件，没有修改技能正文、规则或基线校验脚本。
