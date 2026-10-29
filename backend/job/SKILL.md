---
name: job
description: yzj-job-spring-boot-starter 任务调度使用指南（去 Quartz、仅依赖数据库、可观测）。当需要编写定时任务 / 延时任务 / 广播任务（@YzjJob、JobHandler、cron / fixedRate / fixedDelay）、按商户等维度并行处理（ctx.fanOut）、手动触发 / 暂停 / 覆盖 cron（JobOperations / 管理 API）、查看执行记录与实时日志、配置告警（企业微信 / 邮件）、处理多实例重复执行 / Flyway 建表冲突 / 表前缀时使用此 skill；从旧 Quartz 版 yzj-job（invokeTarget、job_info / qrtz_*）迁移时也使用。
---

# yzj-job-spring-boot-starter 任务调度

> 定位：**不引入 Quartz / Redis / ZK / 调度中心**，只依赖业务已有的数据库（MySQL；H2 用于单测）。
> 多实例（含蓝绿切换重叠期）下每次触发**至多执行一次**，执行记录、实时日志、指标、告警开箱即用。
> 设计文档：framework `.document/design/2026-10-29_yzj-job-scheduler-design.md`。

---

## 一、快速接入

```xml
<dependency>
    <groupId>com.yeziji</groupId>
    <artifactId>yzj-job-spring-boot-starter</artifactId>
</dependency>
```

前提：容器中有 `DataSource`（缺失时启动失败，不会静默降级——静默降级会在多实例下变成重复执行）。
不需要调度的应用：`yzj.job.enabled=false`。

```yaml
yzj:
  job:
    jdbc:
      initialize-schema: create-if-absent   # create-if-absent（默认）/ flyway / never
      table-prefix: yzj_job_                # 表前缀，避免与业务表重名（[A-Za-z0-9_]{0,32}）
    api:
      enabled: false                         # 管理 API，默认关闭；开启后必须用 security / 网关保护 path
      path: /yzj-job
    alarm:
      wecom:
        webhook: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
      mail:
        enabled: true                        # 还需 spring.mail.*
        to: [ ops@example.com ]
```

自动建表 5 张：`{prefix}info / run / run_item / run_log / node`。

---

## 二、编写任务

任务类放在 `integration/jobs/`，调用 domain Service（与 integration-flow 规范一致）。

### 2.1 方法注解（主推）

```java
@Slf4j
@Component
public class MerchantSyncJobs {
    @Resource
    private MerchantSyncService merchantSyncService;

    @YzjJob(name = "syncDrugAndStock",
            cron = "${jobs.sync-drug.cron:0 */30 * * * ?}",
            timeout = "10m", owner = "hwy", description = "按商户同步药品与库存",
            alarmTo = {"13800000000", "ops@example.com"})
    public String syncDrugAndStock(JobContext ctx, MerchantJobParams params) {
        List<Long> ids = merchantSyncService.resolveMerchantIds(params);
        return ctx.fanOut("merchant", ids, String::valueOf, merchantSyncService::syncDrugAndStock).summary();
    }
}
```

- 支持签名：`()`、`(JobContext)`、`(P)`、`(JobContext, P)`；P 为任意 POJO（参数在库中是 JSON，执行前反序列化），返回值写入执行记录 result。
- 任务以 `group.name` 唯一（group 默认 `DEFAULT`），**与方法名解耦**；name / group 只允许字母、数字、`_`、`-`。
- 触发器三选一：`cron`（Spring 6 语法，6 位）/ `fixedRate` / `fixedDelay`（`30s`、`10m`、`PT1H` 或毫秒）；都不填 = 仅手动 / 延时执行。
- 所有字符串属性支持 `${}` 占位符；签名、cron、重名在**启动期校验**，非法直接启动失败。

### 2.2 接口式（便于单测）

```java
@Component
@YzjJob(group = "cart", cron = "0 0 3 * * ?")
public class CleanExpiredCartJob implements JobHandler<Void> {
    @Override
    public Object execute(JobContext ctx, Void params) { ... }
}
```

### 2.3 注解属性速查

| 属性 | 默认 | 说明 |
|---|---|---|
| `timeout` | 不限 | 到时中断线程并置取消标记，状态 TIMEOUT（协作式，见 2.5） |
| `retry` / `retryBackoff` | 0 / 30s | 失败或超时后重试，指数退避（上限 `scheduler.retry-backoff-max`）；**非幂等任务保持 0** |
| `blockStrategy` | SKIP | 上次未结束：SKIP 记一条 SKIPPED / PARALLEL 并行 |
| `misfire` | FIRE_ONCE_NOW | 停机 / 失联错过触发：立即补跑一次 / SKIP 记录跳过（不会补跑全部错过次数） |
| `broadcast` | false | 每个存活且持有该任务的节点各执行一次（不支持 fixedDelay） |
| `params` | — | 默认参数 JSON（可被运维覆盖） |
| `alarmTo` | — | 手机号（企业微信 @ 人）/ 邮箱（邮件收件人） |

### 2.4 JobContext

| 方法 | 用途 |
|---|---|
| `ctx.log().info/warn/error` | 写执行日志（可实时 tail），同时写 slf4j |
| `ctx.isCancelled()` / `ctx.checkCancelled()` | 长循环中定期检查（超时 / 手动取消 / 停机 / 失联） |
| `ctx.wrap(Runnable / Callable / Executor)` | 业务自建线程时传递上下文：否则该线程的日志不归档、感知不到取消 |
| `ctx.fanOut(dim, items, keyFn, consumer)` | 本地并行处理子项，见 2.6 |
| `JobContext.current()` | 任意深度代码中取当前执行上下文 |

任务线程中业务代码自己的 `log.info(...)`（slf4j + Logback）会自动归档到执行日志，无需改代码。

### 2.5 取消是协作式的

Java 无法强杀线程。超时 / 取消只做两件事：置取消标记 + `interrupt()`。
- 阻塞 IO / `sleep` / `wait` 会被中断；
- 纯计算循环、不响应中断的第三方调用**不会停**——必须在循环里 `ctx.checkCancelled()`；
- fanOut 自动在子项之间检查取消。

### 2.6 fanOut（替代「按商户 for 循环」）

```java
FanOutResult r = ctx.fanOut(FanOutSpec.of("merchant").concurrency(8).continueOnError(true),
        merchantIds, String::valueOf, id -> syncOne(id));
```

- 每个子项一条记录（状态、耗时、异常），批量写库；
- 任一子项失败 → 本次执行 FAILED（`item_failed` 计数），其余子项照常处理（`continueOnError=false` 则停止后续子项）；
- **失败项单独重跑**：`JobOperations.retryFailedItems(runId)` / `POST /runs/{id}/retry-failed-items`，业务代码零改动（fanOut 自动只处理失败 key）；
- key 必须在本次执行内唯一、不超过 255 字符；
- 只在本 JVM 内并行，不做跨节点分片。

---

## 三、运维操作

注入 `JobOperations`（任何时候可注入，引擎启动后可用）：

```java
jobOperations.trigger("DEFAULT.syncOrder", "{\"merchantIds\":[1,2]}", operator);   // 立即执行
jobOperations.schedule("DEFAULT.syncOrder", null, fireAtMillis, operator);          // 一次性延时任务
jobOperations.pause / resume("DEFAULT.syncOrder");
jobOperations.overrideTrigger("DEFAULT.syncOrder", "0 */10 * * * ?");             // null 恢复代码定义
jobOperations.cancel(runId);                                                         // 含同链未执行的重试
```

管理 API（`yzj.job.api.enabled=true`，前缀 `yzj.job.api.path`）：`GET /jobs`、`POST /jobs/{key}/pause|resume|trigger`、`PUT /jobs/{key}/override`、`DELETE /jobs/{key}`（仅孤立任务）、`GET /runs`、`GET /runs/{id}`、`/runs/{id}/items`、`/runs/{id}/logs?afterSeq=`、`POST /runs/{id}/cancel|retry-failed-items`、`GET /nodes`、`GET /broadcasts/{id}`。
**API 本身不鉴权**：开启时必须在 yzj-security / 网关中保护该路径。

**代码是定义的真源**：改注解（cron、超时……）重启即生效；运维覆盖（override cron / 参数 / 告警人、暂停）存在独立列，重启不会被代码覆盖。

---

## 四、可观测与告警

| 能力 | 位置 |
|---|---|
| 执行记录 | `{prefix}run`：WAITING / RUNNING / SUCCESS / FAILED / TIMEOUT / CANCELLED / SKIPPED / LOST / INTERRUPTED，含来源、尝试次数、节点、traceId、耗时、子项计数 |
| 实时日志 | `GET /runs/{id}/logs?afterSeq=`（每秒刷库，单次上限 `log.max-size-per-run`） |
| traceId | MDC `traceId` = 本次执行 traceId，现有日志 pattern 直接可检索 |
| 指标 | `yzj.job.run`、`yzj.job.fire.lag`、`yzj.job.run.active`、`yzj.job.fanout.items`、`yzj.job.scheduler.poll` |
| Actuator | `/actuator/yzjjob`；健康 `yzjJob` **只在调度器自身故障时 DOWN**（任务失败不影响探活） |
| Spring 事件 | `YzjJobRunEvent`（开始 / 结束） |
| 扩展点 | `JobRunListener`、`JobRunInterceptor`（如设置商户 / 租户上下文）、`JobNotifier`（自定义告警渠道） |
| 告警 | 最终失败 / 超时 / 节点失联；同任务同异常静默期内合并；连续失败后首次成功发恢复通知；内置企业微信、邮件（钉钉 / 飞书 TODO） |
| 数据保留 | 内置任务 `YZJ_JOB.retention`，默认保留 30 天 |

---

## 五、多实例语义（必读）

- 每次触发**至多执行一次**：靠数据库条件更新（CAS）抢占，不需要分布式锁；蓝绿切换重叠期安全。
- 节点失联（宕机 / 被 kill / 长 GC / 断库）：其执行记 **LOST**，**不会自动重跑**（框架无法判断是否幂等）——告警后人工决定是否 trigger。
- 失联节点上**尚未开始**的执行会按 misfire 策略释放给其他节点补跑。
- 被误判失联的节点会自我取消（fencing），其结果不会覆盖 LOST。
- 多节点负载靠轮询抖动自然均衡；广播任务每个存活节点各一条，节点失联那条记 LOST。
- 节点之间的时间比较以数据库时间为准，仍建议服务器开启 NTP。

---

## 六、建表与 Flyway

| `initialize-schema` | 行为 | 适用 |
|---|---|---|
| `create-if-absent`（默认） | 表不全时执行建表脚本；表已存在时**不执行任何 DDL**（生产无 DDL 权限也可）；**保证排在业务 Flyway / Liquibase 之后** | 绝大多数项目 |
| `flyway` | 独立 Flyway 实例 + 独立 history 表 `{prefix}schema_history`，与业务 Flyway 互不干扰；yzj-job 后续表结构升级自动执行 | 已使用 Flyway、希望表结构版本化 |
| `never` | 不建表，缺表启动失败并提示脚本位置 | 运维 / DBA 统一管理 DDL（如 ERP 云端实例） |

- 脚本位置：`yzj-job.jar!/META-INF/yzj-job/db/{mysql|h2}/V*.sql`，占位符 `${yzj_job_prefix}`。
- 若把脚本复制进业务自己的 Flyway 迁移：配置 `spring.flyway.placeholders.yzj_job_prefix=yzj_job_`，否则 Flyway 报占位符未定义。

---

## 七、禁止与易错

| ❌ 错误 | ✅ 正确 |
|---|---|
| 需要执行记录 / 手动触发 / 多实例互斥的业务任务仍用 `@Scheduled` | 用 `@YzjJob`；`@Scheduled` 只留给无需记录的本地轻量维护（如清理本地缓存） |
| 业务自己 `new Thread` / `CompletableFuture` 不包装 | `ctx.wrap(...)`，否则日志丢失、取消无效 |
| 长循环不检查取消 | 循环内 `ctx.checkCancelled()` |
| 非幂等任务配置 `retry > 0` | 保持 0，失败靠告警 + 人工 trigger |
| 期待 LOST 自动重跑 | LOST 只告警，需人工判断后 trigger |
| 任务方法写成 static / 两个业务参数 | 实例方法，参数合并为一个对象 |
| 开启管理 API 但不加鉴权 | security / 网关保护 `yzj.job.api.path` |
| 业务表也叫 `info` / `run` 且前缀设为空串 | 保持默认前缀或使用业务相关前缀 |
| 在 starter / 框架代码里写嵌套 `@Configuration` 做条件装配 | 拆成独立 `@AutoConfiguration`（扫描根包为 `com.yeziji` 时嵌套配置会被提前扫描，条件失效） |

---

## 八、从旧 Quartz 版迁移（drug-supply-mall-service 等）

前提：项目已升级 Spring Boot 3 / Java 21。

| 旧 | 新 |
|---|---|
| `@YzjJobBean` 类 + `@YzjJob(value = 方法名, cron)`，value 必须等于方法名 | `@YzjJob(name = 任意, cron)` 标在方法上，与方法名无关 |
| `JobHandler.java` 汇总 + `*JobsHandler` 实现 | 直接在 `integration/jobs/*Job` 上标注，删除汇总层 |
| `String params` 手动 JSON 解析 | 方法参数直接声明为参数对象 |
| 按商户 for 循环 | `ctx.fanOut("merchant", ...)` |
| `YzjJobLogger` | `ctx.log()`（或直接用 slf4j，自动归档） |
| `job_info` / `job_log` / 11 张 `qrtz_*` | `yzj_job_*` 5 张（前缀不同，可并存；确认无误后再删旧表） |
| `/yzjJob/**` 管理接口 | `yzj.job.api.path`（默认 `/yzj-job`），接口形态不同，前端需调整 |
| BackdoorJobController 直接调 handler（绕过记录与互斥） | `JobOperations.trigger(...)` |

步骤：引入 starter → 改注解与签名 → 本地 H2 / 测试库验证 → 上线后观察 `yzj_job_run` → 停用旧 starter 并清理 `qrtz_*` 与旧表（DDL 走项目迁移流程）。
