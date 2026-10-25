# 前后端契约速查（常驻规则）

> 本文件由 Claude Code 自动加载（`.claude/rules/*.md`）。权威长文档放 `.document/adr/`，这里只放两端都必须遵守的速查项；
> `api-contract-checker` 在 dev-session P4 据此校验，技术设计文档「契约」章节按此约定冻结每个需求的接口。
> 占位符 {xxx} 按项目填写；与项目栈不符的行**删掉**，不留"大概是这样"的约定。
> 模板来源：framework/skills/templates/.claude/rules/api-contract.md（填完删除本行）。

## 响应包装与返回类型

| 后端操作 | 后端返回 | 前端泛型 | `if (res.data)` |
|----------|---------|----------|-----------------|
| 创建 | `CommonResult<Long>` | `number`/`string` | ✅ |
| 更新/删除 | `CommonResult<Boolean>` | `boolean` | ✅ |
| 分页 | `CommonResult<CommonPage<T>>` | `PageResponse<T>` | ✅ |
| 登录等 Void | `CommonResult<Void>` | — | ❌ 用 `code` 判断 |

- 写操作禁止返回 `Void`：`data` 为 null 时前端 `if (res.data)` 永远 falsy，静默失败

## ID 与时间

- **ID**：后端 `Long`，**前端一律 `string`** 接收、传递、绑定（超过 2^53 丢精度）；前端 ID 类 state 初始值用 `''` 不用 `0`，`onChange` 直接存值不做 `Number()` 转换
- **时间**：后端统一 {毫秒时间戳 / ISO 字符串}；前端统一经 `{formatTime 工具路径}` 展示，禁止直接 `new Date(x).toLocaleString()` 或把原始值渲染出来

## 分页

- 请求 `{ pageNum: 1, pageSize: 20 }`，`pageNum` 从 **1** 开始；响应 `{ list, total, pageNum, pageSize }`
- 后端先 `COUNT`，为 0 直接返回空列表，不执行 list 查询

## 附件 / 文件字段

- 不返回裸 URL 字符串，统一 `{ name, url }` 对象；单文件可为空、多文件为数组

## 幂等

- 写操作接口的幂等策略：{请求头 / body 中的 idempotencyKey；业务唯一键；无}——前端每次提交生成新 key，不复用上一次
- 豁免清单（按路径和 ID 天然幂等的 modify / changeState 类）以后端 Operate 定义为准，前端不多传

## 参数校验

- 后端 Controller 层 `@Valid` / `@Validated`，失败统一返回 {code}；Service 层不重复做同样校验
- 前端表单 rules 必须对齐后端：`@Size(min/max)` ↔ `min/max`、`@NotBlank` ↔ `required`、`@Email` ↔ `type: 'email'`，输入框 `:maxlength` 同步

## 契约变更流程

- 先改技术设计文档「契约」章节 → 再改两端实现（见 `pre-dev-alignment`）；**禁止后端先改实现再补文档**
- 后端约束"创建后不可改"的字段，前端编辑态必须 `disabled`；后端默认脱敏的字段，前端不预填明文、不打 console

## {多租户 / 权限 / 其他项目专有契约}

{按项目填写：Header 约定、权限 key 约定、字段命名强制项；权威长文档放 .document/adr/}

## 已踩过的跨端坑

- **CommonResult\<Void\> 静默失败**：`data` 为 null，前端 `if (res.data)` 永远 falsy → 写操作禁止返回 Void
- **前端类型必须对齐后端 VO/Operate**：不能有后端不存在的字段
- **前端表单验证对齐后端 @Size**：min/max 必须一致
- {项目踩坑随迭代追加；重复出现的进 memory 并在此放一行指针}
