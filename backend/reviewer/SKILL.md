---
name: code-reviewer
description: 代码审查 skill，用于对 Java 代码进行规范审查。当用户要求 review 代码、审查代码规范、检查代码质量问题、要求优化代码时使用此 skill。审查范围包括：命名规范、代码格式、OOP 规范、注释规范、项目结构规范、Proto3 编写规范等。
---

# 代码审查规范

本 skill 用于对 Java 代码进行规范审查，确保代码符合项目制定的开发规范。

## 一、审查维度概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         代码审查维度                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 命名规范与约束        - 类名、方法名、变量名、常量名、枚举命名  │
│  2. 代码格式              - 大括号、缩进、单行长度、空格规范        │
│  3. OOP 规范与约束        - 覆写注解、静态访问、接口过时处理       │
│  4. 代码注释              - 类注释、方法注释、参数注释、返回注释     │
│  5. 数据转换              - convert 方法、ConvertAid 辅助类        │
│  6. Service 层规范        - 方法命名、跨业务处理                   │
│  7. 项目结构规范          - 分层架构、包结构、文件归属              │
│  8. Proto3 编写规范       - message、service、enum 编写规范        │
└─────────────────────────────────────────────────────────────────┘
```

## 二、命名规范审查

### 2.1 类名规范

| 检查项 | 规范要求 | 正确示例 | 错误示例 |
|--------|----------|----------|----------|
| 类名格式 | UpperCamelCase | `UserService`, `OrderDTO` | `userService`, `user_service` |
| 抽象类 | Base 开头 | `BaseInitializer` | `AbstractUserService` |
| 异常类 | Exception 结尾 | `BusinessException` | `BusinessError` |
| 测试类 | 以测试类名开头，Tests 结尾 | `UserServiceTests` | `TestUserService` |
| 枚举类 | Enum 后缀 | `StatusEnum` | `Status`, `StatusType` |

### 2.2 方法名与变量名

| 检查项 | 规范要求 | 正确示例 | 错误示例 |
|--------|----------|----------|----------|
| 方法名/参数名/变量名 | lowerCamelCase | `getUserById`, `userName` | `GetUserById`, `user_name` |
| 常量名 | 全大写+下划线 | `MAX_RETRY_COUNT` | `maxRetryCount`, `MAX_RETRY` |
| 布尔变量 | 禁止 is 开头 | `enabled`, `deleted` | `isEnabled`, `isDeleted` |

### 2.3 POJO 类方法名约束

**检查项**：如果 POJO 类中不存在某个变量，禁止定义 `getXxx`/`setXxx` 方法。

**原因**：在 Redis / RPC 序列化与反序列化过程中会导致异常。

```java
// 错误示例：不存在 isEnabled 变量但定义了 getIsEnabled 方法
public class UserDTO {
    private String name;
    
    // 禁止这样定义
    public Boolean getIsEnabled() {
        return true;
    }
}

// 正确示例
public class UserDTO {
    private Boolean enabled;
    
    public Boolean getEnabled() {
        return enabled;
    }
}
```

### 2.4 数据转换方法命名

| 场景 | 规范要求 | 示例 |
|------|----------|------|
| POJO 内转换方法 | convert 开头 | `convertToUserInfoVo()` |
| 被多处引用的转换 | 单独定义 ConvertAid 类 | `UserInfoConvertAid` |

**ConvertAid 类命名规则**：`{业务}{描述}ConvertAid`

```java
// 正确示例
public class UserInfoConvertAid {
    public UserRoleInfoVO convertToUserRoleInfoVo(UserRolePermissionDTO dto) {
        // 转换逻辑
    }
}
```

### 2.5 Service 层方法命名

| 操作类型 | 命名规则 | 示例 |
|----------|----------|------|
| 获取单个 | get 前缀 | `getDtoById()` |
| 获取多个 | getxxxList 前缀 | `getDtoListByQuery()` |
| 获取统计值 | statistics 前缀 | `statisticsUserCount()` |
| 插入 | add 前缀 | `add(UserDTO dto)` |
| 删除 | remove 前缀 | `removeById()` |
| 修改 | update 前缀 | `update(UserDTO dto)` |

## 三、代码格式审查

### 3.1 大括号规范

```java
// 空代码块：简洁写成 {}
public void emptyMethod() {}

// 非空代码块
public void nonEmptyMethod() {
    if (condition) {
        doSomething();
    } else {
        doOtherthing();
    }
}
```

### 3.2 单行字符数

- **限制**：单行字符数不超过 120 个
- **换行规则**：
  - 第二行相对第一行缩进 4 个空格
  - 方法调用点号与下文一起换行
  - 多个参数需换行时在逗号后进行

```java
// 正确示例：参数换行
List<UserDTO> userList = userService.getDtoListByQuery(
    UserQuery.builder()
        .name("张三")
        .status(1)
        .build()
);

// 正确示例：方法链换行
List<String> names = userList.stream()
    .map(UserDTO::getName)
    .filter(Objects::nonNull)
    .toList();
```

### 3.3 运算符与空格

- 运算符与下文一起换行
- 方法参数定义和传入时，逗号后加空格

```java
// 正确
public void method(int param1, int param2) {
    int result = value1
        + value2
        - value3;
}
```

## 四、OOP 规范审查

### 4.1 覆写方法必须加 @Override

```java
// 正确
@Override
public void doSomething() {
}

// 错误
public void doSomething() {
}
```

### 4.2 静态访问规范

**检查项**：外部访问静态变量或静态方法时，必须用类名直接访问，禁止通过对象引用。

```java
// 正确
int count = UserEntity.CACHE_EXPIRE_SECONDS;
String result = StringUtils.trimToEmpty(value);

// 错误
UserEntity entity = new UserEntity();
int count = entity.CACHE_EXPIRE_SECONDS;  // 禁止通过对象访问
```

### 4.3 接口过时处理

- 外部正在调用或二方库依赖的接口，**禁止修改方法签名**
- 过时接口必须加 `@Deprecated` 注解，并说明新接口或新服务

```java
/**
 * @deprecated 请使用 {@link #getNewUserById(Long)} 方法
 */
@Deprecated
public UserDTO getUserById(Long id) {
    return getNewUserById(id);
}
```

### 4.4 this 与 super 调用规范

| 调用类型 | 规范要求 | 正确示例 | 错误示例 |
|----------|----------|----------|----------|
| 调用自身方法 | 必须使用 this | `this.doSomething()` | `doSomething()` |
| 调用父类方法 | 必须使用 super | `super.parentMethod()` | `this.parentMethod()` |

```java
public class UserServiceImpl extends BaseServiceImpl {
    
    public void process() {
        // 调用当前类方法：必须用 this
        this.doSomething();
        
        // 调用父类方法：必须用 super
        super.init();
    }
}
```

### 4.5 可变参数规范

- 相同参数类型、相同业务含义才可使用可变参数
- 可变参数必须放置在参数列表**最后**
- 避免使用 Object

```java
// 正确
public void addUsers(String name, Long... ids) {
}

// 错误：可变参数不在最后
public void addUsers(Long... ids, String name) {
}
```

### 4.6 Object equals 调用

**检查项**：使用 Object 的 equals 方法容易抛空指针异常，应使用常量或确定有值的对象来调用。

```java
// 正确：使用常量调用 equals
if ("ADMIN".equals(role)) {
}

// 错误：对象调用 equals 可能抛 NPE
if (role.equals("ADMIN")) {
}
```

### 4.7 Service 层职责规范

#### 4.7.1 核心原则

| 操作类型 | Service 层规范 | 说明 |
|----------|----------------|------|
| **单表写操作（增/删/改）** | ✅ 允许在 Service 层直接处理 | 如：`add()`, `update()`, `removeById()` |
| **单表查询操作** | ✅ 允许在 Service 层直接处理 | 如：`getById()`, `getListByQuery()` |
| **跨业务/跨表写操作** | ❌ 禁止在 Service 层处理 | 应在 integration 层 Flow 中处理 |
| **跨业务/跨表查询** | ⚠️ 特殊情况可允许 | 仅限业务必需且无法拆分的情况 |

#### 4.7.2 正确示例

**场景 1：单表操作 ✅**

```java
// UserService 中处理用户自身的增删改查
public class UserServiceImpl implements UserService {
    
    @Resource
    private UserMapper userMapper;
    
    @Override
    public void add(AddUserOperate operate) {
        // 验证用户名唯一性（单表查询）
        UserEntity existUser = userMapper.selectOne(
            UserEntity::getUsername, operate.getUsername()
        );
        if (existUser != null) {
            throw new BusinessException("用户名已存在");
        }
        
        // 单表插入
        UserEntity entity = UserConvertAid.convertToEntity(operate);
        userMapper.insert(entity);
    }
}
```

**场景 2：跨业务操作需要 Flow ✅**

```java
// integration 层 Flow：处理用户注册 + 角色分配 + 发送通知
public class UserRegisterFlow {
    
    @Resource
    private UserService userService;
    @Resource
    private RoleService roleService;
    @Resource
    private NotificationService notificationService;
    
    public void register(UserRegisterOperate operate) {
        // 1. 创建用户（调用 UserService 单表操作）
        userService.add(operate);
        
        // 2. 分配角色（调用 RoleService 单表操作）
        roleService.assignRoles(operate.getUserId(), operate.getRoleIds());
        
        // 3. 发送通知（跨系统操作）
        notificationService.sendWelcome(operate.getUserId());
    }
}
```

#### 4.7.3 错误示例

```java
// ❌ 错误：Service 中处理跨业务写操作
public class UserServiceImpl implements UserService {
    
    @Resource
    private UserMapper userMapper;
    @Resource
    private OrderService orderService;  // 禁止引入其他业务域 Service
    @Resource
    private AccountService accountService;  // 禁止引入
    
    @Override
    public void register(UserRegisterOperate operate) {
        // 1. 保存用户
        userMapper.insert(this.convertToEntity(operate));
        
        // 2. 创建账户（跨域操作不应在 UserService 中）
        accountService.createAccount(operate.getUserId());
        
        // 3. 创建初始订单（跨域操作不应在 UserService 中）
        orderService.createInitOrder(operate.getUserId());
    }
}
```

```java
// ❌ 错误：Service 中处理跨表写操作
public class OrderServiceImpl implements OrderService {
    
    @Resource
    private OrderMapper orderMapper;
    @Resource
    private OrderItemMapper orderItemMapper;  // 禁止直接操作其他表的 Mapper
    
    @Override
    public void add(OrderAddOperate operate) {
        // 在 OrderService 中直接操作 order_item 表
        OrderEntity order = this.convertToEntity(operate);
        orderMapper.insert(order);
        
        // 跨表插入 order_item - 应该在 OrderService 中通过调用 OrderItemService 处理
        for (OrderItemOperate item : operate.getItems()) {
            OrderItemEntity itemEntity = itemConvert.toEntity(item);
            orderItemMapper.insert(itemEntity);  // 禁止直接操作
        }
    }
}
```

#### 4.7.4 QueryChain 查询链规范

**规范**：使用代码实现（QueryChain）进行 SQL 构建，不使用 Mapper XML 或注解。仅在复杂增删改场景下才使用 XML。

##### 4.7.4.1 QueryChain 包结构与命名

```
domain/{业务域}/
└── mapper/
    └── queryChain/
        └── {业务名}QueryChain.java    // 如 CustomerInfoQueryChain
```

**命名规则**：`{业务名}QueryChain`

##### 4.7.4.2 TableDef 统一引用

通过 `TableDefCollect` 类统一引用所有 TableDef，避免分散引入：

```java
import com.yeziji.{project}.support.TableDefCollect;

// 使用 TableDefCollect 中的静态常量
TableDefCollect.{表名}
```

##### 4.7.4.3 QueryChain 实现示例

```java
package com.yeziji.{project}.domain.{业务域}.mapper.queryChain;

import com.mybatisflex.core.query.If;
import com.yeziji.mybatis.IQueryChain;
import com.yeziji.{project}.domain.{业务域}.entity.{Entity}Entity;
import com.yeziji.{project}.domain.{业务域}.model.dto.{Entity}DTO;
import com.yeziji.{project}.domain.{业务域}.model.query.{Entity}Query;

import static com.yeziji.{project}.support.TableDefCollect.*;
import static com.yeziji.{project}.domain.{业务域}.entity.table.{Entity}TableDef.{表名};

/**
 * {业务描述}查询构造链
 *
 * @author hwy
 * @since 2026/03/21
 **/
public class {Business}QueryChain {

    /**
     * 获取DTO查询构造链
     *
     * @param query 查询条件
     * @return {@link IQueryChain} 查询构造器
     */
    public static IQueryChain<{Business}DTO, {Entity}Entity> getDtoQueryChain({Business}Query query) {
        return getDtoQueryChainBase(query)
                .select(TableDefCollect.{ENTITY}.DEFAULT_COLUMNS)
                // 添加关联查询字段
                .leftJoin(关联Entity.class)
                .on(queryWrapper ->
                        queryWrapper.where(关联Entity::getId).eq({Entity}Entity::getXxxId)
                                .and(关联Entity::getMerchantId).eq({Entity}Entity::getMerchantId)
                )
                .defaultOrderDescBy({Entity}Entity::getCreateTime);
    }

    /**
     * 获取基础查询构造链
     *
     * @param query 查询条件
     * @return {@link IQueryChain} 查询构造器
     */
    private static IQueryChain<{Business}DTO, {Entity}Entity> getDtoQueryChainBase({Business}Query query) {
        return IQueryChain.of(query, {Entity}Entity.class)
                .commonWrappers({Entity}Entity::getName, {Entity}Entity::getAbbreviation)
                .where({Entity}Entity::getStatus).eq(query.getStatus(), If::notNull)
                .and({Entity}Entity::getRemark).like(query.getRemark(), If::notNull);
    }
}
```

##### 4.7.4.4 QueryChain 常用方法

| 方法 | 说明 | 示例 |
|------|------|------|
| `IQueryChain.of(query, Entity.class)` | 创建查询链 | 初始化查询构造器 |
| `.select(TableDef.DEFAULT_COLUMNS)` | 选择默认列 | 实体所有字段 |
| `.select(Entity::getField)` | 选择特定字段 | 单个字段或多个 |
| `.leftJoin(Entity.class)` | 左连接 | 关联表 |
| `.on(queryWrapper -> ...)` | 连接条件 | `where(...).eq(...).and(...)` |
| `.where(Entity::getField).eq(value)` | 条件等于 | Eq.eq() |
| `.where(Entity::getField).like(value, If::notNull)` | 模糊查询 | 条件成立才拼接 |
| `.commonWrappers(...fields)` | 通用模糊查询 | 支持多字段 OR 匹配 |
| `.defaultOrderDescBy(Entity::getField)` | 默认降序排序 | 创建时间等 |
| `.list().convertTo(Target.class)` | 查询并转换 | 返回 VO/DTO |

##### 4.7.4.5 XML 使用场景

```xml
<!-- 仅在复杂的多表关联、动态 SQL、批量操作等场景使用 XML -->
<!-- 一般单表和简单跨表查询必须使用 QueryChain -->
```

**总结**：
- **Service 层禁止**：跨业务域调用、跨表写操作（INSERT/UPDATE/DELETE 其他表）
- **Service 层允许**：单表 CRUD、跨表查询（通过 QueryChain）
- **integration 层负责**：多业务协同、跨业务写操作、事务协调
- **QueryChain 为首选**：一般查询必须使用 QueryChain，XML 仅用于复杂 SQL
- **TableDef 引用**：统一通过 `TableDefCollect` 类引用

## 五、代码注释规范

### 5.1 类注释模板

```java
/**
 * 加载权限初始化
 *
 * @author hwy
 * @since 2026/01/01 01:58
 **/
public class LoadPermissionInitializer {
}
```

### 5.2 方法注释规范

```java
/**
 * 同步商户用户数据
 * 
 * <p>同时会优先同步角色数据，保留角色与用户的关联关系</p>
 *
 * @param merchantIds 商户 ID 列表
 * @return 是否同步成功: true 成功, false 失败
 */
public boolean syncMerchantUserData(List<Long> merchantIds) {
}
```

**覆写接口实现方法**：不需要重复描述功能

```java
// interface 中需要完整注释
/**
 * 同步商户用户数据
 *
 * @param merchantIds 商户 ID 列表
 * @return 是否同步成功
 */
boolean syncMerchantUserData(List<Long> merchantIds);

// impl 中覆写不需要重复描述
@Override
public boolean syncMerchantUserData(List<Long> merchantIds) {
}
```

### 5.3 代码逻辑注释

```java
public boolean compareAndMergePermission() {
    // 加载文件的权限
    List<SystemPermission> newPermissions = this.loadPermission();
    
    // 扁平化聚合的数据
    SelfAssociationAid<SystemPermission> selfAssociationAid = new SelfAssociationAid<>(newPermissions);
    
    // TODO：数据合并
    // FIXME：可能需要改造为 type 和 key 才是唯一的
}
```

### 5.4 注释格式要求

- 双斜线与注释内容之间有且仅有一个空格
- 注释前后需要空行

```java
// 正确
public void method() {
    
    // 设置用户名称
    user.setName("张三");
    
    // 保存用户
    this.save(user);
}

// 错误：缺少空格
public void method() {
    //设置用户名称
    user.setName("张三");
}
```

## 六、项目结构规范

### 6.1 模块结构

```
{project}/
├── {project}-common/        # 公共模块
├── {project}-grpc-api/      # gRPC 契约模块
└── {project}-server/        # 服务模块
```

### 6.2 Server 分层架构

```
com.yeziji.{project}/
├── domain/                  # 核心业务层（按业务域垂直切分）
│   └── {业务域}/
│       ├── entity/         # 数据库实体
│       ├── mapper/         # 数据访问层
│       ├── service/        # 业务服务接口
│       │   └── impl/      # 业务服务实现
│       ├── model/         # 数据传输对象（DTO/VO/Query）
│       ├── enums/         # 域内枚举
│       └── aid/          # 辅助转换类
│
├── integration/            # 集成层
│   ├── jobs/              # 定时任务
│   ├── listener/          # 事件监听器
│   └── business/          # 业务模块（Flow）
│
├── interfaces/            # 接口层
│   ├── api/               # 外部 HTTP 接口
│   │   └── controller/   # 控制器
│   ├── sdk/               # 内部 HTTP 接口
│   │   ├── client/       # 接口定义
│   │   └── provider/     # 接口实现
│   └── grpc/              # 内部 gRPC 接口
│       └── service/      # @GrpcService 实现类
│
└── support/               # 扩展层
    ├── configuration/    # 服务配置
    ├── annotation/       # 自定义注解
    ├── validator/        # 校验器
    ├── adapter/          # 适配器
    ├── aspect/           # 切面
    └── utils/            # 服务工具类
```

### 6.3 层间依赖规则

```
interfaces → integration → domain
                          ↑
                       support (横切，可被任意层引用)
```

**禁止反向依赖**：domain 不得依赖 interfaces 或 integration

### 6.4 Controller 职责

**检查项**：Controller 只做参数校验、调用 Service、返回结果，禁止编写业务逻辑。

```java
@RestController
@RequestMapping("/api/v1/system/permission")
public class SystemPermissionController {
    
    @Resource
    private SystemPermissionService systemPermissionService;
    
    // 只做：参数校验 → 调用 Service → 返回结果
    // 禁止在 Controller 中编写业务逻辑
    @GetMapping("/{id}")
    public UserDTO getById(@PathVariable Long id) {
        return systemPermissionService.getDtoById(id);
    }
}
```

## 七、Proto3 编写规范

### 7.1 基本规范

| 检查项 | 规范要求 |
|--------|----------|
| 文件命名 | snake_case，如 `platform_client_datasource.proto` |
| message 命名 | UpperCamelCase，如 `PlatformClientDatasourceMessage` |
| 字段命名 | snake_case，如 `client_code` |
| enum 值命名 | UPPER_SNAKE_CASE，如 `DATA_CENTER` |
| 字段编号 | 不得复用，删除后用 `reserved` 保留 |

### 7.2 枚举规范

- 枚举首个值必须为 0
- 命名惯例：`{枚举名}_UNSPECIFIED = 0`

```protobuf
enum ClientType {
    CLIENT_TYPE_UNSPECIFIED = 0;
    DATA_CENTER = 1;
    ERP_HEADQUARTERS = 2;
}
```

### 7.3 GrpcServiceImpl 规范

**检查项**：
- 必须使用 `@GrpcService` 注解
- 必须继承 `{ServiceName}Grpc.{ServiceName}ImplBase`
- Entity 转 proto Message 必须使用 `DataUtils.setIfNotNull` 进行 null 安全赋值
- 调用顺序：`responseObserver.onNext(...)` → `responseObserver.onCompleted()`

```java
@GrpcService
public class PlatformClientDatasourceGrpcServiceImpl
        extends PlatformClientDatasourceServiceGrpc.PlatformClientDatasourceServiceImplBase {

    private PlatformClientDatasourceMessage convertToProtoMessage(PlatformClientDatasourceEntity entity) {
        PlatformClientDatasourceMessage.Builder builder = PlatformClientDatasourceMessage.newBuilder();
        DataUtils.setIfNotNull(entity.getId(), builder::setId);
        DataUtils.setIfNotNull(entity.getType(), builder::setType);
        return builder.build();
    }
}
```

## 八、禁止事项

以下行为在代码审查中将直接判定为**不通过**：

| 序号 | 禁止事项 | 说明 |
|------|----------|------|
| 1 | Controller 中写业务逻辑 | Controller 只做参数校验、调用 Service、返回结果 |
| 2 | Service 跨域直接操作其他域的 Mapper | 应通过对方域的 Service 接口调用 |
| 3 | domain 层依赖 interfaces 层 | 禁止反向依赖 |
| 4 | 把域专属枚举放在 common 中 | 未被多域共享的枚举留在域内 |
| 5 | 手动修改 entity/table/ 下的文件 | 这些由代码生成器自动生成 |
| 6 | 在 support 包中放业务逻辑 | support 只放横切关注点 |
| 7 | POJO 类中存在 get/set 但不存在对应变量 | 导致序列化/反序列化异常 |
| 8 | 布尔变量以 is 开头 | 导致序列化/反序列化异常 |
| 9 | proto 文件字段编号复用 | 删除字段后必须用 reserved |

## 九、审查报告格式

当代码审查**不通过**时，按以下格式输出报告：

```markdown
## 代码审查报告

### 审查结果：❌ 不通过

### 问题汇总

| 序号 | 严重程度 | 问题类型 | 文件位置 | 问题描述 |
|------|----------|----------|----------|----------|
| 1 | 🔴 严重 | 命名规范 | UserService.java:23 | 布尔变量 isEnabled 违反了不得以 is 开头的规范 |
| 2 | 🟡 警告 | 代码格式 | UserService.java:45 | 单行字符数超过 120 限制 |
| 3 | 🔴 严重 | OOP 规范 | UserService.java:67 | 调用自身方法未使用 this 关键字 |

### 问题详情

#### 问题 1：布尔变量命名违规
**文件位置**：`UserService.java` 第 23 行

**违规代码**：
```java
private Boolean isEnabled;
```

**规范要求**：
> 在 POJO 类中布尔类型的变量不允许以 is 开头。is 开头在 redis / rpc 序列化与反序列化过程中会出现异常。

**修改建议**：
```java
private Boolean enabled;
```

---

#### 问题 2：单行字符数超限
**文件位置**：`UserService.java` 第 45 行

**违规代码**：
```java
String userName = userService.getUserNameById(userId) + "的余额为：" + balance + "元，状态：" + status;
```

**规范要求**：
> 单行字符数限制不超过 120 个。

**修改建议**：
```java
String userName = userService.getUserNameById(userId) + "的余额为：" + balance 
    + "元，状态：" + status;
```

---

### 优化建议

1. **命名规范**：将所有布尔变量改为非 is 开头
2. **代码格式**：对超长行进行合理换行
3. **方法调用**：在调用类自身方法时必须使用 this 关键字
```

---

## 十、审查流程

```
┌─────────────────┐
│   接收代码文件    │
└────────┬────────┘
         ▼
┌─────────────────┐
│   识别代码类型    │  ← Java / Proto / Config
└────────┬────────┘
         ▼
┌─────────────────┐
│   执行分项审查    │
├─────────────────┤
│  1. 命名规范     │
│  2. 代码格式     │
│  3. OOP 规范     │
│  4. 注释规范     │
│  5. 项目结构     │
│  6. Proto3(如适用)│
└────────┬────────┘
         ▼
┌─────────────────┐
│   汇总问题并输出  │
│   审查报告       │
└─────────────────┘
```

## 十一、审查结论判定

| 结论 | 判定标准 |
|------|----------|
| ✅ 通过 | 无任何违规问题，或仅有轻微建议项 |
| ❌ 不通过 | 存在 1 个或以上严重/警告级别问题 |

**严重程度定义**：
- 🔴 严重：违反会导致运行时异常或序列化问题
- 🟡 警告：影响代码可读性或维护性
- 🟢 提示：建议优化，非强制要求
