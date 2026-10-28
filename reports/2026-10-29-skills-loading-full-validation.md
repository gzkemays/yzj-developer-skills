# 技能库加载与规则完整验证报告

验证日期：2026-10-29（Asia/Tokyo）  
验证版本：`25da6d2c62da99c689e9788ff0de2695a4e6ebb5`  
前次复验：[2026-10-29 技能库跨宿主加载复验报告](2026-10-29-skills-loading-revalidation.md)

## 验证结论

当前会话能够定位并按任务读取 34 份技能，入口、目录分层及主要宿主映射可识别。上轮发现的单栈项目误报和 reviewer 缺失漏检，已在本轮对应场景中验证修复。

本轮扩大到 38 个脚本主场景，29 个符合验收预期、9 个不符合；另执行 4 个语言环境对照场景，2 个符合预期、2 个不符合。失败场景归为六类校验问题，另有三处文字规则需要澄清。整体接入校验仍不通过。

主场景的验收预期以发现错误接入为目标。其中 `single-backend-contaminated` 是脚本顶部已声明需要人工判读的限制，本报告将其作为自动校验覆盖边界记录，不冒充新发现；同组的双技术栈标志混装场景则暴露了新的优先匹配问题。

本轮完整覆盖的是当前仓库的技能发现、必要字段、具体资源引用、规则衔接和所列本地校验场景。不同模型与宿主的新会话自动触发、真实业务全流程和辅助脚本的外部依赖仍需专门执行。文件可读与脚本检查结果不构成这些能力的认证。

## 验证证据

| 检查范围 | 实际结果 |
|---|---|
| 技能清单 | 通用 13、后端 18、前端 3，共 34 份；名称与目录一致，description 存在 |
| 具体资源引用 | 提取到的 12 个 scripts、references、agents 等具体文件均存在 |
| 辅助 Python 文件 | 17 个文件通过 AST 语法解析；未执行其业务功能或检查全部外部依赖 |
| 分层安装 | common 和 Claude 两种布局分别 34 份一致；双宿主布局 68 份一致 |
| 单栈识别 | Maven、Gradle、Java 源码、domain/integration、Vue views、Vue package 标志均通过 |
| reviewer 缺失 | 分层前端、分层后端、单前端、单后端四种缺失均正确返回非零 |
| 目标项目迁移 | 中文及空格目标目录中的分层布局通过；样例入口的 5 个相对链接仍可解析 |
| 原有漂移与结构检查 | 普通流程漂移、文件缺失、名称不匹配、无技能目录等控制场景按预期处理 |
| 排除目录 | .scratch、.claude/worktrees、.worktree、.bak-*、node_modules、.git 中的无效参考副本不影响有效计数 |
| 源文件稳定性 | 主测试前后 34 份技能、入口、模板及基线脚本的已记录哈希未发生变化 |

必要字段检查针对名称和 description，不等同于完整 YAML 或 Agent Skills 模式认证。前后端 reviewer 的同名是分域设计；framework-usage 仍为弃用转向入口。

所有目标样例都位于临时目录。主测试先复制基线快照，再构造不同布局；脚本调用在相互独立的样例上执行。覆盖、删除字段、移走文件等操作只作用于临时副本，样例已清理。

可复核的文件：

- [主测试脚本 validate.py](validation-2026-10-29-full/validate.py)
- [主测试原始结果 results.json](validation-2026-10-29-full/results.json)，含每次命令、退出码、完整输出和源文件哈希
- [语言环境对照脚本 check_locale.py](validation-2026-10-29-full/check_locale.py)
- [语言环境原始结果 locale-results.json](validation-2026-10-29-full/locale-results.json)
- [资源与语法检查 resources.json](validation-2026-10-29-full/resources.json)

## 可加载技能清单

以下 34 份均可从当前仓库定位和读取。这里列出的是仓库技能，不包含宿主另外安装的插件技能；读取成功不代表已经执行其全部工作流。

| 范围 | 技能入口 | 状态 |
|---|---|---|
| 通用 | [api-contract-checker](../common/skills/api-contract-checker/SKILL.md) | 可读取 |
| 通用 | [capability-registry](../common/skills/capability-registry/SKILL.md) | 可读取 |
| 通用 | [dev-output](../common/skills/dev-output/SKILL.md) | 可读取 |
| 通用 | [dev-session](../common/skills/dev-session/SKILL.md) | 可读取 |
| 通用 | [git-commit](../common/skills/git-commit/SKILL.md) | 可读取 |
| 通用 | [iteration-planner](../common/skills/iteration-planner/SKILL.md) | 可读取 |
| 通用 | [pre-dev-alignment](../common/skills/pre-dev-alignment/SKILL.md) | 可读取 |
| 通用 | [progress-tracker](../common/skills/progress-tracker/SKILL.md) | 可读取 |
| 通用 | [project-onboarding](../common/skills/project-onboarding/SKILL.md) | 可读取 |
| 通用 | [similar-issue-sweep](../common/skills/similar-issue-sweep/SKILL.md) | 可读取 |
| 通用 | [skill-creator](../common/skills/skill-creator/SKILL.md) | 可读取 |
| 通用 | [team-memory](../common/skills/team-memory/SKILL.md) | 可读取 |
| 通用 | [yzj-dev-workflow](../common/skills/yzj-dev-workflow/SKILL.md) | 可读取 |
| 后端 | [cache](../backend/cache/SKILL.md) | 可读取 |
| 后端 | [common](../backend/common/SKILL.md) | 可读取 |
| 后端 | [controller-conventions](../backend/controller-conventions/SKILL.md) | 可读取 |
| 后端 | [database-design](../backend/database-design/SKILL.md) | 可读取 |
| 后端 | [db-migration](../backend/db-migration/SKILL.md) | 可读取 |
| 后端 | [financial](../backend/financial/SKILL.md) | 可读取 |
| 后端 | [framework-usage](../backend/framework-usage/SKILL.md) | 可读取；已弃用，按正文转向组件技能 |
| 后端 | [grpc](../backend/grpc/SKILL.md) | 可读取 |
| 后端 | [integration-flow](../backend/integration-flow/SKILL.md) | 可读取 |
| 后端 | [logging](../backend/logging/SKILL.md) | 可读取 |
| 后端 | [model-conventions](../backend/model-conventions/SKILL.md) | 可读取 |
| 后端 | [mybatis](../backend/mybatis/SKILL.md) | 可读取 |
| 后端 | [project-structure](../backend/project-structure/SKILL.md) | 可读取 |
| 后端 | [reviewer](../backend/reviewer/SKILL.md) | 可读取 |
| 后端 | [security](../backend/security/SKILL.md) | 可读取 |
| 后端 | [service-conventions](../backend/service-conventions/SKILL.md) | 可读取 |
| 后端 | [tabledef](../backend/tabledef/SKILL.md) | 可读取 |
| 后端 | [testing](../backend/testing/SKILL.md) | 可读取 |
| 前端 | [i18n-automation](../frontend/i18n-automation/SKILL.md) | 可读取 |
| 前端 | [reviewer](../frontend/reviewer/SKILL.md) | 可读取 |
| 前端 | [view-conventions](../frontend/view-conventions/SKILL.md) | 可读取 |

前后端各有一份 reviewer，共计 34 份文件、33 个不同名称；必须结合所在技术栈目录加载。

## 问题一 多技术栈标志会重新放行混装

**复现：** 同一根技能目录安装通用、后端、前端技能，同时在项目根放置 `pom.xml` 和 `src/views/`。两份 reviewer 已因同名只剩一份。严格校验却返回 0，显示一致 32、项目专有差异 1、结构错误 0。

**原因：** [verify-baseline.sh](../scripts/verify-baseline.sh) 第 105 至 106 行把所有栈提示追加到优先区域；第 79 至 80 行命中第一个区域就返回。即使同时识别到 backend 和 frontend，也优先选择后端 reviewer 基线，把前端 reviewer 当作后端版本的普通项目差异。

没有本级标志的混装样例仍能正确失败，但原先带有两种本级标志的混装复现场景已重新出现错误通过。单后端根被混入前端规范也返回 0；后者属于脚本第 10 至 11 行承认的人工兜底限制。

**建议：** 仅在根目录恰好匹配单一技术栈时附加该栈的优先区域；匹配多个栈时要求明确的分域路径或报告歧义。另检查同一技能目录是否同时包含前后端规范，避免仅凭 reviewer 差异量推定项目定制。

## 问题二 基线目录含空格会使正常 reviewer 被误报

**复现：** 将同一份基线复制到名称含空格的目录，对完整分层项目执行校验。显式传入基线路径和使用该脚本默认基线路径，两种方式都返回 1，显示一致 32、结构错误 2；前后端 reviewer 均被误判为来源歧义。目标项目路径本身含空格的控制场景通过。

**原因：** [verify-baseline.sh](../scripts/verify-baseline.sh) 第 79 行使用 `for ar in $2`，把拼接后的优先路径列表按空格拆分，破坏了单个目录路径。

**建议：** 用数组或独立参数传递优先区域，通过带引号的参数展开遍历；基线目录移动、改名或包含空格后，正常分层布局应继续得到 34 份一致。

## 问题三 不存在的基线目录被接受为成功

**复现：** 对正常项目显式传入一个不存在的 framework 基线路径，严格模式返回 0。一致数为 0，34 份技能均被当作项目专有技能跳过。

**原因：** [verify-baseline.sh](../scripts/verify-baseline.sh) 第 35 至 36 行只校验目标项目目录，没有验证显式传入的基线目录。第 125 行又把所有找不到基线的情况统一归为项目专有。

**建议：** 开始比对前解析和验证基线路径，至少确认基线根及必要的技能区域存在。无效基线应返回参数或配置错误，不应进入逐技能比较。

## 问题四 必需的 frontmatter 字段缺失会漏检

**复现：** 分别删除已安装 cache 技能的 `name` 或 `description` 行，严格模式都返回 0，显示一致 33、项目专有差异 1、结构错误 0。把 name 改成另一个非空名称的控制场景则正确报错。

**原因：** [verify-baseline.sh](../scripts/verify-baseline.sh) 第 122 至 123 行仅在 name 非空时检查目录匹配，没有把 name 缺失计为错误，也没有检查 description。规范技能正文差异默认属于提示，不触发严格模式失败。

**建议：** 对每份技能先检查 frontmatter 边界和非空 name、description，再校验名称与目录。当前源库的 34 份字段齐全；此问题影响目标项目副本损坏后的识别能力。

## 问题五 双宿主必需流程技能只检查并集

**复现：** 双宿主项目保留 `.claude/skills/dev-session/`，删除 `common/skills/dev-session/`。严格模式返回 0，显示一致 67、结构错误 0。此时 AGENTS 入口声明的通用目录已没有开发流程总入口。

**原因：** [verify-baseline.sh](../scripts/verify-baseline.sh) 第 159 行对两种宿主目录使用“任一存在即可”的判断，导致一侧副本掩盖另一侧缺失。

**建议：** 先确认项目启用了哪些宿主布局，再分别检查每个已启用布局的必需流程技能。单宿主项目仍只检查自身布局；双宿主项目不能依赖另一宿主的未声明目录补齐。

## 问题六 项目覆写识别存在语言环境依赖和误判

**本机环境：** Windows Git Bash；主测试继承 `LANG=C.UTF-8`、`LC_ALL=C.UTF-8`。对照测试显式切换 `LC_ALL` 与 `LANG`。

| 文本情形 | C 环境 | C.UTF-8 环境 | 正确预期 |
|---|---|---|---|
| iteration-planner 增加文件头差异声明和 📌 标记段 | 退出 0，识别为项目覆写 | 退出 1，误识别为普通漂移 | 应按声明的覆写路径提示人工核对 |
| project-onboarding 仅追加一行无覆写声明的普通文本 | 退出 0，误识别为项目覆写 | 退出 1，识别为普通漂移 | 应识别为未声明漂移并失败 |

两组对照说明两个独立原因：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 136 行依靠 `grep -q '📌'` 搜索全文，本机该匹配在两种语言环境中结果不同；当匹配有效时，project-onboarding 基线原文已有的 📌 说明文字足以把任何追加修改误判为项目覆写。

**建议：** 使用不依赖语言环境的明确覆写声明，并检查文件头差异清单及对应改动，不能只判断整个文件是否存在某个符号。语言环境问题是本机实测结果，不外推为所有 grep 实现都具有相同行为。

## 需要澄清的三处文字规则

这些项目来自文档语义核对，不计入脚本的 9 个主场景失败。建议与脚本修订分开评审。

| 位置 | 当前歧义 | 建议 |
|---|---|---|
| [project-onboarding](../common/skills/project-onboarding/SKILL.md) 第 46、55 行 | 第一步要求把识别结果写入目标入口，第二步才要求全程只读并等待确认；按步骤直接执行容易提前写入 | 第一步将结果记入预演报告，确认后再写目标入口 |
| [api-contract 规则](../templates/common/rules/api-contract.md) 第 12、21 行 | 创建 ID 的泛型允许 number/string，而下文要求所有 ID 一律 string；[api-contract-checker](../common/skills/api-contract-checker/SKILL.md) 第 101 行又以 Long 对应 number 为默认 | 将 ID 与普通 Long 数值分开，并统一创建接口 ID 的类型表述 |
| [yzj-dev-workflow](../common/skills/yzj-dev-workflow/SKILL.md) 第 66 行与 [db-migration](../backend/db-migration/SKILL.md) 第 12 行 | DDL 检查项要求按 db-migration 生成脚本，而该技能限制仅显式请求时执行 | 在流程检查项补明“已获显式请求时生成，否则记录待办或使用项目既有迁移机制” |

通用入口中“先预演、确认后写入”和 db-migration 的显式触发约束仍应遵守；上述建议用于减少不同模型按步骤理解时的分歧。

## 路由与执行边界核对

| 场景 | 当前可识别的加载关系 | 边界 |
|---|---|---|
| 今天做什么、继续任务 | iteration-planner，确认方向后进入 dev-session | 本轮做文件与描述核对，未模拟独立新会话 |
| 业务功能开发 | dev-session、pre-dev-alignment 及对应技术栈规范 | 真实业务按任务级别执行评审门禁 |
| YZJ 后端开发 | yzj-dev-workflow 及命中的后端技能 | 同栈适用 |
| Vue 前端开发与国际化 | view-conventions、i18n-automation | 读取项目设计系统和契约规则 |
| 代码审查 | 前后端各自目录内的 reviewer | 不允许同名覆盖替代另一端 |
| 跨端接口修改 | 入口引用的 api-contract 规则、api-contract-checker | 先更新契约，再修改实现 |
| 引入或同步技能 | project-onboarding | 先预演报告与动作清单，确认后写目标项目 |
| 生成迁移脚本 | db-migration | 显式请求条件已可识别 |
| 提交与推送 | git-commit | 按当前会话授权范围执行 |
| 命中 framework-usage | 转向对应组件技能 | 弃用文件不作为现行开发规范 |
| 技能库只读验证与小型文档维护 | 仓库通用入口及相关参考 | 不套用业务项目完整 12 阶段，不把模板台账当真实进度 |

## 全部主场景记录

主场景在本机继承的 C.UTF-8 环境下运行。除标明默认模式的场景外，技能比较使用严格模式；表中的“符合”表示正确接受或正确拒绝该样例。

计数依次为“一致 / 项目专有差异 / 项目覆写 / 流程漂移 / 结构错误”；破折号表示脚本在输出汇总前退出。原始日志和命令见 results.json。

| 场景及证据 ID | 预期退出码 | 实际退出码 | 计数 | 结论 |
|---|---|---|---|---|
| 通用目录分层安装<br>`split-common` | 0 | 0 | 34 / 0 / 0 / 0 / 0 | 符合 |
| Claude 目录分层安装<br>`split-claude` | 0 | 0 | 34 / 0 / 0 / 0 / 0 | 符合 |
| 双宿主完整安装<br>`dual-host` | 0 | 0 | 68 / 0 / 0 / 0 / 0 | 符合 |
| 单后端 Maven 标志<br>`single-backend-pom` | 0 | 0 | 31 / 0 / 0 / 0 / 0 | 符合 |
| 单前端 views 标志<br>`single-frontend-views` | 0 | 0 | 16 / 0 / 0 / 0 / 0 | 符合 |
| 单后端 Gradle 标志<br>`single-backend-gradle` | 0 | 0 | 31 / 0 / 0 / 0 / 0 | 符合 |
| 单后端 Java 源码标志<br>`single-backend-java` | 0 | 0 | 31 / 0 / 0 / 0 / 0 | 符合 |
| 单后端 domain/integration 标志<br>`single-backend-domain` | 0 | 0 | 31 / 0 / 0 / 0 / 0 | 符合 |
| 单前端 Vue package 标志<br>`single-frontend-package` | 0 | 0 | 16 / 0 / 0 / 0 / 0 | 符合 |
| 嵌套后端目录<br>`nested-backend` | 0 | 0 | 34 / 0 / 0 / 0 / 0 | 符合 |
| 分层后端缺 reviewer<br>`missing-backend-reviewer` | 非零 | 1 | 33 / 0 / 0 / 0 / 1 | 符合 |
| 分层前端缺 reviewer<br>`missing-frontend-reviewer` | 非零 | 1 | 33 / 0 / 0 / 0 / 1 | 符合 |
| 单后端缺 reviewer<br>`missing-single-backend-reviewer` | 非零 | 1 | 30 / 0 / 0 / 0 / 1 | 符合 |
| 单前端缺 reviewer<br>`missing-single-frontend-reviewer` | 非零 | 1 | 15 / 0 / 0 / 0 / 1 | 符合 |
| 无本级栈标志的混装<br>`flat-no-markers` | 非零 | 1 | 32 / 0 / 0 / 0 / 1 | 符合 |
| 双栈标志下混装<br>`flat-dual-markers` | 非零 | 0 | 32 / 1 / 0 / 0 / 0 | **不符合** |
| 单后端混入前端技能（已知限制）<br>`single-backend-contaminated` | 非零 | 0 | 32 / 1 / 0 / 0 / 0 | **不符合** |
| 流程漂移，严格模式<br>`flow-drift-strict` | 非零 | 1 | 33 / 0 / 0 / 1 / 0 | 符合 |
| 流程漂移，默认模式<br>`flow-drift-default` | 0 | 0 | 33 / 0 / 0 / 1 / 0 | 符合 |
| 漂移差异输出<br>`show-diff` | 非零 | 1 | 33 / 0 / 0 / 1 / 0 | 符合 |
| 含明确覆写声明<br>`declared-override` | 0 | 1 | 33 / 0 / 0 / 1 / 0 | **不符合** |
| 基线已有标记，新增未声明漂移<br>`drift-intrinsic-marker` | 非零 | 1 | 33 / 0 / 0 / 1 / 0 | 符合 |
| 项目自定义技能<br>`unknown-project-skill` | 0 | 0 | 34 / 0 / 0 / 0 / 0 | 符合 |
| 后端仅自定义技能<br>`custom-only-backend` | 0 | 0 | 13 / 0 / 0 / 0 / 0 | 符合 |
| 技能目录缺 SKILL.md<br>`missing-skill-file` | 非零 | 1 | 33 / 0 / 0 / 0 / 1 | 符合 |
| 技能名称与目录不符<br>`mismatch-name` | 非零 | 1 | 33 / 1 / 0 / 0 / 1 | 符合 |
| 缺 name 字段<br>`missing-name` | 非零 | 0 | 33 / 1 / 0 / 0 / 0 | **不符合** |
| 缺 description 字段<br>`missing-description` | 非零 | 0 | 33 / 1 / 0 / 0 / 0 | **不符合** |
| 单宿主缺核心流程技能<br>`missing-root-flow` | 非零 | 1 | 33 / 0 / 0 / 0 / 1 | 符合 |
| 双宿主一侧缺核心流程技能<br>`dual-missing-root-flow` | 非零 | 0 | 67 / 0 / 0 / 0 / 0 | **不符合** |
| 排除目录内的无效副本<br>`excluded-copies` | 0 | 0 | 68 / 0 / 0 / 0 / 0 | 符合 |
| 目标迁移到中文及空格路径<br>`relocated-target` | 0 | 0 | 34 / 0 / 0 / 0 / 0 | 符合 |
| 显式基线路径含空格<br>`baseline-path-spaces` | 0 | 1 | 32 / 0 / 0 / 0 / 2 | **不符合** |
| 默认基线路径含空格<br>`baseline-path-spaces-default` | 0 | 1 | 32 / 0 / 0 / 0 / 2 | **不符合** |
| 显式基线路径不存在<br>`missing-framework-path` | 非零 | 0 | 0 / 0 / 0 / 0 / 0 | **不符合** |
| 目标没有技能目录<br>`no-skills` | 非零 | 1 | — | 符合 |
| 目标路径不存在<br>`invalid-target` | 2 | 2 | — | 符合 |
| 未知命令参数<br>`unknown-option` | 2 | 2 | — | 符合 |

合计 38 个主场景，29 个符合、9 个不符合。语言环境的 4 个额外对照场景单独列在问题六及 locale-results.json 中，不与主场景合并计数。

## 修订与复验建议

先修正来源匹配和基线路径校验，确保比较对象可靠；再补齐逐宿主必需项、元数据与覆写识别。保留本轮已经通过的单栈和 reviewer 缺失控制场景，防止修复新问题时重新引入旧问题。

修订后可在技能仓库根目录运行：

```text
python reports/validation-2026-10-29-full/validate.py --bash <Git Bash的bash.exe路径> --jobs 4
python reports/validation-2026-10-29-full/check_locale.py --bash <Git Bash的bash.exe路径>
```

脚本将覆盖各自结果 JSON，请在需要保留本轮证据时先复制结果文件。测试脚本本身的退出码不代替用例结论，应检查 JSON 的 `matches_expectation`、计数和原始输出。目标样例自动清理，技能源文件保持不变。

本次仅新增验证脚本、结果和报告，没有修改技能正文、项目入口模板或基线校验脚本，也没有提交或推送代码。
