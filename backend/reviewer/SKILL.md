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

### 类名规范

| 检查项 | 规范要求 | 正确示例 | 错误示例 |
|--------|----------|----------|----------|
| 类名格式 | UpperCamelCase | `UserService` | `userService` |
| 抽象类 | Base 开头 | `BaseInitializer` | `AbstractUserService` |
| 异常类 | Exception 结尾 | `BusinessException` | `BusinessError` |
| 测试类 | 测试类名 + Tests | `UserServiceTests` | `TestUserService` |
| 枚举类 | Enum 后缀 | `StatusEnum` | `Status` |
| Controller | record 类 + `{平台}{业务}{版本}Controller` | `AdminAuthV1Controller` | `AuthController` |

### 方法名与变量名

| 检查项 | 规范要求 | 正确示例 | 错误示例 |
|--------|----------|----------|----------|
| 方法名/参数名/变量名 | lowerCamelCase | `getUserById` | `GetUserById` |
| 常量名 | 全大写 + 下划线 | `MAX_RETRY_COUNT` | `maxRetryCount` |
| 布尔变量 | 禁止 is 开头（旧项目兼容除外） | `enabled` | `isEnabled` |

### Service 方法命名

| 操作 | 前缀 | 示例 |
|------|------|------|
| 获取单个 | `get` | `getDtoById()` |
| 获取多个 | `getxxxList` | `getDtoListByQuery()` |
| 获取统计 | `statistics` | `statisticsUserCount()` |
| 插入 | `add` | `add(operate)` |
| 删除 | `remove` | `removeById()` |
| 修改 | `update` | `update(operate)` |

### 数据转换方法

| 场景 | 规范 | 示例 |
|------|------|------|
| POJO 内转换（单处引用） | `convert` 开头 | `convertToUserInfoVo()` |
| 多处引用的转换 | `ConvertAid` 类 | `UserInfoConvertAid` |

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
