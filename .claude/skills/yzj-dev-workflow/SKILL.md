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

> **细节规范请按需读取对应 backend skill**：`project-structure`、`model-conventions`、`service-conventions`、`controller-conventions`、`integration-flow`、`mybatis`、`cache`、`security`、`common`、`logging`、`database-design`、`grpc`、`tabledef`、`db-migration`、`reviewer`。
> 完整研发生命周期（含开发者门禁、进度台账、沉淀核对）由通用 skill `dev-session` 编排，本 skill 对应其 P3 后端路径。

---

## 0. 编码前置门禁

**在编写任何业务代码之前，必须确认以下条件已满足：**

### 0.1 上游对齐已完成

根据 `pre-dev-alignment` 完成的开发计划，确认：

```
- [ ] 开发计划已写入并由用户 approve
- [ ] 对齐结论已落档（.document/plan/ 文档 + STATUS.md 台账登记）
- [ ] 场景类型已确认（A 新项目 / B 旧项目新功能 / C 旧项目迭代）
- [ ] 风险等级已确认（LOW / HIGH）
- [ ] 涉及的业务域已确认
- [ ] 层归属已确认（domain / integration / interfaces / support）
- [ ] 接口类型已确认（api / sdk / grpc）
- [ ] 已查能力登记册（CAPABILITY.md），可复用能力已列入计划
```

**如果上述任一条件未满足，停止编码并提示用户先完成 `pre-dev-alignment`。**

### 0.2 编码前结构确认

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
- [ ] 涉及 DDL：TableDef 已按 `tabledef` skill 同步维护，迁移脚本按 `db-migration` 生成
- [ ] 涉及 proto：字段编号未复用（删除需 reserved）
```

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

### 2.1 场景 A：新项目 / 全新业务域

```
1. 创建业务域包：domain/{业务}/
        ↓ 参考 project-structure
2. 定义 Entity（@Table，继承 CommonEntity）
        ↓
3. 创建 Mapper + 手动编写 TableDef（参考 `tabledef` skill）
   （在 support/TableDefCollect.java 中统一注册）
        ↓
4. 创建 Operate / Query / DTO / VO
        ↓ 参考 model-conventions
5. 编写 Service 接口 + ServiceImpl
        ↓ 参考 service-conventions（命名规约、QueryChain）
6. 如有复杂查询：编写 QueryChain
        ↓ 参考 mybatis（IQueryChain 链式查询）
7. 是否涉及跨业务写操作？
   ├── 是 → 创建 Flow（integration/business/{业务}/）
   │       参考 integration-flow
   └── 否 → 跳过
        ↓
8. 编写 Controller（record 类 + 构造注入）
        ↓ 参考 controller-conventions
9. 如有缓存需求：加 @CacheRead/@CachePut/@CacheEvict
        ↓ 参考 cache
10. 如有 gRPC：在 grpc-api 模块定义 proto，实现 GrpcServiceImpl
        ↓ 参考 grpc
11. 自检 + Code Review
        ↓ 参考 reviewer
```

### 2.2 场景 B：旧项目新功能

```
1. 阅读同业务域现有代码，确认命名/风格
        ↓
2. 按场景 A 的步骤执行
        ↓
3. 保持与现有代码的一致性（不引入差异）
```

### 2.3 场景 C：旧项目迭代调整

```
1. 影响面分析（受影响的 Service/Controller/Flow/Mapper/QueryChain）
        ↓
2. 外科手术式修改（只改必要的，不顺手重构）
        ↓
3. 回归测试（覆盖被改动方法的调用链）
        ↓
4. 如涉及接口签名变更：检查 SDK / gRPC stub 是否需要同步
```

---

## 3. 关键命名规范速查

> 详细规范请读取对应 backend skill。

### 3.1 类命名

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| Entity | `{业务}{表名}Entity` | `SystemPermissionEntity` |
| Mapper | `{业务}{表名}Mapper` | `SystemPermissionMapper` |
| Service | `{业务}{表名}Service` | `SystemPermissionService` |
| ServiceImpl | `{业务}{表名}ServiceImpl` | `SystemPermissionServiceImpl` |
| Operate（增删改入参） | `{操作}{业务}Operate` | `AddUserOperate`、`UpdateUserOperate` |
| Query（查询入参） | `{业务}{描述}Query` | `UserInfoQuery` |
| DTO（数据传输） | `{业务}{描述}DTO` | `UserInfoDTO` |
| VO（视图模型） | `{业务}{描述}VO` | `UserInfoVO` |
| QueryChain | `{业务}{描述}QueryChain` | `CustomerInfoQueryChain` |
| Flow | `{业务描述}Flow` | `AuthLoginFlow` |
| Controller | `{平台}{业务}{版本}Controller` | `AdminAuthV1Controller` |
| ConvertAid | `{业务}{描述}ConvertAid` | `SystemPermissionConvertAid` |
| Enum | `{业务}{描述}Enum` | `SystemPermissionTypeEnum` |
| Initializer | `{描述}Initializer` | `LoadPermissionInitializer` |
| Job | `{描述}Job` | `OrderTimeoutJob` |
| Listener | `{描述}Listener` | `DataMessageConfirmListener` |

### 3.2 Operate 命名规范（与 KPay 同源）

**操作动词在前，业务名在后**：

```
✓ AddUserOperate            ✗ UserAddOperate
✓ UpdateUserOperate         ✗ UserUpdateOperate
✓ RemoveUserOperate         ✗ UserRemoveOperate
```

### 3.3 Service 方法命名

| 操作 | 前缀 | 示例 |
|------|------|------|
| 获取单个 | `get` | `getDtoById()` |
| 获取列表 | `get...List` | `getDtoListByQuery()` |
| 获取分页 | `get...Page` | `getDtoPageByQuery()` |
| 统计 | `statistics` | `statisticsUserCount()` |
| 新增 | `add` | `add(AddUserOperate operate)` |
| 修改 | `update` | `update(UpdateUserOperate operate)` |
| 删除 | `remove` | `removeById(Long id)` |

### 3.4 API 路径规范

```
格式：/{版本}/{平台或应用}/{业务路径}
示例：/v1/admin/auth/login
      /v1/open/db/datasource
      /v2/admin/application/version

平台：admin（管理后台）、open（开放平台）、merchant（商户）等
```

---

## 4. 通用模式速查

### 4.1 响应包装

```java
// 成功（无数据）
return CommonResult.success();

// 成功（带数据）
return CommonResult.success(data);

// 成功（分页）
return CommonResult.successPage(page);  // Page<T> 自动转 CommonPage<T>

// 失败
throw new ApiException(SomeErrorMsg.XXX);  // 优先用 ApiException，不直接 return failed
```

### 4.2 分页查询链路

```
Service 层返回 Page<T>（com.mybatisflex.core.paginate.Page）
   ↓
Controller 层用 CommonResult.successPage(page) 自动转换为 CommonPage<T>
```

**禁止自行创建 Page 类**。

### 4.3 上下文获取

```java
// 获取当前登录用户
Long userId = SessionContext.getUserDetailsAttribute(IUserDetails::getUserId);

// 获取当前租户
Long tenantId = SessionContext.getTenantAttribute(TenantInfo::getTenantId);

// 获取 IP
String ip = SessionContext.getServletInfoAttribute(ServletInfo::getIp);
```

### 4.4 异常处理

```java
// 业务异常统一使用 ApiException
throw new ApiException(UserErrorMsg.USER_NOT_FOUND);

// 禁止
throw new RuntimeException("...");
```

### 4.5 Controller 写法（record + 构造注入）

```java
@RestController
@RequestMapping("/v1/admin/user")
public record AdminUserV1Controller(UserService userService) {

    @PostMapping("/page")
    public CommonResult<CommonPage<UserVO>> page(@RequestBody UserInfoQuery query) {
        return CommonResult.successPage(userService.getDtoPageByQuery(query));
    }
}
```

---

## 5. 编码质量自检（编码后）

编码完成后，在提交前执行以下自检（详细规则参考 `reviewer` skill）：

### 5.1 命名规范自检

```
- [ ] 类名 UpperCamelCase，抽象类以 Base 开头，异常以 Exception 结尾
- [ ] 方法名/变量名 lowerCamelCase
- [ ] 常量名 UPPER_SNAKE_CASE
- [ ] 布尔变量不以 is 开头（新代码）
- [ ] Controller 用 record 类，命名 {平台}{业务}{版本}Controller
- [ ] Operate 命名为 {操作}{业务}Operate（动词在前）
- [ ] 枚举以 Enum 结尾，继承 CommonEnum
```

### 5.2 层归属自检

```
- [ ] Controller 不含业务逻辑（只校验入参、调用 Service/Flow、包装返回）
- [ ] Service 不跨业务域写操作（应在 Flow 中）
- [ ] Service 不直接操作其他业务域的 Mapper
- [ ] Flow 不直接操作 Mapper（通过 Service）
- [ ] domain 不依赖 interfaces 或 integration
- [ ] 业务专属枚举留在 domain/{业务}/enums/，不放 common/enums/
- [ ] support 包不含业务逻辑
```

### 5.3 Model 自检

```
- [ ] DTO 在 model/dto/，VO 在 model/vo/，Operate 在 model/operate/，Query 在 model/query/
- [ ] Operate 继承 CommonOperate，Query 继承 CommonQuery<T>
- [ ] 有继承关系的类用 @SuperBuilder（不用 @Builder）
- [ ] @EqualsAndHashCode(callSuper = true) 已添加（有继承时）
- [ ] POJO 不存在无对应变量的 getXxx/setXxx 方法
- [ ] 枚举字段使用 @see 引用枚举类
```

### 5.4 查询与数据库自检

```
- [ ] 优先使用 QueryChain（仅在 QueryChain 无法表达时用 XML）
- [ ] TableDef 通过 TableDefCollect 引用
- [ ] 敏感字段已加 @Encryption
- [ ] 新增 / 变更字段已同步到手写 TableDef，并注册到 TableDefCollect（参考 `tabledef` skill）
```

### 5.5 接口自检

```
- [ ] Controller 路径含版本号 /v{n}/
- [ ] Controller 用 record 类 + 构造注入
- [ ] 返回值使用 CommonResult<T> 包装
- [ ] 分页用 CommonResult.successPage(page)
- [ ] @Valid 校验已加在合适的入参上
```

### 5.6 gRPC 自检（如适用）

```
- [ ] proto 文件 snake_case 命名
- [ ] message/service/enum 命名规范
- [ ] 字段编号未复用（删除字段需 reserved）
- [ ] GrpcServiceImpl 使用 DataUtils.setIfNotNull（避免 setXxx(null) 异常）
```

---

## 6. 完整研发流程总览

```
┌──────────────────────────────────────────────────────────────────┐
│                  YZJ Framework 后端开发完整流程                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  需求输入                                                        │
│    ↓                                                             │
│  pre-dev-alignment ─→ 场景分类 + 风险检测 + 开发计划              │
│    ↓                                                             │
│  yzj-dev-workflow ──→ 编码前门禁                                  │
│    ↓                                                             │
│  按场景执行编码（A/B/C），过程中按需调用 backend skill：           │
│                                                                  │
│    ├── project-structure    → 文件归属决策                       │
│    ├── model-conventions    → DTO/VO/Operate/Query              │
│    ├── service-conventions  → Service 方法命名 + 职责边界        │
│    ├── controller-conventions → Controller 编写                  │
│    ├── integration-flow     → 跨业务 Flow / Job / Listener      │
│    ├── mybatis              → QueryChain 查询构建                │
│    ├── cache                → 缓存注解 + 分布式锁                │
│    ├── security             → 鉴权 + Token 上下文                │
│    ├── common               → CommonResult / ApiException / 枚举│
│    ├── logging              → 日志规范 + 敏感字段脱敏            │
│    ├── database-design      → 数据库设计建议（不生成 DDL）       │
│    └── grpc                 → proto 定义 + GrpcServiceImpl       │
│                                                                  │
│    ↓                                                             │
│  编码质量自检（本 skill 第 5 节）                                 │
│    ↓                                                             │
│  reviewer skill ──→ Code Review                                  │
│    ↓                                                             │
│  合并上线                                                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**关键控制点**：
1. 计划必须在编码前确认，禁止先编码再补计划
2. 关键风险模块全程附加检查
3. 每个人工确认节点都不可跳过
4. AI 负责产出，人工负责评审和决策

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
