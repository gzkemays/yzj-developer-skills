# pre-dev-alignment · 开发前检查清单

> 门禁：每个计划必须包含本清单（按技术栈 / 场景 / 风险选取），是进入编码阶段的前置门禁；HIGH RISK 的关键风险附加项全部通过才可编码。

### 通用（所有场景）

```
- [ ] 技术栈已确认：前端 / 后端 / 前后端联动
- [ ] 场景类型已确认：A / B / C；风险等级已确认：LOW / HIGH
- [ ] 已查 memory（相关约束）与能力登记册（可复用清单）
- [ ] 计划已落档 + 台账已登记；砍掉 / 推迟的功能点已落 `plan/backlog-*.md`
- [ ] 联动需求：「契约」章节已冻结并经确认（纯单端写"不涉及"）
```

### 后端通用

```
- [ ] 涉及业务域已确认（新建 / 已有）；层归属已确认（domain / integration / interfaces / support）
- [ ] 接口类型已确认（api / sdk / grpc）；CommonResult/CommonPage 包装结构已确认
```

### 后端场景 B/C 附加

```
- [ ] 已读取同业务域现有代码，确认代码风格
- [ ] 已确认现有 Service 方法命名（get/getXxxList/statistics/add/update/remove）
- [ ] 已确认现有 Controller 路径结构（/v{n}/{平台}/{业务}）
- [ ] 已确认 Operate / Query 是否继承 CommonOperate / CommonQuery<T>
```

### 后端场景 C 附加

```
- [ ] 影响面分析已完成（受影响的 Service、Controller、Mapper、QueryChain）+ 调用链已列出
- [ ] 回滚方案已制定；改动范围已约束（外科手术式，只改必要的）
```

### 后端跨业务域写操作附加

```
- [ ] 跨业务域写操作放在 integration/business/{业务}/Flow 中（禁止 domain Service 处理）
- [ ] Flow 通过 Service 操作数据库（禁止直接操作 Mapper）；必要时已使用 @Transactional
```

### 后端关键风险附加

```
- [ ] 权限/鉴权：已确认 SessionContext / SecurityToken 使用方式
- [ ] 缓存：@CacheRead/@CachePut/@CacheEvict 注解和 key 命名已确认
- [ ] 分布式锁：@DistributedLock 的 key、prefix、waitTime、leaseTime 已确认
- [ ] DDL：TableDef 已按 `tabledef` skill 同步维护方案确认
- [ ] proto：字段编号未复用（删除需 reserved）；敏感字段已加 @Encryption
- [ ] 支付/资金：金额 BigDecimal、业务单号唯一索引 + 幂等、@DistributedLock(transactional)、行锁、同事务流水（`financial` skill）
- [ ] 对外接口 / SDK / proto 变更：对接文档同一次提交更新
- [ ] 含敏感 payload 的接口：加入 yzj.logger.ignore-request-url / ignore-response-url
```

### 前端通用

```
- [ ] 涉及页面/模块已确认；组件方案已确认（新建 / 复用 / 改造）
- [ ] 已确认可参考的 frontend skill（view-conventions / i18n-automation 等）
```

### 前端场景 B/C 附加

```
- [ ] 已读取同模块现有页面代码，确认结构与风格
- [ ] 已确认组件命名规范和拆分粒度；路由结构和菜单配置方式
- [ ] 已确认数据请求方式与后端接口对接的数据结构
```

### 前端场景 C 附加

```
- [ ] 影响面分析已完成（受影响的页面、组件、store、路由）+ 组件引用链已列出
- [ ] 改动范围已约束；公共组件修改已评估对其他页面的影响
```

### 前端关键风险附加

```
- [ ] 全局状态：store 结构和影响范围已确认
- [ ] 路由/权限：路由守卫逻辑和菜单权限配置已确认
- [ ] 公共组件：被引用位置和使用方式已确认
- [ ] 第三方库：版本、bundle 体积、按需加载已确认
- [ ] 国际化：i18n key 命名规范和 locale 文件更新已确认
- [ ] 全局样式：CSS 变量/主题变量影响范围已确认
```
