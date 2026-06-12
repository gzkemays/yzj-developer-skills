---
name: api-contract-checker
description: >
  前后端 API 契约校验器（YZJ 项目通用）。在编写或修改后端 Controller/Service/Operate/VO
  或前端 service API/TypeScript 类型时自动触发，按 5 条契约规则逐条扫描代码，
  发现违反约定立即提醒，避免上线后才暴露的"前后端不对齐"类问题。
user-invocable: false
---

# API Contract Checker

> 触发时机：所有涉及 Controller、Service、Operate、DTO、VO、ConvertAid、前端 `src/service/`、`src/typings/` 的写操作都应主动调用本 skill 自检一遍（dev-session P4 跨端检查）。
> 本 skill **只检查不修改**，发现问题后报告，由 dev-session P4 决定自修或上报。
> 项目如有额外契约约定（如多租户 Header），以项目根 CLAUDE.md 的 Cross-Cutting Contracts 为准、叠加检查。

---

## 规则 1 — CommonResult 写操作禁止返回 Void

### 反模式
```java
@PostMapping
public CommonResult<Void> create(@RequestBody @Valid AddXxxOperate operate) {
    xxxService.create(operate);
    return CommonResult.success();  // ❌ data 为 null，前端 if(res.data) 永远 falsy
}
```

### 正确模式
| 操作 | 返回 | 类型 |
|------|------|------|
| 创建 | `CommonResult<Long>` | 新记录 ID |
| 更新/删除 | `CommonResult<Boolean>` | `true` |
| 分页 | `CommonResult<CommonPage<T>>` | T 必须是 VO |
| 查询单条 | `CommonResult<T>` | T 必须是 VO |

### 检查清单
- [ ] 所有写操作 Controller 方法返回类型 ≠ `CommonResult<Void>`
- [ ] Service 写方法返回 `Long`（新增）/`Boolean`（修改/删除），不返回 `void`
- [ ] 前端用 `if (res.data)` 判断成功的场景，对应后端 data 不为 null

---

## 规则 2 — Operate 拆分：Add 与 Modify 不可共用

### 反模式
```java
@Data
@SuperBuilder
public class XxxOperate extends CommonOperate {
    @NotBlank
    private String username;  // ❌ 编辑场景 username disabled，但 @NotBlank 会拦截
}
```

### 正确模式
```java
// 新增：必填字段加 @NotBlank
public class AddXxxOperate extends CommonOperate {
    @NotBlank private String username;
    @NotBlank @Size(min = 8) private String password;
}

// 修改：所有字段可选，使用 @Size 等格式约束但不强制非空
public class ModifyXxxOperate extends CommonOperate {
    @Size(max = 50) private String displayName;
    @Email private String email;
}
```

### 检查清单
- [ ] 同一实体的新增/修改使用两个独立 Operate（`AddXxxOperate` + `ModifyXxxOperate`）
- [ ] `AddXxxOperate` 含 `@NotBlank`，`ModifyXxxOperate` 仅含格式约束
- [ ] Controller 入参对应：`POST` → `AddXxxOperate`，`PUT` → `ModifyXxxOperate`

---

## 规则 3 — 前端 TypeScript 类型必须对齐后端 VO/Operate

### 反模式
```typescript
interface UserVO {
  id: number;
  username: string;
  avatar: string;       // ❌ 后端 UserVO 没这个字段，运行时为 undefined
}
```

### 检查方法

扫描前端类型定义时，Grep 对应后端文件交叉验证：

```bash
grep -n "private" {backend}/src/main/java/**/XxxVO.java
grep -n "interface XxxVO" {frontend}/src/typings/**/*.d.ts
```

### 检查清单
- [ ] 前端 `XxxVO` 接口字段是后端 `XxxVO.java` 字段的**子集**（不能多出字段）
- [ ] 前端 `XxxOperate` / `XxxQuery` 接口字段是后端对应类的**子集**
- [ ] 字段类型对齐：`Long` ↔ `number`（雪花 ID 走 `string` 防精度丢失，按项目约定），`Boolean` ↔ `boolean`，`LocalDateTime` ↔ `string`/`number`

---

## 规则 4 — 前端表单 rules 必须对齐后端 @Size / @NotBlank

后端 `@Size(min = 8, max = 32)` ↔ 前端 `formRules.min/max` 必须一致；`@NotBlank` ↔ `required: true`；`@Email` ↔ `type: 'email'`；`@Size(max)` 同时对齐输入框 `:maxlength`。

### 检查清单
- [ ] `@Size(min/max = N)` 与 `formRules.field.min/max === N`
- [ ] `@NotBlank` 对应 `required: true`；`@Email` 对应 `type: 'email'`

---

## 规则 5 — `updateById` 前必须显式校验存在性

### 反模式
```java
public Boolean modify(ModifyXxxOperate operate) {
    XxxEntity entity = ConvertAid.convert(operate, XxxEntity.class);
    return this.updateById(entity);  // ❌ ID 不存在时静默成功（affected rows = 0）
}
```

### 正确模式
```java
public Boolean modify(ModifyXxxOperate operate) {
    Asserts.notNull(this.getById(operate.getId()), ErrorMsg.RECORD_NOT_FOUND);
    XxxEntity entity = ConvertAid.convert(operate, XxxEntity.class);
    return this.updateById(entity);
}
```

### 检查清单
- [ ] 所有 `updateById()` / `deleteById()` 调用前有 `Asserts.notNull(this.getById(id), ...)` 存在性校验
- [ ] `deleteByQuery()` 不需要校验（按条件批量删除）

---

## 触发后的输出格式

```markdown
## API 契约检查结果

### ✅ 通过的规则
- 规则 X：[简述]

### ⚠️ 违反的规则
- 规则 X：[文件路径:行号] - [具体问题]
  - 建议修复：[最小改动方案]

### ❓ 需要人工确认
- [文件路径:行号] - [无法自动判定的情况]
```

如全部通过：`✅ API 契约检查通过`。

发现违规且属于本次变更引入的 → dev-session P4 中自修；属于存量代码的 → 按 `similar-issue-sweep` 报告，由开发者决定排期。

---

## 关联

- 项目根 `CLAUDE.md` — Cross-Cutting Contracts（项目专属契约叠加于本 skill 之上）
- `.claude/skills/yzj-dev-workflow` — 后端开发流程
- `frontend/reviewer` 与 `backend/reviewer` — P4 审查时本 skill 作为跨端维度
