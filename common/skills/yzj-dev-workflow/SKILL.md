---
name: yzj-dev-workflow
description: >
  YZJ Framework 后端业务开发流程指南，覆盖 domain（核心业务）、integration（跨业务集成）、interfaces（api/sdk/grpc 接口）、support（横切扩展）四层架构的完整开发规范。
  当用户需要在基于 YZJ Framework + Spring Boot 3 + MyBatis-Flex 的项目中执行以下任务时触发此 Skill：新增业务实体的 CRUD 接口、编写 QueryChain 查询、创建跨业务 Flow、定义 gRPC 服务、集成 SDK、编写 Controller/Service/Operate/Query/DTO/VO、搭建新业务域。
  即使用户没有明确提到"YZJ 开发流程"，只要涉及基于 YZJ Framework 项目的业务代码编写，都应使用此 Skill 来确保遵循项目约定，并按需引用对应的 backend 子 skill。
---

# YZJ 业务开发流程指南

本 skill 是 YZJ Framework 后端开发的总入口。它**不重复**各个 backend 子 skill 的细节规范，而是负责：
1. 编码前的前置门禁
2. 完整研发流程的串联
3. 引导用户在恰当的时机使用对应的 backend skill
4. 编码后的自检与提交规范

> **细节规范请按需读取对应 backend skill**：`project-structure`、`model-conventions`、`service-conventions`、`controller-conventions`、`integration-flow`、`job`、`mybatis`、`cache`、`security`、`common`、`logging`、`database-design`、`grpc`、`tabledef`、`db-migration`、`financial`、`testing`、`reviewer`。
> 完整研发生命周期（含开发者门禁、进度台账、沉淀核对）由通用 skill `dev-session` 编排，本 skill 对应其 P3 后端路径。

> **加载方式**：本文件是主文件——读完全文后，按「路由表」只读本次需要的子文件与 backend skill；完整研发流程见 `dev-session`（12 阶段 + 门禁），本 skill 不再重复。

## 约束卡（本 skill 的硬门禁）

| 门禁 | 要求 | 细则 |
|------|------|------|
| **先过编码前置门禁** | 0.1 上游对齐（评审门禁 + 落档）、0.2 结构确认（适用规则已实际读取）、0.3 HIGH RISK 附加项全部满足才写业务代码；任一未满足停止并提示先完成 `pre-dev-alignment` | 下文第 0 节 |
| **逐文件自检 + 增量修改** | 每生成 / 修改一个文件输出前过 0.4 清单；已有文件只 Edit 必要行，禁止整体重写；改签名 / 删方法 / 改字段类型 = Breaking Change，列调用方等开发者确认 | 下文 0.4 |
| **四层边界** | `interfaces → integration → domain`，`support` 横切；domain 不反向依赖；跨域写操作只在 Flow，Flow 不碰 Mapper | 下文第 1、7 节 |
| **🔴 禁止事项零容忍** | 第 7 节 🔴 项任一命中即不得提交 | 下文第 7 节 |
| **编码后自检 → P4** | 按 `references/self-check.md` 自检后仍必过 `reviewer`（dev-session 规则 4） | `references/self-check.md` |

## 路由表（按本次需要只读对应子文件）

| 需要 | 必读 |
|------|------|
| 编码前（所有任务） | 下文第 0 节 + 第 1 节 |
| 按场景（A 新建 / B 旧项目新功能 / C 迭代）走步骤 | `references/scenario-steps.md` |
| 写代码时查命名 / 响应包装 / 分页 / 上下文 / 异常 / Controller 写法 | `references/conventions-quickref.md`，细则按第 8 节读对应 backend skill |
| 编码完成、进 P4 之前 | `references/self-check.md` |
| 想知道某件事该读哪个 backend skill | 下文第 8 节 |

---

## 0. 编码前置门禁

**在编写任何业务代码之前，必须确认以下条件已满足：**

### 0.1 上游对齐已完成

根据 `pre-dev-alignment` 完成的编码前文档与评审门禁，确认：

```
- [ ] 编码前评审门禁已通过：L2 技术设计文档经开发者技术审核 + 二次评估；L3 需求/调整文档经用户复核 + 技术设计文档经开发者审核
- [ ] 对齐结论已落档（需求文档→.document/plan/、技术设计文档→.document/design/ + STATUS.md 台账登记）
- [ ] 场景类型已确认（A 新项目 / B 旧项目新功能 / C 旧项目迭代）
- [ ] 风险等级已确认（LOW / HIGH）
- [ ] 涉及的业务域已确认
- [ ] 层归属已确认（domain / integration / interfaces / support）
- [ ] 接口类型已确认（api / sdk / grpc）
- [ ] 已查能力登记册（CAPABILITY.md），可复用能力已列入计划
```

**如果上述任一条件未满足，停止编码并提示用户先完成 `pre-dev-alignment`。**

### 0.2 编码前结构确认

按本次改动建立实际的规范对应关系，而不是只列技能名：转换与模型读取 `model-conventions` 第四节和同域转换类；业务码判断/赋值读取 `common` 第二节及目标枚举/常量；Java 注释读取 `reviewer` 第五节。技能入口链接到 references 时继续读相关正文。适用规则未读取，不算完成编码前确认。

```
- [ ] domain/{业务域}/ 包结构已确认（entity / mapper / service / model / enums / aid）
- [ ] 是否需要新建业务域（domain/{业务}/）
- [ ] 是否涉及跨业务 Flow（integration/business/{业务}/）
- [ ] Controller 路径已规划：/v{版本}/{平台}/{业务}/
- [ ] 是否需要新枚举（域内 enums/ vs 通用 common/enums/）
```

### 0.3 关键风险编码附加确认

如果 pre-dev-alignment 标记为 HIGH RISK：

```
- [ ] 跨业务写操作放在 Flow 中（禁止 Service 跨域写）
- [ ] Service 不直接操作其他业务域的 Mapper
- [ ] 涉及缓存：@CacheRead / @CachePut / @CacheEvict 的 key 已规划
- [ ] 涉及分布式锁：@DistributedLock 的 prefix + key 已规划
- [ ] 涉及鉴权：使用 SessionContext / SecurityToken 上下文
- [ ] 涉及敏感字段：已加 @Encryption 注解
- [ ] 涉及 DDL：TableDef 已按 `tabledef` skill 同步维护；迁移脚本在**用户显式要求时**按 `db-migration` 生成，未获要求则记录待办或走项目既有迁移机制（与 db-migration 触发约束一致）
- [ ] 涉及 proto：字段编号未复用（删除需 reserved）
- [ ] 涉及资金 / 金额：按 `financial` skill——BigDecimal、业务单号唯一索引 + 先查后写、@DistributedLock(transactional = true)、行锁 / 乐观锁、同事务流水
- [ ] 涉及安全关键词（auth / token / password / card / pan / permission）：按 `security` skill 第八节红线
- [ ] 涉及对外接口 / SDK / proto 变更：对接文档在同一次提交内更新
- [ ] 含敏感 payload 的接口：已加入 yzj.logger.ignore-request-url / ignore-response-url（`logging` skill 第九节）
```

### 0.4 编码中的逐文件自检与增量模式（强制）

**每生成 / 修改一个文件，输出前过一遍**（不攒到 `references/self-check.md` 第 5 节统一自检——那时返工成本已经翻倍）：

```
- [ ] 文件路径与包归属符合 project-structure（domain / integration / interfaces / support）
- [ ] 类名 / 方法名 / Operate / 枚举命名符合 `references/conventions-quickref.md` 第 3 节
- [ ] 转换已核对源/目标字段，优先显式 builder/setter；保留反射复制时有具体适用依据
- [ ] 类 Javadoc 有职责、真实 author/since；方法的参数、返回、边界契约完整，覆写例外已核对上游文档
- [ ] 业务编码复用已定义的枚举/常量；比较优先匹配的 isCode，赋值用 getCode，不写魔法值
- [ ] 无 System.out / printStackTrace / catch 空块 / ${} / RuntimeException 直抛
- [ ] Entity 继承 CommonEntity / CommonBusinessEntity；新增字段已同步 TableDef（tabledef skill）
- [ ] 敏感字段 @Encryption；金额 BigDecimal；时间类型与同域一致
- [ ] HIGH RISK 文件：0.3 对应项已满足
```

**增量模式**：

- 目标文件不存在 → 新建；**已存在 → 只改必要的行（Edit），禁止整体重写**——整体重写会抹掉他人改动与项目注释
- 修改**已有方法签名 / 删除方法 / 改字段类型** → 标注为 **Breaking Change**，Grep 全仓列出调用方并等开发者确认后再动；SDK / gRPC 契约变更同步 interfaces 层与对接文档
- 同一文件本次多处修改时，按"读全文 → 一次性列出改动点 → 逐处 Edit"执行，不边读边改

---

## 1. 架构概览（速查）

```
project/
├── {project}-common/        # 公共定义（稳定层）
├── {project}-grpc-api/      # gRPC 契约
└── {project}-server/        # 业务实现
    └── com.yeziji.{project}/
        ├── domain/          # 核心业务（按业务域垂直划分）
        ├── integration/     # 跨业务集成（Flow / Job / Listener / Initializer）
        ├── interfaces/      # 接口层（api / sdk / grpc）
        └── support/         # 横切扩展（configuration / annotation / aspect / utils）
```

**依赖方向**：`interfaces → integration → domain`，`support` 横切。**禁止 domain 反向依赖 interfaces / integration**。

> 详细架构与文件归属请读取 `project-structure` skill。

---

## 2. 标准开发流程（按场景）

见 `references/scenario-steps.md`：场景 A 新项目 / 全新业务域 12 步、场景 B 旧项目新功能、场景 C 旧项目迭代调整（影响面分析 → 外科手术式修改 → 回归 → 契约同步）。

---

## 3. 关键命名规范速查 / 4. 通用模式速查

见 `references/conventions-quickref.md`（类命名、Operate 动词在前、Service 方法前缀、API 路径；响应包装、分页链路、上下文获取、异常处理、record Controller）。详细规范按第 8 节读对应 backend skill。

---

## 5. 编码质量自检（编码后）

见 `references/self-check.md`（命名 / 层归属 / Model / 通用 Java 契约 / 查询与数据库 / 接口 / gRPC / 安全·金融·测试）。自检后仍须走 dev-session P4 reviewer 硬流程。

---

## 6. 完整研发流程

见 `dev-session`（12 阶段 + 门禁 + 全程规则）；编码中按关注点调用的 backend 技能见第 8 节。

---

## 7. 禁止事项总表

| # | 禁止事项 | 严重程度 | 关联 skill |
|---|----------|:--------:|-----------|
| 1 | Controller 中写业务逻辑 | 🔴 | controller-conventions |
| 2 | Service 跨域直接操作其他域的 Mapper | 🔴 | service-conventions |
| 3 | Service 处理跨业务域的写操作 | 🔴 | service-conventions / integration-flow |
| 4 | Flow 中直接操作 Mapper | 🔴 | integration-flow |
| 5 | domain 层依赖 interfaces / integration 层 | 🔴 | project-structure |
| 6 | 布尔变量以 `is` 开头（新代码） | 🔴 | reviewer / model-conventions |
| 7 | POJO 中存在无对应变量的 get/set | 🔴 | reviewer / model-conventions |
| 8 | proto 字段编号复用 | 🔴 | grpc |
| 9 | GrpcServiceImpl 中 `builder.setXxx(null)` | 🔴 | grpc |
| 10 | 使用 `@Builder` 替代 `@SuperBuilder`（有继承时） | 🟡 | model-conventions |
| 11 | 域专属枚举放在 common 中 | 🟡 | project-structure / common |
| 12 | 新增 Entity 后未同步创建 / 更新 TableDef | 🟡 | tabledef |
| 13 | support 包中放业务逻辑 | 🟡 | project-structure |
| 14 | Controller 不使用 record 类 | 🟡 | controller-conventions |
| 15 | API 路径无版本号 | 🟡 | controller-conventions |
| 16 | 自行创建 Page 类而非用 MyBatis-Flex 的 `Page` | 🔴 | service-conventions |
| 17 | DTO/VO 直接放在 `model/` 而非 `model/dto/`、`model/vo/` | 🟡 | model-conventions |
| 18 | 直接 `throw new RuntimeException(...)` 而非 `ApiException` | 🟡 | common |
| 19 | Operate 命名为 `{业务}{操作}Operate`（动词在后） | 🟡 | model-conventions |
| 20 | 金额用 double / `new BigDecimal(double)` / `==` 比较 | 🔴 | financial |
| 21 | 资金写操作无幂等、余额读-减-覆盖、变动不写流水 | 🔴 | financial |
| 22 | XML `${}` / 硬编码密钥 / MD5 存密码 / `Math.random` 生 token | 🔴 | security |
| 23 | 已存在文件整体重写；改方法签名不标 Breaking Change | 🟡 | 本 skill 0.4 |
| 24 | 对外接口 / SDK / proto 变更不同步对接文档 | 🔴 | reviewer #48 |

---

## 8. Skill 引用速查表

| 需要做的事 | 触发的 skill |
|------------|-------------|
| 在 YZJ 项目中确定文件该放哪个包 | `project-structure` |
| 创建 DTO / VO / Operate / Query | `model-conventions` |
| 编写 Service 方法（命名 + 职责边界） | `service-conventions` |
| 写复杂查询 / 链式查询 | `mybatis` + `service-conventions` |
| 编写 Controller（record 类 + 路径设计） | `controller-conventions` |
| 跨业务 Flow / 定时任务 / 事件监听 / 启动初始化 | `integration-flow` |
| 缓存读写 / 分布式锁 | `cache` |
| 定时任务 / 延时任务 / 广播 / 按商户并行（fanOut） | `job` |
| Token 鉴权 / OAuth / 上下文获取 | `security` |
| 用 ApiException、CommonResult、SessionContext、CommonEnum | `common` |
| 打日志 / 日志级别 / 敏感字段脱敏 | `logging` |
| 与开发者讨论新表 / 字段 / 索引设计（不生成 DDL） | `database-design` |
| 新增 Entity / 字段变更后维护 TableDef | `tabledef` |
| 生成 SQL 迁移脚本（up + down） | `db-migration` |
| 编写 proto / gRPC 服务 | `grpc` |
| 代码审查 / 规范检查 | `reviewer` |
| 一开始的需求对齐 | `pre-dev-alignment` |
| 修复/纠正后的同类问题回溯 | `similar-issue-sweep`（通用） |
| 金额 / 余额 / 支付 / 转账 / 结算 / 流水 / 幂等 | `financial` |
| 安全编码红线（持卡人数据 / 密码学 / 注入 / 越权 / SSRF） | `security` 第八节 |
| 编写 / 补齐单元测试 | `testing` |
| LoggerFilter 忽略清单 / 含敏感 payload 的接口 | `logging` 第九节 |
