# 项目架构分层与包结构

> 适用于基于 YZJ Framework + Spring Boot 3 + MyBatis-Flex 的 Java 后端项目。

---

## 一、模块总览

```
project/
├── {project}-common/        # 公共模块（稳定层，低频变动）
├── {project}-grpc-api/      # gRPC 契约模块（proto 定义 + Stub）
└── {project}-server/        # 服务模块（业务层，高频变动）
```

| 模块 | 定位 | 变动频率 |
|------|------|----------|
| `common` | 公共定义：枚举、常量、数据结构、配置、i18n、契约接口 | 低 |
| `grpc-api` | gRPC 契约：`.proto` 文件 + 编译生成的 Java Stub 类 | 低 |
| `server` | 业务实现：核心业务、基础设施、对外接口、横切支撑 | 高 |

---

## 二、Server 四层架构

```
com.yeziji.{project}/
│
├── Application.java
│
├── domain/                           # 核心业务层
│   ├── {业务域A}/
│   └── {业务域B}/
│
├── integration/                      # 集成层
│   ├── jobs/
│   ├── listener/
│   ├── initializer/
│   └── business/
│
├── interfaces/                       # 接口层
│   ├── api/                          #   外部 HTTP 接口
│   ├── sdk/                          #   内部 HTTP 接口
│   └── grpc/                         #   内部 gRPC 接口
│
└── support/                          # 扩展层（公用包）
    ├── configuration/
    ├── annotation/
    ├── validator/
    ├── aspect/
    └── utils/
```

### 架构分层图

```
┌─────────────────────────────────────────────────────┐
│                   interfaces 接口层                  │
│                  (api / sdk / grpc)                  │
├────────────────────────┬────────────────────────────┤
│                        ▼                            │
│               integration 集成层                     │
│      (jobs / listener / business / initializer)     │
├────────────────────────┬────────────────────────────┤
│                        ▼                            │
│                 domain 核心业务层                     │
│                  (按业务域垂直划分)                    │
└─────────────────────────────────────────────────────┘
                ← ← ← support 扩展层 → → →
                    (可被以上任意层引用)
```

### 层间依赖规则

```
interfaces → integration → domain
                              ↑
                           support (横切，可被任意层引用)
```

> **禁止反向依赖**：`domain` 不得依赖 `interfaces` 或 `integration`

---

## 三、domain — 核心业务层

凡涉及数据库操作（CRUD）的业务逻辑，均属于核心业务。

```
domain/
├── system/
│   ├── entity/                     # 数据库实体
│   │   └── table/                  # MyBatis-Flex TableDef（自动生成）
│   ├── mapper/                     # 数据访问层
│   │   └── queryChain/             # QueryChain 查询构造链
│   ├── service/                    # 业务服务接口
│   │   └── impl/                   # 业务服务实现
│   ├── model/                      # 数据传输对象
│   │   ├── dto/                    # 数据模型（内部传输）
│   │   ├── vo/                     # 视图模型（返回客户端）
│   │   ├── operate/                # 操作对象（增删改入参）
│   │   └── query/                  # 查询对象
│   ├── enums/                      # 域内枚举
│   └── aid/                        # 辅助转换类
│
└── user/
    ├── entity/
    ├── mapper/
    ├── service/
    │   └── impl/
    └── model/
```

### 命名规范

| 包 | 类命名规则 | 示例 |
|----|-----------|------|
| `entity` | `{业务}{表名}Entity` | `SystemPermissionEntity` |
| `entity/table` | `{业务}{表名}TableDef`（自动生成） | `SystemPermissionTableDef` |
| `mapper` | `{业务}{表名}Mapper`（自动生成） | `SystemPermissionMapper` |
| `service` | `{业务}{表名}Service` | `SystemPermissionService` |
| `service/impl` | `{业务}{表名}ServiceImpl` | `SystemPermissionServiceImpl` |
| `model` | `{业务}{描述}`（纯 POJO） | `SystemPermission` |
| `model/operate` | `{操作}{业务}Operate` | `AddUserOperate` |
| `model/query` | `{业务}{描述}Query` | `ElectronReleaseVersionInfoQuery` |
| `enums` | `{业务}{描述}Enum`（继承 CommonEnum） | `SystemPermissionTypeEnum` |
| `aid` | `{业务}{描述}ConvertAid` | `SystemPermissionConvertAid` |

---

## 四、integration — 集成层

编排跨业务流程、定时任务、事件监听等。不直接操作数据库，调用 `domain` 层的 Service。

```
integration/
├── jobs/                           # 定时任务
│   └── {描述}Job.java
├── listener/                       # 事件监听器
│   └── {描述}Listener.java
├── initializer/                    # 初始化器
│   └── {描述}Initializer.java
└── business/                       # 业务模块（按业务域细分）
    ├── auth/
    │   └── AuthLoginFlow.java
    └── db/
        └── PlatformClientRegisterCloudDbFlow.java
```

---

## 五、interfaces — 接口层

```
interfaces/
├── api/                            # 外部 HTTP 接口
│   ├── controller/
│   │   └── {版本}/{平台或应用}/     #   按版本+平台分层
│   │       └── {功能}Controller.java
│   └── configuration/
│
├── sdk/                            # 内部 HTTP 接口
│   ├── client/
│   ├── provider/
│   └── configuration/
│
└── grpc/                           # 内部 gRPC 接口
    └── impl/                       #   @GrpcService 实现类
        └── {业务}GrpcServiceImpl.java
```

### 三类接口区分

| 类型 | 协议 | 端口 | 用途 | 鉴权 |
|------|------|------|------|------|
| `api` | HTTP | 8080 | 外部客户端/第三方调用 | 完整鉴权（Token + 权限） |
| `sdk` | HTTP | 8080 | 内部微服务调用（HTTP） | 轻量鉴权（服务间签名/白名单） |
| `grpc` | gRPC | 9090 | 内部微服务调用（gRPC） | 无鉴权，网络层隔离 |

---

## 六、support — 扩展层

```
support/
├── configuration/                  # 服务配置
│   ├── mybatis/
│   ├── security/
│   │   └── component/              # 安全组件实现
│   ├── thread/
│   ├── cache/
│   ├── mq/
│   └── netty/
├── annotation/                     # 自定义注解
├── validator/                      # 校验器
├── adapter/                        # 适配器
├── aspect/                         # 切面
├── component/                      # 通用组件
├── model/                          # support 层模型
├── holder/                         # 持有者（静态引用）
├── base/                           # 基类
├── utils/                          # 服务级工具类
└── TableDefCollect.java            # TableDef 统一引用
```

---

## 七、Common 模块结构

```
com.yeziji.{project}.common/
├── enums/              # 通用枚举（被 2 个及以上业务引用）
├── constants/          # 通用常量
├── model/              # 通用数据结构
├── configuration/      # 通用配置
├── base/               # 基类
├── contract/           # 契约接口（SPI 定义，不放实现）
└── msg/                # i18n 异常信息枚举
```

> 新枚举默认放在 `domain/{业务}/enums/`。当被多个业务引用时，再提升到 `common/enums/`。

---

## 八、Resources 目录

```
resources/
├── application.yml                 # 主配置
├── application-dev.yml             # 开发环境
├── application-test.yml            # 测试环境
├── application-prod.yml            # 生产环境
├── logback.xml
├── dev/                            # 开发环境组件配置
│   ├── datasource.yml
│   ├── redis.yml
│   └── rabbitmq.yml
├── test/                           # 测试环境
├── prod/                           # 生产环境
├── mapper/                         # MyBatis XML（仅复杂 SQL）
└── permission/                     # 权限定义文件
```

---

## 九、文件归属速查表

| 我要创建的是... | 放在 | 示例 |
|----------------|------|------|
| 数据库实体 | `domain/{业务}/entity/` | `OrderEntity.java` |
| Mapper 接口 | `domain/{业务}/mapper/` | `OrderMapper.java` |
| QueryChain | `domain/{业务}/mapper/queryChain/` | `OrderQueryChain.java` |
| 业务 Service | `domain/{业务}/service/` | `OrderService.java` |
| 操作对象 | `domain/{业务}/model/operate/` | `AddOrderOperate.java` |
| 查询对象 | `domain/{业务}/model/query/` | `OrderQuery.java` |
| 通用模型 | `domain/{业务}/model/` | `OrderDetail.java` |
| DTO | `domain/{业务}/model/dto/` | `OrderInfoDTO.java` |
| VO | `domain/{业务}/model/vo/` | `OrderInfoVO.java` |
| 实体转换工具 | `domain/{业务}/aid/` | `OrderConvertAid.java` |
| 业务内枚举 | `domain/{业务}/enums/` | `OrderStatusEnum.java` |
| 对外 API 接口 | `interfaces/api/controller/{版本}/{平台}/` | `AdminOrderV1Controller.java` |
| 对内 SDK 接口 | `interfaces/sdk/provider/` | `OrderProvider.java` |
| 对内 gRPC 接口 | `interfaces/grpc/impl/` | `OrderGrpcServiceImpl.java` |
| 定时任务 | `integration/jobs/` | `OrderTimeoutJob.java` |
| 事件监听 | `integration/listener/` | `OrderCreatedListener.java` |
| 初始化逻辑 | `integration/initializer/` | `LoadPermissionInitializer.java` |
| 跨业务 Flow | `integration/business/{业务}/` | `OrderCreateFlow.java` |
| 框架配置 | `support/configuration/{功能}/` | `RedisConfiguration.java` |
| 自定义注解 | `support/annotation/` | `RequirePermission.java` |
| AOP 切面 | `support/aspect/` | `LogAspect.java` |
| 校验器 | `support/validator/` | `PhoneValidator.java` |
| 工具类 | `support/utils/` | `TreeBuildUtils.java` |
| 通用枚举 | `common/enums/` | `GenderEnum.java` |
| 通用常量 | `common/constants/` | `CacheKeyConstants.java` |
| i18n 错误信息 | `common/msg/` | `ExampleErrorMsg.java` |
| 契约接口 | `common/contract/` | `Initializer.java` |

---

## 十、新功能开发流程

```
1. 确定业务域
   ├── 已存在 → 在现有业务下添加
   └── 不存在 → 在 domain/ 下创建新业务包
          │
2. 创建 Entity（数据库实体）
          │
3. 生成 Mapper + TableDef（代码生成器）
          │
4. 创建 Service 接口 + Impl
          │
5. 是否需要数据转换？
   ├── 是 → 创建 Model + ConvertAid
   └── 否 → 跳过
          │
6. 创建接口
   ├── 给外部调用（HTTP）  → interfaces/api/controller/{版本}/{平台}/
   ├── 给内部调用（HTTP）  → interfaces/sdk/provider/
   └── 给内部调用（gRPC）  → interfaces/grpc/impl/
```

---

## 十一、禁止事项

1. Controller 中写业务逻辑
2. Service 跨域直接操作其他域的 Mapper（应通过对方域的 Service 接口调用）
3. domain 层依赖 interfaces 层（禁止反向依赖）
4. 把域专属枚举放在 common 中（未被多域共享的枚举留在域内）
5. 手动修改 `entity/table/` 下的 TableDef 文件（代码生成器自动生成）
6. 在 support 包中放业务逻辑（support 只放横切关注点）
