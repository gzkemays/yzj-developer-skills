# 技能库工作区更新复验报告

验证日期：2026-10-29（Asia/Tokyo）  
验证对象：基于 `7cded4dce4b37ec1058679157ad2f777ec79b997` 的当前未提交工作区更新。  
校验脚本 SHA-256：`c35515516b55ff45d307aad44d1fef6878f82a0530961f8c9a5741297850f10d`。  
上轮报告：[技能库更新复验报告](2026-10-29-skills-loading-update-validation.md)。

## 结论

原有 57 个场景全部符合预期，包括 38 个主场景、4 个语言环境对照及上轮新增的 15 个边界场景。上轮报告中的 8 个失败样例已全部修复，正常安装场景没有出现回归。

针对本次新增的轻量 frontmatter 读取器、BOM 处理、覆写声明位置及基线必要文件检查，补充 12 个定向场景，8 个符合预期、4 个不符合。剩余缺陷是：未闭合的 frontmatter 被接受、纯空白描述被接受、带尾随空格的引号名称被误报、带 BOM 的合法覆写被误判为漂移。因此，当前更新通过了上轮验收用例，但接入校验仍有四个可复现边界缺陷。

本轮尊重脚本声明的“轻量检查，刻意不做完整 YAML 校验”范围，只核对它已承诺处理的块边界、非空值、双引号与空白，以及已有 BOM 处理的一致性，不以完整 YAML 支持作为验收条件。

源库 34 份技能仍可发现和读取；名称、描述和提取到的具体资源引用检查未发现缺失。文件验证不能代替不同模型在目标项目新会话中的实际路由和业务执行验证。

## 验证结果

| 检查范围 | 本轮结果 | 与上轮比较 |
|---|---|---|
| 主场景 | 38 / 38 符合 | 保持通过 |
| C 与 C.UTF-8 对照 | 4 / 4 符合 | 保持通过 |
| 上轮边界场景 | 15 / 15 符合 | 从 7 / 15 提升，8 个失败样例修复 |
| 新增定向场景 | 8 / 12 符合 | 发现 4 个边界缺陷 |
| 合计 | 65 / 69 符合 | 错误样例被正确拒绝也算符合预期 |
| 技能文件 | 通用 13、后端 18、前端 3，共 34 份 | 必需字段检查无异常 |
| 资源引用 | 12 个提取到的具体文件引用全部存在 | 无缺失 |
| Python 文件 | 17 个通过 AST 语法解析 | 未执行辅助脚本业务功能或检查全部外部依赖 |

所有测试都在临时项目和基线副本上执行，结束后已清理。原有三个测试脚本逐字复用，未改动验收预期；原有 `override-after-line-20` 样例把声明追加到文件末尾，在新旧位置规则下都属于超出窗口，不影响可比性。新规则的精确第 20、21 行及长 frontmatter 已另外验证。

本轮测试记录的是工作区内容，而不是一个新提交。`results.json` 等旧脚本中的 revision 字段仍为 HEAD，必须结合 [source-manifest.json](validation-2026-10-29-worktree-c3551551/source-manifest.json) 的 41 个文件哈希及 [working-tree.patch](validation-2026-10-29-worktree-c3551551/working-tree.patch) 确认本轮版本。

## 上轮三类问题复核

| 问题 | 本轮结果 |
|---|---|
| 元数据按全文匹配 | 删除 frontmatter、仅正文代码块含字段，以及 description 没值、空字符串、空折叠块，均被正确拒绝；`name: "cache"` 正确接受 |
| 三个空目录被当作有效基线 | 现在返回 2；分别缺失通用 dev-session、后端 reviewer、前端 reviewer 必要文件，也都返回 2 |
| 描述中的锚点误认作覆写 | 现在按未声明漂移返回 1；真正的引用块声明仍可通过，C 与 C.UTF-8 结果一致 |

声明位置的新约定也按预期执行：frontmatter 结束后第 20 行的声明通过，第 21 行的声明被拒绝；frontmatter 本身超过 20 行时，其后的合法声明仍能识别。

## 剩余缺陷

### 一 未闭合的 frontmatter 被接受

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 64 至 76 行。

将目标 cache 技能改成下面三个字段行，并在文件末尾结束，不提供关闭分隔符：

```yaml
---
name: cache
description: Fixture description without closing boundary.
```

严格模式实际返回 0，一致 14、项目差异 1、结构错误 0。`read_fm` 在读到关闭分隔符时会退出，但没有记录是否真正遇到关闭分隔符；到达 EOF 后仍在 END 中输出已收集的字段。因此，不完整的 frontmatter 也会被当作有效头部。

建议显式记录开始与结束边界，仅在完整闭合时返回有效字段；EOF 前未闭合应计结构错误。这属于轻量块边界检查，不需要完整 YAML 解析。

### 二 只有空白的描述被当作非空

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 70 至 71 行。

将 cache 的描述改为 `description: "   "`，严格模式实际返回 0，一致 14、项目差异 1、结构错误 0。

当前先去尾部空白，再去双引号。由于空白位于引号内部，第一次处理没有去除它们；去掉引号后，剩余空格仍被 `v != ""` 判定为有效描述。纯空白描述无法提供技能路由信息。

建议在去除受支持的引号后再次清理首尾空白，再检查非空值。

### 三 带尾随空格的合法引号名称被误报

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 68 行。

将名称写为 `name: "cache"`，并在闭引号后添加三个空格，严格模式实际返回 1，误报名称为 `cache"`、与目录不同。没有尾随空格的相同引号名称已在回归场景中通过。

name 的处理顺序与 description 又不相同：先剥双引号，再去尾部空白。闭引号后有空格时，闭引号不在行末，剥引号步骤只移除了开引号。

建议统一字符串处理顺序：先清理字段值外围空白，再去掉成对的受支持引号，最后校验规范化后的值与目录是否一致。

### 四 BOM 处理在两次头部读取中不一致

位置：[verify-baseline.sh](../scripts/verify-baseline.sh) 第 64、183 行。

给包含合法覆写声明的 iteration-planner 文件增加 UTF-8 BOM，严格模式实际返回 1，一致 14、流程漂移 1、结构错误 0。相同声明不带 BOM 时可以通过；普通 cache 元数据带 BOM 的控制场景也可以通过。

`read_fm` 会在首行去除 BOM，因此名称与描述检查通过；计算 `fm_end` 的另一次 awk 读取却未做相同处理，无法识别首行分隔符，也就找不到后续声明窗口。

建议从同一次头部读取中返回字段及结束行号，或至少统一两处的 BOM 与换行处理，避免元数据有效但覆写识别失效。

## 新增场景明细

本组使用 13 个通用技能，加后端 cache 与 reviewer，共 15 份文件，以集中验证本次更新。未改动的控制场景为 15 份一致；修改一个技能后，正常比较基数为 14 份一致。

| 场景与证据 ID | 预期退出码 | 实际退出码 | 结论 |
|---|---|---|---|
| 未修改的 15 份技能控制样例<br>`control` | 0 | 0 | 符合 |
| 只有起始分隔符，直到 EOF 都未闭合<br>`unclosed-frontmatter` | 非零 | 0 | **不符合** |
| 双引号内只有空格的描述<br>`whitespace-only-quoted-description` | 非零 | 0 | **不符合** |
| 带尾随空格的双引号名称<br>`quoted-name-trailing-spaces` | 0 | 1 | **不符合** |
| 普通元数据含 UTF-8 BOM<br>`bom-metadata` | 0 | 0 | 符合 |
| 含 BOM 的合法覆写声明<br>`bom-declared-override` | 0 | 1 | **不符合** |
| frontmatter 后第 20 行声明<br>`declaration-post-fm-line-20` | 0 | 0 | 符合 |
| frontmatter 后第 21 行声明<br>`declaration-post-fm-line-21` | 非零 | 1 | 符合 |
| 长 frontmatter 后的合法声明<br>`long-frontmatter-valid-declaration` | 0 | 0 | 符合 |
| 基线缺通用 dev-session<br>`missing-sentinel-common` | 2 | 2 | 符合 |
| 基线缺后端 reviewer<br>`missing-sentinel-backend` | 2 | 2 | 符合 |
| 基线缺前端 reviewer<br>`missing-sentinel-frontend` | 2 | 2 | 符合 |

## 可复核证据与复现

| 文件 | 内容 |
|---|---|
| [source-manifest.json](validation-2026-10-29-worktree-c3551551/source-manifest.json) | 工作区身份、脚本哈希及 41 个源文件哈希 |
| [working-tree.patch](validation-2026-10-29-worktree-c3551551/working-tree.patch) | 本轮测试前的三处未提交源文件差异 |
| [results.json](validation-2026-10-29-worktree-c3551551/results.json) | 38 个主场景的完整命令、退出码与输出 |
| [locale-results.json](validation-2026-10-29-worktree-c3551551/locale-results.json) | 4 个语言环境对照结果 |
| [boundary-results.json](validation-2026-10-29-worktree-c3551551/boundary-results.json) | 上轮 15 个边界场景的本轮结果 |
| [edge-results.json](validation-2026-10-29-worktree-c3551551/edge-results.json) | 新增 12 个场景的预期、结果和完整输出 |
| [static-results.json](validation-2026-10-29-worktree-c3551551/static-results.json) | 34 份技能清单、资源和语法检查、旧测试脚本一致性 |

在仓库根目录使用 Python 3 与 Git Bash，分别运行：

```text
python reports/validation-2026-10-29-worktree-c3551551/validate.py --bash <bash.exe路径> --jobs 4
python reports/validation-2026-10-29-worktree-c3551551/check_locale.py --bash <bash.exe路径>
python reports/validation-2026-10-29-worktree-c3551551/check_boundaries.py --bash <bash.exe路径> --jobs 2
python reports/validation-2026-10-29-worktree-c3551551/check_frontmatter_edges.py --bash <bash.exe路径> --jobs 2
```

结果文件会被对应脚本覆盖。复验新版本时应复制本轮证据到新目录，并重新记录当前版本的 source-manifest.json；新增定向脚本会拒绝与清单不一致的源文件，避免误把不同版本的结果混在一起。验收看结果 JSON 的 `matches_expectation` 和日志，测试脚本自身返回成功不代表所有样例符合预期。

本轮只新增验证报告、测试脚本和证据文件，保留用户已有的未提交修改及前次报告。
