---
name: code-reviewer
description: 后端代码审查 skill。当用户要求 review 代码、审查代码规范、检查代码质量、要求优化代码，或 dev-session P4 AI Review 阶段触发时使用。审查范围覆盖：命名规范、代码格式、OOP 规范、注释规范、项目结构、Model 层、Service 层、Controller 层、Integration 层、Proto3 编写规范。按七步硬流程执行，逐维度 × 逐文件全覆盖，禁止选择性抽查。审查标准以各职能 skill 为准。
---

# 后端代码审查规范

本 skill 用于对后端代码进行规范审查。审查规则以各职能 skill 为权威标准，本文聚焦**硬性审查流程**、审查要点和报告格式。

> **为什么是硬流程**：历史教训表明，依赖"维度表 + 被动检查"会反复漏检（`this.` 前缀、私有方法 Javadoc、布尔 is 前缀均多次漏检后才被开发者捕获），且"改动小/有把握"常被用作跳过 Review 的理由导致返工。因此本 skill 把审查定义为**不可跳过、不可抽查**的步骤序列。

---

## 〇、七步硬流程（任何 Review 必须按此执行）

**Step 0 — 装载规则**：Read 本 skill 全文（不许 skim）+ Read 项目 memory 中 reviewer 相关 feedback（如有）。
进入审查前必须在输出中明确写一句：**"已 Read reviewer SKILL 全文 + 漏检史清单（{日期}），按 {N} 文件 × 全维度矩阵审查。"** 未写此句即开始 review = 违反协议 = 必返工。

**Step 1 — 圈定范围**：列出本次 `git status` / `git diff` 中所有新建 + 修改的 `.java` / `.proto` 文件，输出文件清单。**全部进入审查范围，不允许"只看核心文件"。**

**Step 2 — 强制 Grep 扫描**（对每个新建/修改的 ServiceImpl / Flow / Controller / 工具类）：

| 扫描目标 | Grep 模式 | 对应禁止项 |
|----------|-----------|-----------|
| `this.` 缺失 | `^\s+[a-z][a-zA-Z]+\(` 逐行确认调用类型 | #35 |
| 布尔 is 前缀 | `private Boolean is[A-Z]` / `private boolean is[A-Z]` | #4 🔴 |
| 私有方法缺 Javadoc | `private\s+(static\s+)?[\w<>\[\]]+\s+\w+\s*\(` 前无 `/**` | #37 |
| RuntimeException 直抛 | `throw new RuntimeException` | #22 |
| Controller 手动 stream 转换 | `\.stream\(\)\.map\(` （Controller 内） | #34 |

`this.` 扫描的逐行判定：当前类**实例方法** → 必须 `this.`；**静态方法** → 不需要（建议类名前缀）；lambda/局部函数 → 不需要。**此扫描禁止跳过。**

**Step 3 — Entity / TableDef 检查**（每个新建/修改的 Entity）：
- 继承正确（业务表 `CommonBusinessEntity` / 全局表 `CommonEntity`，按项目多租户约定）
- TableDef 已按 `tabledef` skill 同步创建/更新，并注册到 `TableDefCollect`（#10 🔴）
- `@Column(isLarge = true)` 字段 → Service 读取处用 `selectOneByQuery(QueryWrapper.select(ALL_COLUMNS))`，**不是** `queryChain().one()` / `getById()`（默认不返回大字段）

**Step 4 — DTO / Model 检查**（每个新建/修改的 DTO/VO/Operate/Query）：
- 字段名与列名不一致时，QueryChain 查询有 `.as(DTO::getter)` 显式映射
- 继承 CommonOperate / CommonQuery；有继承用 `@SuperBuilder`；布尔命名 `xxxFlag` + `@Column("is_xxx")`

**Step 5 — Controller / Flow 检查**（每个新建/修改的 Controller/Flow）：
- record vs class 判定正确（需类级 AOP 注解时必须 class + `@Resource`，record 不兼容 CGLIB）
- 无内联业务逻辑（鉴权用 AOP 注解；DTO→VO 用 `CommonResult.success(data, fn)` 系列）
- Flow 类有 `@Validated`（方法级参数校验生效的前提）

**Step 6 — 按第十三节标准格式输出报告**：逐维度给出结论（通过/问题数），不允许"整体看了没问题"式总结。

**Step 7 — 自修后复检**：修复所有问题后**重跑 Step 2 ~ Step 6**，验证无回归，输出第二轮结论。

### 同类违规回溯（与 `similar-issue-sweep` 联动）

Step 2-6 中**每发现一处违规**，立即在**本次变更的全部文件**中扫描同一模式（同一开发批次极易复现同一错误）；若该违规属于历史漏检清单中的条目，扩大到**所在业务域全量文件**扫描，结果并入报告。

---

## 一、审查维度与规则来源

```
┌─────────────────────────────────────────────────────────────────┐
│                         代码审查维度                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 命名规范         → 本文第二节 + 各层 skill                    │
│  2. 代码格式         → 本文第三节                                 │
│  3. OOP 规范         → 本文第四节（含类成员排序硬规定）            │
│  4. 代码注释         → 本文第五节（含 Doc 精简原则）               │
│  5. 项目结构         → project-structure skill + tabledef skill  │
│  6. Model 层         → model-conventions skill                   │
│  7. Service 层       → service-conventions skill                 │
│  8. Controller 层    → controller-conventions skill              │
│  9. Integration 层   → integration-flow skill                    │
│  10. Proto3 / gRPC   → grpc skill                                │
└─────────────────────────────────────────────────────────────────┘
```

**全覆盖要求**：每个被审文件至少过一遍其适用维度；报告中逐维度给结论。**禁止选择性 Review**——只审"觉得可能有问题的文件/维度"是流程违规。

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
| Controller 非 record 类（无 AOP 场景） | `class XxxController` | `record XxxController(...)` | controller-conventions |
| Controller 命名不符 | `AuthController` | `AdminAuthV1Controller` | controller-conventions |
| 方法名非 lowerCamelCase | `GetUserById` | `getUserById` | — |
| 常量非全大写下划线 | `maxRetryCount` | `MAX_RETRY_COUNT` | — |
| 布尔变量以 is 开头（新代码） | `isEnabled` | `enabled` / `enabledFlag` | model-conventions |
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
| **类成员排序** | 严格按 `静态字段 → 实例字段 → 构造器 → 公开方法 → 私有实例方法 → 私有静态方法` 排序，**禁止 public/private 顺序交叉** |

### 类成员排序规范（硬规定）

类成员定义顺序自上而下：

1. **静态字段**：`private static final XXX = ...`（常量）、`private static XXX`（可变）
2. **实例字段**：`@Resource` 注入字段、private 字段
3. **构造器**（如有）
4. **公开方法**（public，含 `@Override`）— 按业务分组、调用关系可加注释段落分隔
5. **私有实例方法**（private 非 static）— 服务于上方公开方法的辅助逻辑
6. **私有静态方法**（private static）— 工具方法、空值兜底等

**禁止**在公开方法之间插入私有方法（即「先 public → 中间夹 private → 又 public」是违规）。
**禁止**在私有实例方法和私有静态方法之间穿插。

#### 反例

```java
public class XxxServiceImpl implements XxxService {
    public void publicA() { ... }
    private void helperOfA() { ... }   // ❌ 私有方法穿插在公开方法之间
    public void publicB() { ... }
    private static int nz(int v) { ... } // ❌ 私有静态方法在公开方法后但在私有实例方法前不允许
    private void helperOfB() { ... }
}
```

#### 正例

```java
public class XxxServiceImpl implements XxxService {
    // === 静态字段 ===
    private static final DateTimeFormatter FMT = ...;

    // === 实例字段 ===
    @Resource private XxxMapper mapper;

    // === 公开方法 ===
    @Override public void publicA() { this.helperOfA(); }
    @Override public void publicB() { this.helperOfB(); }

    // === 私有实例方法 ===
    private void helperOfA() { ... }
    private void helperOfB() { ... }

    // === 私有静态方法 ===
    private static Integer nz(Integer v) { return v == null ? 0 : v; }
}
```

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

- **所有方法**（public / protected / private）均须 Javadoc 注释，不限于 Service 接口
- 每个方法必须说明功能和参数作用
- 有返回值需描述返回内容
- 复杂流程需简要说明核心影响
- 覆写接口实现方法不需要重复描述

### 代码逻辑注释

- 双斜线与内容之间有且仅有一个空格
- 注释前后需要空行
- 未完成事项用 `TODO`，待修复点用 `FIXME`

### Doc 注释精简原则

DOC 不是 README 也不是 ADR。只回答三件事：

1. **是干什么的**（一句话）
2. **什么时候出意外行为**（异常、边界、副作用）
3. **有什么反直觉的设计决策**（防止后人"优化"掉）

其他都不写：内部实现、与其他组件的关系论证、变更历史、bug 修复记录 → 属于 README / ADR / commit message。

#### 篇幅与契约

- **类注释**：15 ~ 30 行（含空行）。简单类可更短
- **方法注释**：聚焦契约
  - `@param` — 参数语义（不是"是什么类型"，Java 类型已说明）
  - 返回值 — 描述返回内容含义（不是复述"返回 xxx 字段"）
  - `@throws` — 异常条件
  - 线程安全性（如有特殊语义）
- **实现细节** → 写在代码行内注释（双斜线），不进 Javadoc
- **覆写接口实现方法不需要重复描述**

#### 反直觉决策必写

如果某个设计决策让后来者会想"优化"掉，**必须显式写明为什么这么做**。建议用「反直觉点：xxx」前缀。

例：
- 实体已设值时不覆盖（防止后人改成无条件覆盖）
- 无上下文时抛异常（防止后人加 silent fallback）
- 多租户豁免注解 + INSERT 不豁免（防止后人加 escape hatch）

#### 反模式速查（不允许）

| 反模式 | 示例 | 应改为 |
|--------|------|--------|
| 复述代码 | `"这个方法返回 organizationId"` | 删除 / 写参数语义 |
| commit message 风格 | `"修复了 xxx bug"` `"重构后..."` | 写在 commit message |
| 过度结构化 | 短文档堆 `<h3>` `<ul>` 像论文 | 段落 + `<b>` 强调即可 |
| 实现关系论证 | `"本类不与 X 框架冲突，因为..."` | 删除 → ADR |
| 装饰性 emoji | `⚠️ 🔴 ✅` 大量出现 | 删除 |
| 重复 `@see` | 已用 `@link` 引用过的类又加 `@see` | 只保留 `@link` |
| 宣传词 | `"业务代码零侵入"` `"性能优异"` | 删除 |
| 未来时态 | `"未来可能扩展为..."` `"预留 X 给 Y"` | 仅写当前已存在的契约 |

---

## 六、项目结构审查要点

> 详细规则参考 `project-structure` skill

- 层间依赖是否正确（禁止反向依赖）
- 文件是否放在正确的包中
- 域专属枚举是否错误放在 common 中
- support 包中是否包含业务逻辑
- **TableDef 同步检查**（参考 `tabledef` skill）：
  - 新增 Entity → 必须有对应的 `entity/table/{ClassName}TableDef.java`
  - 新增 TableDef → 必须在 `support/TableDefCollect.java` 注册短名常量
  - Entity 字段变更 → TableDef 中的 QueryColumn 必须同步更新

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
- TableDef 是否通过 `TableDefCollect` 统一引用（禁止局部变量持有 TableDef）
- 大字段（`@Column(isLarge = true)`）读取是否用 `select(ALL_COLUMNS)` 显式取全列

---

## 九、Controller 层审查要点

> 详细规则参考 `controller-conventions` skill

- **record vs class**：默认用 record + 构造注入；需要类级 AOP 注解（如项目自定义鉴权注解）时必须用 class + `@Resource` 注入（record 是 final 类，不兼容 CGLIB 代理）
- 路径是否按 `/{版本}/{平台或应用}/` 分层
- **禁止业务逻辑**：鉴权检查 → 用注解 + AOP Aspect；数据转换 → 用 `CommonResult` 转换系列方法
- 返回值是否使用 `CommonResult` 包装
- **DTO→VO 转换**：使用 `CommonResult.success(T, Function)`、`successWith(Collection, Function)`、`successPage(Page, Function)` 内联转换，不在方法体中手动遍历

---

## 十、Integration 层审查要点

> 详细规则参考 `integration-flow` skill

- 跨业务写操作是否在 Flow 中而非 Service 中
- Flow 是否通过 Service 操作数据库（禁止直接操作 Mapper）
- Flow 类是否加 `@Validated`（方法参数校验生效前提）
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
| 10 | 新增 Entity 未同步创建 TableDef 或未注册到 TableDefCollect | 🔴 严重 |
| 11 | support 包中放业务逻辑 | 🟡 警告 |
| 12 | Controller 使用 record 但需要类级 AOP → 应改 class | 🟡 警告 |
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
| 24 | Service 方法返回 VO（应返回 DTO，VO 转换在 Controller 层） | 🔴 严重 |
| 25 | 反直觉设计决策未在 Javadoc 标注 | 🔴 严重（可能被后人"优化"掉） |
| 26 | Javadoc 复述代码本身能看出的东西 | 🟡 警告 |
| 27 | Javadoc 写 commit message 风格 | 🟡 警告 |
| 28 | Javadoc 包含实现关系论证 | 🟡 警告 |
| 29 | Javadoc 过度结构化（短文档像论文） | 🟢 提示 |
| 30 | 类 Javadoc 超过 30 行 | 🟢 提示 |
| 31 | 装饰性 emoji 出现在 Javadoc 中 | 🟢 提示 |
| 32 | 已用 `@link` 引用过的类又加 `@see` | 🟢 提示 |
| 33 | Controller 内联鉴权检查 → 应用注解 + AOP | 🔴 严重 |
| 34 | Controller 手动遍历 DTO→VO 转换 → 应用 `CommonResult` 转换系列 | 🟡 警告 |
| 35 | 调用自身实例方法未加 `this.` 前缀 | 🟡 警告（必须全文件扫描） |
| 36 | 类成员排序违规：public/private 交叉、私有方法穿插 | 🟡 警告 |
| 37 | 私有静态工具方法（如 `nz`、`isBlank`、断言等）无 Javadoc | 🟡 警告（所有方法均须 Javadoc） |
| 38 | Flow 类缺 `@Validated` | 🟡 警告 |
| 39 | `updateById`/`deleteById` 前无存在性校验（详见 `api-contract-checker` 规则 5） | 🟡 警告 |
| 40 | 写操作 Controller 返回 `CommonResult<Void>`（详见 `api-contract-checker` 规则 1） | 🔴 严重 |

---

## 十三、审查报告格式

### 通过

```markdown
## 后端代码审查报告

### 协议确认
已 Read reviewer SKILL 全文 + 漏检史清单（{日期}），按 {N} 文件 × 全维度矩阵审查。

### 审查范围
[文件清单]

### 逐维度结论
| 维度 | 结论 |
|------|------|
| 命名规范 | ✅ |
| 代码格式 | ✅ |
| OOP（含 this. 扫描 / 成员排序） | ✅ |
| 注释（含私有方法 Javadoc） | ✅ |
| 结构 / TableDef 同步 | ✅ |
| Model / Service / Controller / Integration | ✅ |
| 漏检史专项核对 | ✅ |

### 审查结果：✅ 通过
```

### 不通过

```markdown
## 后端代码审查报告

### 协议确认 / 审查范围（同上）

### 问题汇总
| 序号 | 严重程度 | 问题类型 | 文件位置 | 问题描述 |
|------|----------|----------|----------|----------|
| 1 | 🔴 严重 | 命名规范 | UserService.java:23 | 布尔变量 isEnabled 违反命名规范 |

### 问题详情
#### 问题 1：布尔变量命名违规
**文件位置**：`UserService.java` 第 23 行
**违规代码**：`private Boolean isEnabled;`
**规范要求**：布尔类型变量不允许以 is 开头（禁止 #4）
**修改建议**：`private Boolean enabled;`
**同类扫描**：[本次变更其余文件中同模式命中情况]

### 审查结果：❌ 不通过 → 自修后重跑 Step 2-6
```

### 严重程度与判定

- 🔴 **严重**：运行时异常、序列化问题、架构违规 | 🟡 **警告**：可读性/维护性/团队规范 | 🟢 **提示**：建议优化
- ✅ 通过 = 无严重/警告级问题；❌ 不通过 = 存在 ≥1 个严重/警告级问题

---

## 十四、漏检史清单（每次 Review 必须主动核对）

> 这里登记**曾被开发者捕获的 AI 漏检项**。每次 Review 把本清单作为必查项过一遍；
> 项目中新发生的漏检按 `team-memory` 升级机制**当场追加**到项目级清单（项目 memory 或本文件项目副本）。

| Rule | 出处 | 教训来源 |
|------|------|----------|
| `this.` 前缀缺失 | #35 / OOP 第四节 | 多次漏检，包括代码已提交后才被发现——必须 Grep 扫描而非目测 |
| 私有方法 Javadoc 缺失 | #37 / 注释第五节 | 多次漏检 |
| Javadoc `@param + @return` 不完整 | 第五节 | 曾漏检 |
| `@SuperBuilder`（有继承时） | #8 | 偶发 |
| Operate 动词在前（AddXxxOperate） | #17 | 偶发 |
| 布尔 is 前缀 | #4 🔴 | 曾漏检（isAuto） |
| TableDef 用局部变量而非 TableDefCollect | 第八节 | 曾漏检 |
| Controller 手动 stream.map | #34 | 曾漏检 |
| DTO 字段与列名不一致未加 `.as(DTO::getter)` | Step 4 | 曾漏检 |
| `@Column(isLarge=true)` 字段读取未 select ALL_COLUMNS | Step 3 | 曾漏检 |
| Flow 缺 `@Validated` | #38 | 曾漏检 |
| **整段跳过 Review**（编码后直接进自测/提交） | dev-session 规则 4 | 曾以"小修复"为由两次跳过，结果漏检且已 commit 后才补查 |

---

## 十五、审查流程总览

```
接收变更 → Step 0 装载规则（echo 协议）→ Step 1 文件清单
→ Step 2 强制 Grep 扫描 → Step 3-5 分层检查 → 漏检史专项核对
→（发现违规 → 同模式回溯扫描）→ Step 6 报告 → 自修 → Step 7 复检
```
