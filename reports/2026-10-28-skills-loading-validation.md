# 技能库跨宿主加载验证报告

验证日期：2026-10-28（Asia/Tokyo）  
验证对象：YZJ 团队共享技能库 `skills/`  
文档基线：2026-10-28；检查时 Git HEAD：`6ab69f2`  
验证环境：当前 Codex 会话、Windows PowerShell、Git Bash  
面向读者：技能库架构师及接入维护人员

## 验证结论

当前会话能够从 `AGENTS.md` 识别技能目录、触发条件、规则入口和执行门禁，并按任务读取对应技能。共识别到 34 份 `SKILL.md`，其中通用目录 13 份、后端目录 18 份、前端目录 3 份。名称均与所属目录一致，触发描述齐全。

跨宿主接入仍存在三个已确认问题：部分规则强制依赖 `CLAUDE.md`；前后端技能统一安装到根目录时会覆盖同名 `reviewer`；基线脚本对该来源歧义跳过检查并返回成功。因此，当前可以确认显式加载路径可用，尚不满足跨宿主无歧义接入的完整验收要求。

| 验证项 | 结果 | 证据范围 |
|---|---|---|
| 通用入口与目录识别 | 通过 | 当前会话实际读取 `AGENTS.md`、README 和接入模板 |
| 技能名称与触发描述 | 通过 | 34 份文件均有名称与描述，名称与目录一致 |
| 按任务选择技能 | 可确定 | 根据入口路由和触发描述核对，关键技能读取全文 |
| 分层安装的基线比对 | 通过 | 临时样例中 34 份技能一致，严格模式退出码为 0 |
| 流程技能漂移检测 | 通过 | 修改一份临时技能后，严格模式检测到漂移并返回 1 |
| 前后端统一安装 | 不通过 | 34 份源技能安装后仅剩 33 份，后端 reviewer 被覆盖 |
| 来源歧义检测 | 不通过 | reviewer 被跳过，严格模式仍返回 0 |
| 仅有 AGENTS 入口的审查协议 | 静态检查不通过 | 前端 reviewer 强制读取并声明已读 `CLAUDE.md` |
| 不同模型的新会话自动触发 | 待验证 | 本次结论不覆盖不同模型和宿主的独立新会话 |

## 范围与验证方法

本次验证覆盖技能发现、规则加载说明、关键流程引用、安装布局以及基线校验行为。检查了全部技能的 frontmatter 名称与描述，并读取通用入口、两类宿主模板、常驻规则模板及接入、迭代、开发编排、契约校验、前端审查等关键正文。名称和描述检查不等同于完整 Agent Skills 格式认证。

脚本验证采用临时样例，没有向真实业务项目安装技能。样例包含技能副本、规则和文档骨架；后端使用 `pom.xml` 标志，前端使用 `src/views/` 标志。分别测试分层安装、统一安装和流程漂移。样例仅验证文件布局与校验逻辑，不代表真实项目的完整接入验收。

基线命令在 Git Bash 中执行：

```text
bash scripts/verify-baseline.sh <临时样例根目录> <skills源目录> --strict
```

本次没有执行全部技能的业务工作流、实际开发审查或多模型对照测试。临时样例已清理；报告整理未修改技能正文、入口模板和校验脚本。

## 技能加载清单

下列清单表示文件可定位、可按任务读取。加载时仍需满足技术栈和触发条件；前后端 `reviewer` 是两份不同内容，必须按所在目录区分。`framework-usage` 已弃用，仅承担旧引用的转向说明。

### 通用目录中的 13 份技能

| 技能 | 职责与加载条件 |
|---|---|
| [dev-session](../common/skills/dev-session/SKILL.md) | 研发生命周期总入口，编排需求、开发、审查、自测、验收及收尾 |
| [pre-dev-alignment](../common/skills/pre-dev-alignment/SKILL.md) | 编码前对齐、任务分级、风险判断、文档产出与评审 |
| [iteration-planner](../common/skills/iteration-planner/SKILL.md) | 会话开局读取台账、计划与近期活动，确认开发方向 |
| [progress-tracker](../common/skills/progress-tracker/SKILL.md) | 维护进度台账、任务清单、backlog 和并行文档约定 |
| [team-memory](../common/skills/team-memory/SKILL.md) | 记录反馈、踩坑、决策及团队共享认知 |
| [capability-registry](../common/skills/capability-registry/SKILL.md) | 开发前查复用，开发后登记能力并标记待反哺项 |
| [similar-issue-sweep](../common/skills/similar-issue-sweep/SKILL.md) | 修复、纠正、优化后扫描同类问题 |
| [api-contract-checker](../common/skills/api-contract-checker/SKILL.md) | YZJ 前后端接口契约检查，适用于对应技术栈 |
| [dev-output](../common/skills/dev-output/SKILL.md) | 输出开发成果报告并关联需求台账 |
| [yzj-dev-workflow](../common/skills/yzj-dev-workflow/SKILL.md) | YZJ 后端业务开发编排，同栈项目适用 |
| [project-onboarding](../common/skills/project-onboarding/SKILL.md) | 新项目引入、既有项目对比融入与同步 |
| [git-commit](../common/skills/git-commit/SKILL.md) | 提交授权、分支、安全暂存与 Worktree 约定 |
| [skill-creator](../common/skills/skill-creator/SKILL.md) | 技能创建、改进与评测；入口说明其评测脚本依赖 Claude Code CLI |

### 后端目录中的 18 份技能

后端规范面向 YZJ 四层架构及相关组件，按具体任务加载。

| 技能 | 职责与加载条件 |
|---|---|
| [project-structure](../backend/project-structure/SKILL.md) | 架构分层、包结构、文件归属与模块依赖 |
| [model-conventions](../backend/model-conventions/SKILL.md) | DTO、VO、Operate、Query 和模型转换 |
| [service-conventions](../backend/service-conventions/SKILL.md) | Service 命名、职责边界及查询规范 |
| [controller-conventions](../backend/controller-conventions/SKILL.md) | Controller 写法、接口路径与响应包装 |
| [integration-flow](../backend/integration-flow/SKILL.md) | 跨业务 Flow、Job、Listener、Initializer |
| [mybatis](../backend/mybatis/SKILL.md) | 查询链、分页、排序与数据库字段处理 |
| [cache](../backend/cache/SKILL.md) | 缓存、分布式锁与相关框架配置 |
| [common](../backend/common/SKILL.md) | 工具类、枚举、异常、统一响应及上下文 |
| [security](../backend/security/SKILL.md) | 认证、权限和安全编码规则 |
| [logging](../backend/logging/SKILL.md) | 日志规范、敏感数据处理与日志过滤配置 |
| [financial](../backend/financial/SKILL.md) | 金额、幂等、事务、余额一致性及流水 |
| [database-design](../backend/database-design/SKILL.md) | 表、字段与索引设计建议；不直接生成 DDL 或 Entity |
| [tabledef](../backend/tabledef/SKILL.md) | 手写 TableDef 的创建与维护 |
| [db-migration](../backend/db-migration/SKILL.md) | 生成成对迁移脚本；仅在用户显式要求时执行 |
| [grpc](../backend/grpc/SKILL.md) | Proto 定义与 gRPC 服务开发 |
| [testing](../backend/testing/SKILL.md) | 单元测试规范、Mock 边界和必测场景 |
| [reviewer](../backend/reviewer/SKILL.md) | 后端七步代码审查及各规范维度核对 |
| [framework-usage](../backend/framework-usage/SKILL.md) | 已弃用；引导转向 common、cache、mybatis、security |

### 前端目录中的 3 份技能

前端规范按 Vue 3、Naive UI、TypeScript 等实际技术栈和任务选择。

| 技能 | 职责与加载条件 |
|---|---|
| [view-conventions](../frontend/view-conventions/SKILL.md) | 页面、表单、表格、组件、API 调用和状态管理规范 |
| [i18n-automation](../frontend/i18n-automation/SKILL.md) | 国际化补齐、完整性检查与硬编码审计 |
| [reviewer](../frontend/reviewer/SKILL.md) | 前端七步代码审查，包括契约、i18n、token 和表单检查 |

## 规则入口与加载顺序

| 文件 | 作用 |
|---|---|
| [AGENTS.md](../AGENTS.md) | 技能库通用入口，声明目录、路由、宿主映射和执行门禁 |
| [CLAUDE.md](../CLAUDE.md) | Claude Code 维护入口，引用通用入口并补充宿主路由 |
| [AGENTS.md.template](../templates/AGENTS.md.template) | 目标项目通用入口模板，明确规则和技能的相对引用 |
| [CLAUDE.md.template](../templates/CLAUDE.md.template) | 目标项目 Claude Code 入口模板 |
| [collaboration.md](../templates/common/rules/collaboration.md) | 协作、冲突处理、授权和执行自证规则模板 |
| [api-contract.md](../templates/common/rules/api-contract.md) | 响应、ID、时间、分页、校验与契约变更规则模板 |

目标项目的通用模板要求开始工作时读取 `common/rules/collaboration.md`，接口开发或跨端修改时追加读取 `common/rules/api-contract.md`，再按任务选择技能并读取正文和适用的关联内容。子仓库的入口、技能位置及共享文档路径需要在接入时写明。

核心约束可以明确识别：技能执行前读取全文；业务开发中的 P4 审查、P8 确认、P9 台账及编码前评审按流程执行；审查结论提供文件依据；不把搜索零命中等同于语义检查通过；不虚报未执行的验证；评审和 Git 操作分别判断授权；入口加载引用采用相对路径。

本技能库自身的只读咨询、维护及小型文档调整有明确流程豁免。`templates/.document/` 是待实例化的文档骨架，不应作为本技能库正在开展业务需求的真实台账。

## 典型请求的路由判断

以下是依据已读入口和技能描述得到的路由判断，不是不同模型的自动触发测试记录。

| 请求场景 | 应加载的技能或规则 | 关键边界 |
|---|---|---|
| 今天做什么、接着做 | iteration-planner，方向确认后进入 dev-session | 先读取项目实际台账和计划 |
| 开发一个功能 | dev-session、pre-dev-alignment，再加载对应技术栈技能 | 按任务级别执行文档与评审门禁 |
| 开发 YZJ 后端业务 | yzj-dev-workflow 与命中的后端规范 | 只在对应技术栈适用 |
| 开发 Vue 管理页面 | view-conventions，涉及文案时加载 i18n-automation | 同时读取项目设计系统约定 |
| 审查代码 | 按文件范围加载前端或后端 reviewer | 全栈任务需要分别读取两份 reviewer |
| 修改接口或两端契约 | api-contract 规则、api-contract-checker | 先更新设计契约，再修改实现 |
| 引入或同步这套技能 | project-onboarding | 保留项目专有内容与执行门禁 |
| 生成迁移脚本 | db-migration | 需要用户显式要求，不因普通开发任务自动执行 |
| 提交或推送代码 | git-commit | 按已取得的相应授权执行 |
| 命中 framework-usage | 转到对应组件技能 | 不再把弃用文件作为开发规范执行 |

## 已确认的问题

### 问题一 部分规则仍强制依赖 CLAUDE 入口

**影响：仅使用 AGENTS 入口的项目无法严格满足现有前端审查协议。建议优先处理。**

[frontend/reviewer/SKILL.md](../frontend/reviewer/SKILL.md) 第 18 行要求读取前端仓库 `CLAUDE.md` 全文，第 19 行强制输出包含“已 Read 前端 CLAUDE.md”的确认句，第 118 行的报告模板再次固化同一句话。对于按照通用接入方案仅提供 `AGENTS.md` 的项目，模型会遇到必读文件不存在和确认句无法如实填写的问题。

同类引用还包括 [dev-session](../common/skills/dev-session/SKILL.md) 第 15、128、132、133、197、259 行，以及 [api-contract-checker](../common/skills/api-contract-checker/SKILL.md) 第 14、164 行。契约检查仍指向 `CLAUDE.md` 的旧章节，而接入模板已支持把契约放入独立规则文件。

建议将这些权威来源统一表述为“当前项目入口及其显式引用的规则”，并按实际宿主定位 `AGENTS.md` 或 `CLAUDE.md`。审查协议应声明实际读取的文件路径，保留全文读取要求。修改时保留有效的 Claude 专属说明，不做无差别文本替换。

验收标准：仅提供 `AGENTS.md` 和 `common/rules/` 的前端项目，也能完成规则加载并输出真实、准确的审查协议确认句；契约检查能够定位入口引用的契约文件。

### 问题二 统一安装会覆盖同名审查技能

**影响：全栈项目可能丢失一端审查规范。建议优先处理。**

[project-onboarding/SKILL.md](../common/skills/project-onboarding/SKILL.md) 第 70 行允许单仓或 mono-repo 将前后端技能统一放入根 `common/skills/`。但后端与前端各有一个 `reviewer/SKILL.md`，且 frontmatter 名称同为 `reviewer`。

临时样例依次复制通用、后端、前端技能到同一目录后，源库的 34 份技能只剩 33 份。文件哈希比对确认，最终 reviewer 与前端版本相同，与后端版本不同。按此复制顺序，后端版本已被覆盖；交换顺序则会覆盖前端版本。

建议默认保留前后端独立技能目录，并让项目入口明确两份 reviewer 的实际路径。若继续支持统一根目录，需要先定义能够保留双方身份的路径或命名空间，并同步调整路由和校验规则。

验收标准：完整安装后仍保留 34 份源技能，两份 reviewer 均可单独定位；后端审查和前端审查分别加载正确版本。

### 问题三 基线脚本跳过来源歧义并返回成功

**影响：安装问题无法通过严格校验发现，造成错误的通过结论。应与安装方案同步修复。**

[verify-baseline.sh](../scripts/verify-baseline.sh) 第 44 行把含 `.document/` 的宿主目录优先归类为 root。第 59 至 65 行的 `find_fw` 在跨区域遇到同名技能时返回空结果。第 90 行将空结果统一解释为“framework 无，项目专有”，直接跳过。

在问题二的统一安装样例中，reviewer 被输出为“项目专有，跳过”。脚本只统计到 32 份一致技能，结构错误为 0，`--strict` 退出码仍为 0。脚本未区分“基线没有该技能”与“基线存在多个来源、当前布局无法消歧”。

建议将唯一匹配、无匹配和多来源匹配分别处理。来源歧义应计入结构错误，输出候选来源并返回非零。对于明确安装前后端规范的项目，还应检查各自必需的 reviewer 是否存在。

验收标准：前后端分层布局继续通过；统一目录内无法确认来源的 reviewer 明确失败，且提示前后端两个候选路径。

## 脚本实测记录

| 场景 | 样例构造 | 实际结果 | 判定 |
|---|---|---|---|
| 前后端分层安装 | 通用 13 份放根；后端 18 份放 apps/api；前端 3 份放 apps/web，各自使用 common/skills | 一致 34，漂移 0，结构错误 0，退出码 0 | 符合预期 |
| 前后端统一安装 | 通用、后端、前端顺序复制到根 common/skills | 实际仅 33 份；一致 32，reviewer 跳过，结构错误 0，退出码 0 | 未发现覆盖与来源歧义 |
| 流程技能漂移 | 在分层样例的 iteration-planner 末尾追加一行测试文本 | 一致 33，流程漂移 1，结构错误 0，退出码 1 | 符合预期 |

统一安装场景的关键输出：

```text
⊘  reviewer  framework 无 → 项目专有，跳过
✓ 一致 32   ℹ 项目专有差异 0   📌 项目覆写 0   Δ 流程漂移(需确认) 0   ✗ 结构错误 0
```

复现时可按以下步骤构造临时样例：

1. 复制通用技能、规则模板和文档骨架；为前后端建立标志目录及文件。
2. 将后端和前端技能分别安装到 `apps/api/common/skills/` 与 `apps/web/common/skills/`，运行严格校验，确认 34 份一致。
3. 在另一临时样例中把后端、前端技能依次合并进根 `common/skills/`，统计文件数量并比对 reviewer 哈希，再运行严格校验。
4. 在分层样例的一份流程技能末尾追加测试文本，确认严格校验返回非零。

所有覆盖和漂移操作均只针对临时副本。

## 修订顺序与复验要求

建议先统一入口与规则引用，消除仅有 AGENTS 入口时的执行障碍；再确定前后端技能的安装布局，避免同名文件覆盖；最后按该布局完善基线校验。三项修订均应保留既有的全文读取、审查、自证与授权门禁。

| 复验项 | 通过标准 |
|---|---|
| 仅有 AGENTS 入口 | 技能找到正确入口和规则，不要求读取不存在的 CLAUDE 文件 |
| 前后端技能身份 | 两份 reviewer 同时保留，路由到正确版本 |
| 基线校验 | 正常分层安装通过；来源歧义、必要技能缺失和流程漂移明确失败 |
| 项目迁移 | 整体移动或改名后，入口相对引用仍可解析 |
| 独立新会话 | 用“今天做什么”、真实开发、前端审查、后端审查及跨端契约请求核对实际读取行为 |
| 多模型与多宿主 | 分别记录入口加载、技能选择、规则执行和工具降级结果，不能由一个模型的结果推定全部通过 |

当前报告记录问题与修订方向，不包含上述修复。后续复验应以修订后的文件和真实新会话结果为依据。
