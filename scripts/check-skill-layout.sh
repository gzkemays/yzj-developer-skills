#!/usr/bin/env bash
# 校验技能目录布局（主文件引导式）：
#   告警（不阻断）：流程技能 SKILL.md > 8KB（规范技能 > 16KB）且无「## 约束卡」；带约束卡的主文件 > 8KB；
#                   references/ templates/ 子文件 > 12KB
#   失败（阻断）  ：主文件引用的技能内 references/*.md、templates/*.md 不存在；references/ templates/ 下存在主文件未引用的孤立文件；
#                   带约束卡的技能，其 references/*.md 前 5 行缺 "> 门禁" 行；references/*.md 引用同技能的另一个 references/ 文件
# 阈值只是提醒：规则会随能力累积增长，不做硬限制（见 reports/2026-10-30-context-compaction-resilience-plan.md 决策 13）。
# 用法：bash scripts/check-skill-layout.sh [技能根...]   默认扫 common/skills backend frontend；
#       也可传目标项目的技能目录（绝对路径或相对当前目录）；含 dev-session / git-commit 的根按流程技能阈值（8KB），其余 16KB
set -u
ORIG_PWD=$PWD
cd "$(dirname "$0")/.." || exit 1
ROOTS=("$@"); [ ${#ROOTS[@]} -eq 0 ] && ROOTS=(common/skills backend frontend)
MAIN_LIMIT=8192; SPEC_LIMIT=16384; SUB_LIMIT=12288
WARN=0; FAIL=0
warn() { echo "ℹ $*"; WARN=$((WARN+1)); }
fail() { echo "✗ $*"; FAIL=$((FAIL+1)); }
size() { wc -c < "$1" | tr -d ' '; }
# 主文件里形如 references/x.md、templates/x.md 的本技能引用（排除 templates/AGENTS.md.template 这类更长文件名，
# 也排除 ../other/references/x.md、common/skills/x/references/y.md 这类带前缀路径的跨技能引用）
refs_in() { grep -oE '(^|[^/A-Za-z0-9_.-])(references|templates)/[A-Za-z0-9._-]+\.md([^A-Za-z0-9._-]|$)' "$1" \
  | sed -E 's/^[^rt]*//; s/[^A-Za-z0-9._-]$//' | sort -u; }

for root in "${ROOTS[@]}"; do
  root=${root%/}
  # 显式传入的相对路径按调用者当前目录解析（默认根已是仓库相对路径）；不存在的根明确报失败，不回退到本仓库同名目录静默通过
  case "$root" in
    /*|[A-Za-z]:*) ;;
    *) if [ $# -gt 0 ]; then root="$ORIG_PWD/$root"; fi;;
  esac
  root=${root#./}; root=${root%/.}
  [ -d "$root" ] || { fail "技能根不存在：$root"; continue; }
  # 含流程技能（dev-session / git-commit）的根用 8KB 阈值，纯规范技能根（backend / frontend 及其目标项目拷贝）用 16KB
  limit=$SPEC_LIMIT; { [ -d "$root/dev-session" ] || [ -d "$root/git-commit" ]; } && limit=$MAIN_LIMIT
  for dir in "$root"/*/; do
    dir=${dir%/}; main="$dir/SKILL.md"
    [ -f "$main" ] || continue
    name=$dir
    sz=$(size "$main")
    has_card=0; grep -q '^## 约束卡' "$main" && has_card=1
    if [ $has_card -eq 1 ]; then
      [ "$sz" -gt "$MAIN_LIMIT" ] && warn "$name/SKILL.md ${sz}B > ${MAIN_LIMIT}B（主文件偏大，考虑把细则移到 references/）"
    elif grep -q '必须全文加载' "$main"; then
      :  # 声明"必须全文加载"的兜底技能（reviewer）不拆分，只重排，不提示拆
    elif [ "$sz" -gt "$limit" ]; then
      warn "$name/SKILL.md ${sz}B > ${limit}B 且无「## 约束卡」——压缩后只保留开头，建议拆为主文件 + references/ 子文件"
    fi
    for sub in references templates; do
      [ -d "$dir/$sub" ] || continue
      for f in "$dir/$sub"/*.md; do
        [ -f "$f" ] || continue
        rel="$sub/$(basename "$f")"
        s=$(size "$f"); [ "$s" -gt "$SUB_LIMIT" ] && warn "$name/$rel ${s}B > ${SUB_LIMIT}B（子文件偏大）"
        grep -qF "$rel" "$main" || fail "$name/$rel 未被主文件引用（孤立文件：在主文件路由表加引用，或删除）"
        if [ $has_card -eq 1 ] && [ "$sub" = references ] && ! head -n 5 "$f" | grep -q '^> 门禁'; then
          fail "$name/$rel 前 5 行缺「> 门禁」行（子文件被单独读到时也须带自己的门禁）"
        fi
        # references/ 之间不互引，只由主文件路由（templates 与其所属阶段子文件互指门禁行允许）
        if [ "$sub" = references ]; then
          for other in $(grep -oE 'references/[A-Za-z0-9._-]+\.md' "$f" | sort -u); do
            [ "$other" = "$rel" ] && continue
            [ -f "$dir/$other" ] && fail "$name/$rel 引用了同级 $other（references 之间不互引，改为经主文件路由）"
          done
        fi
      done
    done
    # 主文件引用的本技能子文件必须存在——无论子目录是否存在（删目录忘改路由表正是要拦的错误）。
    # 仓库级 templates/ 的引用形如 templates/AGENTS.md.template、templates/.document/…，不被 refs_in 的正则命中。
    for ref in $(refs_in "$main"); do
      [ -f "$dir/$ref" ] || fail "$name/SKILL.md 引用的 $ref 不存在"
    done
  done
done

echo "──────── 小结 ────────"
echo "ℹ 告警 $WARN   ✗ 失败 $FAIL"
[ "$FAIL" -gt 0 ] && exit 1
exit 0
