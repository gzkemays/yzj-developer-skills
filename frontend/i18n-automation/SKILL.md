---
name: i18n-automation
description: 自动化管理 Vue 项目 i18n 文案与合规检查。用户提到国际化、i18n、多语言补齐、硬编码提示、翻译缺失、locale 同步、app.d.ts key 校验时都应优先使用本 Skill，尤其是需要“批量检查+自动修复+输出报告”的场景。
---

# i18n Automation

用于约束“所有面向用户文案必须 i18n 化”，并提供自动补齐翻译、结构化校验与硬编码审计能力。

## 适用场景

- 新增页面或功能后，批量补齐多语言文案。
- 对 `src/locales/langs` 做一致性检查（缺失、空值、重复、未登记 key）。
- 审计 `src` 下硬编码文案并给出替换 key 建议。
- 要求输出可读 diff 的变更清单与合规性报告。

## 输入约定

- Schema 权威文件：`src/typings/app.d.ts`
- 语言目录：`src/locales/langs`
- 基准语义语言：`zh-cn.ts`
- 目标语言：扫描到的所有非 `zh-cn` 语言文件

## 执行步骤

1. 先解析 `app.d.ts` 的 `App.I18n.Schema`，提取完整 key 字典。
2. 解析 `src/locales/langs/*.ts`，建立每个语言文件的扁平 key-value 索引。
3. 对比 `zh-cn` 与其它语言：
   - 找出缺失翻译、空值、重复 key；
   - 找出不在 schema 中登记的 key。
4. 扫描业务代码中的硬编码明文（`vue/ts/tsx/js/jsx`）：
   - 只关注用户可见文案；
   - 忽略 URL、纯变量、日志类调试文本与明显非 UI 文本。
5. 对新增中文文案先理解业务语义，再翻译到各目标语言：
   - 用词简洁、语义明确；
   - 保留占位符格式（如 `{count}`）；
   - 保留快捷键提示（如 `(Ctrl+S)`）。
6. 写回语言文件时保持：
   - 原对象层级结构不变；
   - 新增/修改 key 按字母序插入；
   - 仅增量变更，方便 diff 审阅。
7. 输出标准块：
   - `LANG_FILE_UPDATES`
   - `I18N_VALIDATION`
   - `HARD_CODED_REPORT`

## 输出规范

### LANG_FILE_UPDATES

- 语言维度分组（例如 `en-us.ts`、`fr-fr.ts`）
- 每组列出 `added`、`modified`、`deleted`

### I18N_VALIDATION

- `missing_in_schema`
- `missing_translation`
- `duplicate_keys`
- `empty_values`

### HARD_CODED_REPORT

- `file`: 文件路径
- `snippet`: 触发片段
- `literal`: 硬编码文案
- `suggested_key`: 建议 i18n key（例如 `page.order.detail.fetchFailed`）

## 推荐脚本

优先执行以下脚本（位于本 Skill 的 `scripts/`）：

1. `python scripts/extract_schema_keys.py --app-dts <path>`
2. `python scripts/parse_locale_files.py --langs-dir <path>`
3. `python scripts/validate_i18n_integrity.py --app-dts <path> --langs-dir <path>`
4. `python scripts/detect_hardcoded_literals.py --src-dir <path>`
5. `python scripts/sort_and_merge_keys.py --langs-dir <path> --updates <json-file>`

若用户要求“一次性执行”，可调用 `scripts/run_i18n_audit.py` 聚合以上步骤并打印统一报告。

## 质量要求

- 不得直接输出“建议硬编码”，必须给出 i18n key 方案。
- 翻译结果应避免冗长、机器腔和歧义表达。
- 当上下文不足以确定语义时，先标记 `needs_context` 再向用户提问补充。
