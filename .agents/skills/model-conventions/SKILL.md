---
name: model-conventions
description: "Model 层数据模型规范。当需要创建 DTO、VO、Operate、Query、通用模型、ConvertAid 转换类，或者需要确定使用哪种模型类型、如何组织 model 子包结构时使用此 skill。"
---

# Model 层数据模型规范

---

## 一、Model 子包结构

```
domain/{业务域}/model/
├── {通用模型}.java              # DTO 和 VO 结构一致时，直接用通用模型
├── dto/                         # 数据模型（内部传输）
│   └── {业务}DTO.java
├── vo/                          # 视图模型（返回客户端）
│   └── {业务}VO.java
├── operate/                     # 操作对象（增删改入参）
│   ├── Add{业务}Operate.java
│   └── Update{业务}Operate.java
└── query/                       # 查询对象
    └── {业务}{描述}Query.java
```

> DTO 和 VO 不直接放在 `model/` 下，而是分别放入 `model/dto/` 和 `model/vo/` 子包中。通用模型（无 DTO/VO 后缀）才直接放在 `model/` 下。

---

## 二、模型选择决策树

```
需要一个数据模型？
    │
    ├── 是增删改的入参？ → Operate（放 model/operate/）
    │
    ├── 是查询的入参？ → Query（放 model/query/）
    │
    ├── 是返回给客户端的？
    │   ├── 数据模型和视图模型结构一致？ → 通用模型（直接放 model/）
    │   ├── 需要裁剪字段？ → VO（放 model/vo/）
    │   └── 内部传输用（跨表聚合）？ → DTO（放 model/dto/）
    │
    └── 是纯粹的内部数据结构？ → 通用模型（直接放 model/）
```

---

## 三、各模型类型规范

### 3.1 通用模型（无 DTO/VO 后缀）

当数据模型和视图模型结构一致时，不需要单独定义 DTO 和 VO。

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SystemPermission {
    // 可包含 Entity 中不存在的组合字段，如 children、parentKey
}
```

### 3.2 DTO — 数据模型

当数据层需要复杂的内部结构时，单独命名 DTO 类。

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserInfoDTO {
    // UserEntity 的字段 + SystemRole 的字段（跨表聚合）
}
```

### 3.3 VO — 视图模型

视图层只返回客户端所需数据。一个 DTO/通用模型可以映射多个 VO。

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserInfoVO {
    /** 用户 ID */
    private Long id;
    /** 用户昵称 */
    private String nickname;
    /** 角色名称 */
    private String roleName;
}
```

### 3.4 Operate — 操作对象

用于增删改操作的入参，继承 `CommonOperate`。

**命名规则（强制）**：`{操作动词}{业务名}Operate`，**动词必须在前**。

| ✅ 正确 | ❌ 错误 |
|---------|---------|
| `AddUserOperate` | `UserAddOperate` |
| `UpdateUserOperate` | `UserUpdateOperate` |
| `RemoveUserOperate` | `UserRemoveOperate` |
| `EnableUserOperate` | `UserEnableOperate` |

> 与 Service 方法命名规约对齐（`add(AddUserOperate)`、`update(UpdateUserOperate)`），保持动词同位置可读性更强。

```java
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class ApplicationElectronVersionOperate extends CommonOperate {

    /**
     * 应用类型
     *
     * @see com.yeziji.datacenter.domain.application.enums.ApplicationVersionTypeEnum
     */
    private Integer type;

    /** 应用版本号 */
    @NotBlank(message = "version is cannot be blank")
    private String version;

    /** 文件 */
    @NotNull(message = "file is cannot be null")
    private MultipartFile file;
}
```

**要点**：
- 继承 `CommonOperate`，使用 `@SuperBuilder`
- 字段使用 Jakarta Validation 注解（`@NotBlank`、`@NotNull` 等）
- 枚举类型字段使用 `@see` 注释引用对应枚举类

### 3.5 Query — 查询对象

用于查询操作的入参，继承 `CommonQuery<T>`，泛型 T 为返回的模型类型。

```java
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class ElectronReleaseVersionInfoQuery extends CommonQuery<ElectronReleaseVersionInfo> {

    /**
     * 应用类型
     *
     * @see com.yeziji.datacenter.domain.application.enums.ApplicationVersionTypeEnum
     */
    private Integer type;

    /** 版本号 */
    private String version;
}
```

**要点**：
- 继承 `CommonQuery<T>`，T 指定查询返回类型
- 使用 `@SuperBuilder`（支持继承链上的建造者）
- 范围查询字段使用 `TimeRange`、`NumberRange`、`BigDecimalRange`

---

## 四、ConvertAid 转换辅助类

### 何时使用

| 场景 | 方式 |
|------|------|
| 转换逻辑仅被 1 处使用 | 在起始 POJO 中定义 `convert` 开头的方法 |
| 转换逻辑被 2 处及以上使用 | 单独定义 `ConvertAid` 类 |

### POJO 内转换方法

```java
public class UserRolePermissionDTO {
    /** 转为用户角色信息视图模型 */
    public UserRoleInfoVO convertToUserRoleInfoVo() {
        // 从 this 中获取数据源
    }
}
```

### ConvertAid 类

放置于 `domain/{业务}/aid/` 包下，命名为 `{业务}{描述}ConvertAid`。

```java
/**
 * 系统权限数据转换辅助类
 *
 * @author hwy
 * @since 2026/01/01 01:58
 **/
public class SystemPermissionConvertAid {
    /** Entity → Model */
    public static SystemPermission convertToModel(SystemPermissionEntity entity) {
        // 采用 set/get 赋值，或建造者模式
    }

    /** Model → Entity */
    public static SystemPermissionEntity convertToEntity(SystemPermission model) {
        // 转换逻辑
    }
}
```

---

## 五、Lombok 使用规范

| 注解 | 使用场景 |
|------|----------|
| `@Data` | 所有 Model 类 |
| `@Builder` | 无继承关系的通用模型、DTO、VO |
| `@SuperBuilder` | 有继承关系的类（Operate/Query 必须用） |
| `@NoArgsConstructor` + `@AllArgsConstructor` | 所有 Model 类 |
| `@EqualsAndHashCode(callSuper = true)` | 有继承关系的类 |
| `@Getter` + `@AllArgsConstructor` | 枚举类 |

> **禁止**使用 `@Builder` 替代 `@SuperBuilder`（继承场景下会丢失父类字段）。

---

## 六、字段规范

### 布尔字段

- 新项目**禁止**以 `is` 开头命名布尔变量（会导致 Redis/RPC 序列化异常）
- 旧项目兼容接口中 `is` 前缀字段允许存在（如 `isLatest`），标注为历史遗留

### 枚举引用

使用 `@see` 在字段注释中引用对应枚举类：

```java
/**
 * 应用类型
 *
 * @see com.yeziji.datacenter.domain.application.enums.ApplicationVersionTypeEnum
 */
private Integer type;
```

### POJO 方法约束

如果 POJO 类中不存在某个变量，禁止定义 `getXxx`/`setXxx` 方法（会导致序列化异常）。

---

## 七、不继承 CommonEntity

Model 类（DTO/VO/通用模型）是独立的传输对象，不继承 `CommonEntity`。可包含聚合/计算字段，通过 `DataUtils` 或 `ConvertAid` 编写互转逻辑。
