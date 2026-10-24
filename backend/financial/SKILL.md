---
name: financial
description: YZJ 后端金融级规范。当代码涉及金额、余额、交易、支付、转账、结算、对账、账户流水、退款、优惠抵扣等资金语义，或 pre-dev-alignment 命中「支付/资金」风险关键词时使用此 skill。覆盖金额类型与运算（BigDecimal）、写操作幂等（业务唯一键 + @DistributedLock）、事务边界与异常、余额扣减一致性（行锁 / 乐观锁）、审计流水、脱敏展示；reviewer 金融维度据此审查。
---

# YZJ 后端金融级规范

> 触发关键词（命中任一即按本 skill 执行，Review 走金融维度）：
> `amount` `balance` `transaction` `payment` `pay` `transfer` `settlement` `clearing` `reconcil` `ledger` `refund` `wallet` `fund` `fee` `金额` `余额` `交易` `支付` `转账` `结算` `对账` `流水` `退款`
>
> 资金代码的错误不可逆、难追溯，本 skill 全部是硬规则；"业务简单 / 金额很小"不是降级理由。

---

## 一、金额类型与运算（强制）

**Java 类型**：`BigDecimal`。禁止 `float` / `double` / `int` / `long`（以分为单位的 `long` 仅限与外部系统对接的边界层，进入业务层即转 `BigDecimal`）。
**数据库类型**：`DECIMAL(19, 4)`（见 `database-design` 4.2，精度按项目实际确定）。

```java
// ✅ 正确
BigDecimal amount = new BigDecimal("100.00");                       // 字符串构造
BigDecimal total  = amount.add(fee);                                 // 运算用 add / subtract / multiply
boolean same      = amount.compareTo(other) == 0;                    // 比较用 compareTo
BigDecimal share  = total.divide(count, 4, RoundingMode.HALF_UP);    // divide 必须指定精度 + 舍入
BigDecimal shown  = amount.setScale(2, RoundingMode.HALF_UP);        // 展示位数只在出口处理

// ❌ 禁止
new BigDecimal(100.00);          // double 构造，精度不可控（0.1 会变成 0.1000000000000000055…）
amount.equals(other);            // equals 连 scale 一起比（1.0 ≠ 1.00）
amount == other;                 // 引用比较
total.divide(count);             // 除不尽直接抛 ArithmeticException
double fee = 0.1 + 0.2;          // 0.30000000000000004
```

| 规则 | 说明 |
|------|------|
| 字符串 / `BigDecimal.valueOf(long)` 构造 | 禁止 `new BigDecimal(double)` |
| 比较只用 `compareTo` | `equals` 含 scale，`==` 比引用 |
| `divide` 必须带 scale + `RoundingMode` | 舍入模式按业务定（结算 HALF_UP、手续费 UP / DOWN 由业务文档明示），不用默认 |
| 中间结果不截位 | 只在落库 / 展示的出口 `setScale`，链路中间保留全精度 |
| 分摊 / 拆单要"补差" | N 份之和必须等于总额：最后一份 = 总额 − 前 N−1 份之和 |
| 金额字段 Query 用 `BigDecimalRange` | 范围查询不用两个裸字段（见 `mybatis` skill） |
| 零值用 `BigDecimal.ZERO` | 不 `new BigDecimal("0")` |

---

## 二、写操作幂等（强制）

所有会产生资金变动的写操作（下单、支付、退款、转账、充值、结算）必须幂等：**同一业务请求重复到达，结果与首次一致，不重复扣款 / 入账**。

YZJ 没有单独的幂等组件，按以下组合实现：

### 2.1 业务唯一键（第一道，必须）

每笔资金操作有唯一的业务单号（`orderNo` / `paymentNo` / `refundNo`），对应表建**唯一索引**。重复请求在插入时被唯一索引拦下 → 捕获后**返回首次结果**而非报错。

```java
@Override
public PaymentDTO createPayment(AddPaymentOperate operate) {
    PaymentEntity exist = this.queryChain()
            .where(PaymentEntity::getPaymentNo).eq(operate.getPaymentNo())
            .one();
    if (exist != null) {
        log.info("[创建支付] 重复请求按幂等返回: paymentNo={}", operate.getPaymentNo());
        return PaymentConvertAid.convertToDto(exist);           // 返回首次结果，不抛异常
    }
    // ... 校验 → 构建 → insert（唯一索引兜底并发窗口，DuplicateKey 时再查一次返回）
}
```

### 2.2 `@DistributedLock` 串行化（第二道，并发入口必加）

同一业务键的并发请求用框架分布式锁串行化，锁 key 取**业务单号或账户 ID**，不用用户 ID 这种粗粒度键：

```java
@DistributedLock(key = "#operate.paymentNo", prefix = "payment:create",
        waitTime = 3000, leaseTime = -1, failMessage = "支付处理中，请勿重复提交",
        transactional = true)   // 锁在事务提交 / 回滚后才释放，避免锁先释放、事务未提交
@Transactional(rollbackFor = Exception.class)
public PaymentDTO createPayment(AddPaymentOperate operate) { ... }
```

- 锁内先查后写（2.1），锁只负责把并发变串行，幂等判断仍靠业务唯一键
- `transactional = true` 是资金场景的默认选项（见 `cache` skill 三）
- 接口层防重复点击用 `@ApiLock`（USER_ID + PARAMS 维度），它是**限流不是幂等**，不能替代本节

### 2.3 幂等结果缓存（可选，第三道）

对外部重试频繁的接口，可用 `cacheService.putIfAbsent(idempotencyKey, "processing", 24, TimeUnit.HOURS)` 快速挡掉重复请求；业务失败时**必须删 key** 允许重试，成功后写入结果。只作为性能优化，不替代 2.1。

### 2.4 禁止

- 只靠 `@ApiLock` / 前端禁用按钮当幂等
- 重复请求抛"重复提交"异常给调用方（应返回首次结果；确需拒绝的场景由业务文档明示）
- 幂等键用时间戳 / 随机数（每次都不同，等于没有）

---

## 三、事务边界与异常（强制）

```java
// ✅ 事务在 Service / Flow 的编排方法上，显式 rollbackFor
@Transactional(rollbackFor = Exception.class)
public void transfer(TransferOperate operate) {
    accountService.deduct(operate.getFromId(), operate.getAmount());   // 被编排方不加 @Transactional，融入调用方事务
    accountService.credit(operate.getToId(), operate.getAmount());
    ledgerService.add(LedgerConvertAid.of(operate));                   // 流水与资金变动同一事务
}
```

| 规则 | 说明 |
|------|------|
| `@Transactional(rollbackFor = Exception.class)` | 不写 `rollbackFor` 时受检异常不回滚 |
| 事务在 Service / Flow，不在 Controller | 跨域资金编排在 `integration/business/{业务}/Flow`（见 `integration-flow`） |
| 被编排方不开新事务 | 禁止被调用方 `REQUIRES_NEW` 绕开主事务——部分提交 = 资金不一致 |
| 事务内禁止吞异常 | `try { } catch (Exception e) { log… }` 不 rethrow → 事务不回滚但资金已改 |
| 事务内禁止 `this.method()` 调自身事务方法 | Spring 代理失效；注入自身 Bean 或拆到另一个 Bean |
| 事务内不做外部调用 | 支付网关 / MQ / 通知走 `TransactionUtils.asyncExecuteAfterCommit`（reviewer #20 / #21）——事务未提交先通知下游 = 幽灵交易 |
| 事务尽量短 | 不在事务内做大查询、远程调用、循环逐条写 |

---

## 四、余额扣减与一致性（强制）

余额类字段（账户余额、可用额度、资金池）的变更必须满足"查 → 校验 → 改"在同一把锁 / 同一事务内：

```java
// 方式 A：行锁（推荐，数据库兜底）—— XML 实现 SELECT … FOR UPDATE
AccountEntity account = accountMapper.selectByIdForUpdate(accountId);
Asserts.isTruth(account.getBalance().compareTo(amount) >= 0, AccountErrorMsg.INSUFFICIENT_BALANCE);
int affected = accountMapper.deductBalance(accountId, amount);
// UPDATE account SET balance = balance - #{amount} WHERE id = #{id} AND balance >= #{amount}
Asserts.isTruth(affected == 1, AccountErrorMsg.DEDUCT_FAILED);

// 方式 B：乐观锁（version 字段，读多写少）
// UPDATE account SET balance = balance - ?, version = version + 1 WHERE id = ? AND version = ? AND balance >= ?
// affected rows == 0 → 抛 ApiException 让调用方重试，禁止静默成功
```

- 扣减 SQL 带 `balance >= amount` 条件，`affected rows` 必须校验（0 行 = 扣减失败）
- **禁止**先 `getById` 读余额、Java 里减、再 `updateById` 整行覆盖——并发下丢更新
- 每次余额变动**必写流水**（第五节），余额 = 流水累加 是对账的前提
- 跨账户转账：扣减与入账在同一事务；多账户加锁按账户 ID 升序，防死锁

---

## 五、审计流水（强制）

以下操作必须写独立的流水 / 审计记录，且与资金变动**同一事务**：

- 账户余额变更（任何方向）
- 交易创建 / 状态变更（待支付 → 已支付 → 已退款 …）
- 退款、转账、结算、调账、人工冲正
- 资金相关权限变更

**记录必含**：时间、操作人 ID（`SessionContext`；系统任务填 0 并写明任务名）、操作类型、业务单号、系统流水号、金额、变动前余额、变动后余额、操作结果、来源 IP（`ServletInfo::getIp`）。

**禁止**：流水被物理删除或修改——只允许追加冲正记录；流水表不走逻辑删除字段。

---

## 六、脱敏与展示

| 数据 | 展示规则 | 示例 |
|------|----------|------|
| 手机号 | 前 3 + `****` + 后 4 | `138****8888` |
| 银行卡号 | `****` + 后 4 | `****1234` |
| 身份证号 | 前 3 + `****` + 后 4 | `110****123X` |
| 卡号 PAN / CVV / PIN | 永不存储、永不记日志、永不返回明文 | 见 `security` skill 第八节 |

- 脱敏在 **VO 转换**处做（Controller 层 `CommonResult.success(data, fn)`），Service 返回的 DTO 保持原值供内部计算
- 存储层敏感字段加 `@Encryption`（见 `mybatis` skill）
- 日志按 `logging` skill 第五节：金额可打，卡号 / 密码不可打；**框架 `LoggerFilter` 会打全量 body**，含卡号 / 密码的接口必须进 `yzj.logger.ignore-request-url` / `ignore-response-url`（见 `logging` skill 第九节）

---

## 七、自检清单（编码后、Review 前逐条过）

```
- [ ] 金额全部 BigDecimal；无 double 构造；比较用 compareTo；divide 带 scale + RoundingMode
- [ ] 分摊 / 拆单有补差，N 份之和 = 总额
- [ ] 每个资金写操作：业务单号唯一索引 + 先查后写按幂等返回 + @DistributedLock(transactional = true)
- [ ] 编排方法 @Transactional(rollbackFor = Exception.class)；被编排方不开新事务；无吞异常；无 this. 调自身事务方法
- [ ] 外部调用 / MQ / 通知在 afterCommit 之后
- [ ] 余额扣减：行锁或乐观锁 + SQL 带余额条件 + affected rows 校验；无"读-减-整行覆盖"
- [ ] 每次余额变动同事务写流水，流水含前后余额
- [ ] 卡号 / 密码不入日志不返回；接口已加入 LoggerFilter 忽略清单
- [ ] 单元测试覆盖：幂等重复请求、余额不足、affected rows = 0、回滚、分摊精度、并发扣减（见 `testing` skill 4.2）
```

---

## 八、禁止事项清单

| # | 禁止事项 | 严重程度 |
|---|----------|:--------:|
| 1 | 金额用 `float` / `double`，或 `new BigDecimal(double)` | 🔴 严重 |
| 2 | 金额比较用 `equals` / `==` | 🔴 严重 |
| 3 | `divide` 不指定精度与舍入模式 | 🔴 严重 |
| 4 | 资金写操作无幂等（无唯一索引、无先查后写） | 🔴 严重 |
| 5 | 幂等只靠 `@ApiLock` / 前端防抖 | 🔴 严重 |
| 6 | `@Transactional` 缺 `rollbackFor = Exception.class` | 🔴 严重 |
| 7 | 事务内 `catch` 吞异常不 rethrow | 🔴 严重 |
| 8 | 被编排方法 `REQUIRES_NEW` 绕开主事务 | 🔴 严重 |
| 9 | 事务内同步调外部系统 / 发 MQ | 🔴 严重 |
| 10 | 余额"读-减-整行覆盖"，无行锁 / 乐观锁 | 🔴 严重 |
| 11 | 扣减 SQL 无余额条件或不校验 affected rows | 🔴 严重 |
| 12 | 资金变动不写流水，或流水不在同一事务 | 🔴 严重 |
| 13 | 流水可改可删 | 🔴 严重 |
| 14 | 卡号 / CVV / PIN / 密码出现在日志、响应、非加密存储 | 🔴 严重 |
| 15 | 含敏感 payload 的接口未进 `LoggerFilter` 忽略清单 | 🔴 严重 |
| 16 | 分摊不补差，各份之和 ≠ 总额 | 🟡 警告 |
| 17 | 链路中间 `setScale` 截位 | 🟡 警告 |
