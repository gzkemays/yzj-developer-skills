# yzj-dev-workflow · 编码质量自检（第 5 节，编码后、P4 Review 前）

> 门禁：自检不替代 dev-session P4 的 reviewer 硬流程（规则 4）；每项结论附文件依据，grep 零命中或"已读规范"不算检查通过。

## 5. 编码质量自检（编码后）

编码完成后、进入 dev-session P4 Review 前执行以下自检（详细规则参考 `reviewer` skill）：

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
- [ ] 转换字段白名单、null/默认值/继承字段已核对，未默认使用 BeanUtils.copyProperties
```

### 5.3.1 通用 Java 契约自检

逐文件核对类的 `@author` / `@since`、各参数对应的 `@param`、非 void 方法的 `@return`，保留已存在的真实作者和创建时间；覆写方法只在上游契约完整时免重复。业务枚举/常量检查覆盖判断、查询、赋值与测试，不能只检查枚举声明。审查结论给出命中文件、依据和保留例外，不能用 grep 零命中或“已读规范”代替检查。

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

### 5.7 安全 / 金融 / 测试自检（命中时）

```
- [ ] 安全：security skill 8.8 清单逐条过（输入与注入、敏感数据两组每次必过）
- [ ] 金融：financial skill 第七节清单逐条过
- [ ] 测试：Service / Flow 有 {method}_{scenario}_{expected} 命名的用例；必测场景已覆盖（testing 第四节）
- [ ] 含敏感 payload 接口已进 LoggerFilter 忽略清单
```
