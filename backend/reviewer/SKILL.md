---
name: code-reviewer
description: 后端代码审查 skill。当用户要求 review 代码、审查代码规范、检查代码质量、要求优化代码时使用此 skill。审查范围覆盖：命名规范、代码格式、OOP 规范、注释规范、项目结构、Model 层、Service 层、Controller 层、Integration 层、Proto3 编写规范。审查标准以各职能 skill 为准。
---

# 后端代码审查规范

本 skill 用于对后端代码进行规范审查。审查规则以各职能 skill 为权威标准，本文聚焦审查流程和报告格式。

---

## 一、审查维度与规则来源

```
┌─────────────────────────────────────────────────────────────────┐
│                         代码审查维度                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 命名规范         → 本文第二节 + 各层 skill                    │
│  2. 代码格式         → 本文第三节                                 │
│  3. OOP 规范         → 本文第四节                                 │
│  4. 代码注释         → 本文第五节                                 │
│  5. 项目结构         → project-structure skill                   │
│  6. Model 层         → model-conventions skill                   │
│  7. Service 层       → service-conventions skill                 │
│  8. Controller 层    → controller-conventions skill              │
│  9. Integration 层   → integration-flow skill                    │
│  10. Proto3 / gRPC   → grpc skill                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、命名规范审查

> **权威规范在各子 skill 中定义**，本节只列审查要点 + 高频违规。详细规则参考：
> - 类命名 / 包结构 → `project-structure`
> - Model / Operate / Query / DTO / VO → `model-conventions`
> - Service 方法命名 → `service-conventions`
> - Controller 命名与路径 → `controller-conventions`

### 高频违规速查

| 检查项 | 违规示例 | 正确示例 | 出自 |
|--------|----------|----------|------|
| 类名非 UpperCamelCase | `userService` | `UserService` | project-structure |
| 抽象类非 Base 开头 | `AbstractUserService` | `BaseUserService` | project-structure |
| 异常类非 Exception 结尾 | `BusinessError` | `BusinessException` | common |
| 枚举非 Enum 后缀 | `Status` | `StatusEnum` | common |
| Controller 非 record 类 | `class XxxController` | `record XxxController(...)` | controller-conventions |
| Controller 命名不符 | `AuthController` | `AdminAuthV1Controller` | controller-conventions |
| 方法名非 lowerCamelCase | `GetUserById` | `getUserById` | — |
| 常量非全大写下划线 | `maxRetryCount` | `MAX_RETRY_COUNT` | — |
| 布尔变量以 is 开头（新代码） | `isEnabled` | `enabled` | model-conventions |
| Operate 命名动词在后 | `UserAddOperate` | `AddUserOperate` | model-conventions |
| Service 方法命名违规 | `selectUserById` | `getDtoById` | service-conventions |
| 转换方法命名违规 | `toUserInfoVo()` | `convertToUserInfoVo()` | model-conventions |

---

## 三、代码格式审查

- **大括号**：空代码块写成 `{}`；非空块左大括号前不换行，后换行
- **单行字符数**：不超过 120 个
- **换行规则**：第二行缩进 4 空格，运算符与下文一起换行，点号与下文一起换行，逗号后换行
- **空格**：方法参数逗号后加空格

---

## 四、OOP 规范审查

| 检查项 | 规范要求 |
|--------|----------|
| 覆写方法 | 必须加 `@Override` |
| 静态访问 | 用类名直接访问，禁止通过对象引用 |
| 接口过时 | 加 `@Deprecated` 并说明新接口 |
| 调用自身方法 | 必须用 `this.method()` |
| 调用父类方法 | 必须用 `super.method()` |
| 可变参数 | 必须放在参数列表最后 |
| equals 调用 | 用常量或确定有值的对象调用 equals |

---

## 五、注释规范审查

### 类注释

```java
/**
 * 加载权限初始化
 *
 * @author hwy
 * @since 2026/01/01 01:58
 **/
```

### 方法注释

- 每个方法/接口必须说明功能和参数作用
- 有返回值需描述返回内容
- 复杂流程需简要说明核心影响
- 覆写接口实现方法不需要重复描述

### 代码逻辑注释

- 双斜线与内容之间有且仅有一个空格
- 注释前后需要空行
- 未完成事项用 `TODO`，待修复点用 `FIXME`

---

## 六、项目结构审查要点

> 详细规则参考 `project-structure` skill

- 层间依赖是否正确（禁止反向依赖）
- 文件是否放在正确的包中
- 域专属枚举是否错误放在 common 中
- entity/table/ 下的文件是否被手动修改
- support 包中是否包含业务逻辑

---

## 七、Model 层审查要点

> 详细规则参考 `model-conventions` skill

- 模型类型是否正确选择（通用模型/DTO/VO/Operate/Query）
- Operate 是否继承 `CommonOperate`，Query 是否继承 `CommonQuery<T>`
- 是否使用 `@SuperBuilder`（有继承时）而非 `@Builder`
- 布尔字段是否以 is 开头（旧项目兼容除外）
- POJO 中是否存在无对应变量的 get/set 方法
- ConvertAid 是否在被多处引用时才抽取

---

## 八、Service 层审查要点

> 详细规则参考 `service-conventions` skill

- 方法命名是否遵循规约
- 是否存在跨业务域写操作（应在 Flow 中）
- 是否直接操作其他表的 Mapper（应通过对方 Service）
- QueryChain 是否优先于 XML
- TableDef 是否通过 `TableDefCollect` 统一引用

---

## 九、Controller 层审查要点

> 详细规则参考 `controller-conventions` skill

- 是否使用 record 类 + 构造注入
- 路径是否按 `/{版本}/{平台或应用}/` 分层
- Controller 中是否包含业务逻辑
- 返回值是否使用 `CommonResult` 包装

---

## 十、Integration 层审查要点

> 详细规则参考 `integration-flow` skill

- 跨业务写操作是否在 Flow 中而非 Service 中
- Flow 是否通过 Service 操作数据库（禁止直接操作 Mapper）
- Initializer 是否继承 BaseInitializer

---

## 十一、Proto3 / gRPC 审查要点

> 详细规则参考 `grpc` skill

- proto 文件是否 snake_case 命名
- message/service/enum 命名是否符合规范
- 字段编号是否复用（删除后须 reserved）
- GrpcServiceImpl 中是否使用 `DataUtils.setIfNotNull`

---

## 十二、禁止事项清单

| # | 禁止事项 | 严重程度 |
|---|----------|----------|
| 1 | Controller 中写业务逻辑 | 🔴 严重 |
| 2 | Service 跨域直接操作其他域的 Mapper | 🔴 严重 |
| 3 | domain 层依赖 interfaces 层 | 🔴 严重 |
| 4 | 布尔变量以 is 开头（新代码） | 🔴 严重 |
| 5 | POJO 中存在无对应变量的 get/set | 🔴 严重 |
| 6 | proto 字段编号复用 | 🔴 严重 |
| 7 | GrpcServiceImpl 中 `builder.setXxx(null)` | 🔴 严重 |
| 8 | 使用 `@Builder` 替代 `@SuperBuilder`（有继承时） | 🟡 警告 |
| 9 | 域专属枚举放在 common 中 | 🟡 警告 |
| 10 | 手动修改 entity/table/ 下的文件 | 🟡 警告 |
| 11 | support 包中放业务逻辑 | 🟡 警告 |
| 12 | Controller 不使用 record 类 | 🟡 警告 |
| 13 | API 路径无版本号 | 🟡 警告 |
| 14 | 自行创建 Page 类而非使用 MyBatis-Flex 的 `Page` | 🔴 严重 |
| 15 | CommonEnum 子类重复标注 `@EnumValue` | 🟡 警告 |
| 16 | DTO/VO 直接放在 `model/` 而非 `model/dto/` 或 `model/vo/` | 🟡 警告 |
| 17 | Operate 命名为 `{业务}{操作}Operate`（动词在后） | 🟡 警告 |
| 18 | 参数 > 3 或含数组类型时仍用 `@GetMapping`（应改 POST + CommonQuery） | 🟡 警告 |
| 19 | 写操作仅用 POST，未合理使用 PUT / DELETE | 🟡 警告 |
| 20 | 事务内调用写操作型外部 RPC/HTTP（应用 `TransactionUtils.asyncExecuteAfterCommit`） | 🔴 严重 |
| 21 | 事务内发送业务驱动型 MQ（下游会写库的，应用 `TransactionUtils.asyncExecuteAfterCommit`） | 🔴 严重 |
| 22 | 直接 `throw new RuntimeException(...)` 而非 `ApiException` | 🟡 警告 |
| 23 | 手动 `new CommonPage<>()` 而非 `CommonResult.successPage(page)` | 🟡 警告 |

---

## 十三、审查报告格式

### 通过

```markdown
## 代码审查报告

### 审查结果：✅ 通过

无违规问题。
```

### 不通过

```markdown
## 代码审查报告

### 审查结果：❌ 不通过

### 问题汇总

| 序号 | 严重程度 | 问题类型 | 文件位置 | 问题描述 |
|------|----------|----------|----------|----------|
| 1 | 🔴 严重 | 命名规范 | UserService.java:23 | 布尔变量 isEnabled 违反命名规范 |

### 问题详情

#### 问题 1：布尔变量命名违规
**文件位置**：`UserService.java` 第 23 行
**违规代码**：
```java
private Boolean isEnabled;
```
**规范要求**：布尔类型变量不允许以 is 开头
**修改建议**：
```java
private Boolean enabled;
```
```

---

## 十四、审查流程

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
│   执行分项审查    │  ← 按维度逐项检查
└────────┬────────┘
         ▼
┌─────────────────┐
│   汇总问题并输出  │
│   审查报告       │
└─────────────────┘
```

### 严重程度定义

- 🔴 **严重**：会导致运行时异常、序列化问题、架构违规
- 🟡 **警告**：影响代码可读性、维护性或不符合团队规范
- 🟢 **提示**：建议优化，非强制要求

### 判定标准

| 结论 | 标准 |
|------|------|
| ✅ 通过 | 无严重/警告级别问题 |
| ❌ 不通过 | 存在 1 个或以上严重/警告级别问题 |
