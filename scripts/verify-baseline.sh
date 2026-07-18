#!/usr/bin/env bash
# verify-baseline.sh — 校验目标项目的 skill 是否与 framework 基线对齐。
#
# 布局无关：按「标志文件」自动识别项目里每个 .claude/skills 属于 后端 / 前端 / 根，
# 再对应到 framework 的 backend/ · frontend/ · .claude/skills/ 逐一比对。不依赖仓库目录叫什么名字。
#
# 用法（在 Git Bash / WSL 运行；PowerShell 用 `bash scripts/verify-baseline.sh ...`）：
#   bash verify-baseline.sh <project-root> [framework-skills-root] [--show-diff] [--strict]
#     framework-skills-root  省略时 = 本脚本所在的 skills 仓库
#     --show-diff            打印每个差异 skill 的具体 diff
#     --strict               流程 skill 出现漂移即非零退出（默认仅结构错误才非零）
set -uo pipefail

PROJECT=""; FW=""; SHOW_DIFF=0; STRICT=0
for a in "$@"; do
  case "$a" in
    --show-diff) SHOW_DIFF=1 ;;
    --strict)    STRICT=1 ;;
    -*)          echo "未知参数: $a"; exit 2 ;;
    *) if [ -z "$PROJECT" ]; then PROJECT="$a"; elif [ -z "$FW" ]; then FW="$a"; fi ;;
  esac
done
[ -n "$PROJECT" ] || { echo "用法: bash verify-baseline.sh <project-root> [framework-skills-root] [--show-diff] [--strict]"; exit 2; }
[ -n "$FW" ] || FW="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$(cd "$PROJECT" 2>/dev/null && pwd)" || { echo "项目路径不存在"; exit 2; }

# 流程方法论 skill：与栈无关，应与基线逐字一致（漂移→需确认是否有意增补）
FLOW="dev-session pre-dev-alignment progress-tracker iteration-planner team-memory capability-registry similar-issue-sweep dev-output project-onboarding git-commit"
# 其中应在项目根「存在」的（project-onboarding 是引入器，项目不强制具备）
REQUIRED="dev-session pre-dev-alignment progress-tracker iteration-planner team-memory capability-registry similar-issue-sweep dev-output git-commit"
is_flow () { case " $FLOW " in *" $1 "*) return 0;; *) return 1;; esac; }

# glob 是否匹配到东西（compgen -G 逐模式判断，避开 `ls a b c` 任一不存在即非零的坑）
has_glob () { compgen -G "$1" >/dev/null 2>&1; }

# 按标志文件分类「含 .claude 的目录」为 backend / frontend / root（布局无关，支持嵌套 Maven / 子目录前端）
classify () {
  local d="$1" pj
  # 项目根以 .document/ 为准（最高优先级，避免"含后端子仓库的根"被误判为后端）
  [ -d "$d/.document" ] && { echo root; return; }
  # 后端：本级或一层嵌套的 Maven/Gradle，或四层目录，或 java 源码（覆盖 yadp-server 这类嵌套模块）
  if has_glob "$d/pom.xml" || has_glob "$d/*/pom.xml" || has_glob "$d/build.gradle*" || has_glob "$d/*/build.gradle*" \
     || { [ -d "$d/domain" ] && [ -d "$d/integration" ]; } || [ -d "$d/src/main/java" ] || has_glob "$d/*/src/main/java"; then
    echo backend; return; fi
  # 前端：src/views（本级/嵌套）或 package.json 含 vue（本级/嵌套）
  if [ -d "$d/src/views" ] || has_glob "$d/*/src/views"; then echo frontend; return; fi
  for pj in "$d"/package.json "$d"/*/package.json; do
    [ -f "$pj" ] && grep -q '"vue"' "$pj" 2>/dev/null && { echo frontend; return; }
  done
  echo root
}
area_of () { case "$1" in backend) echo "$FW/backend";; frontend) echo "$FW/frontend";; *) echo "$FW/.claude/skills";; esac; }

# framework 中定位某 skill：先查分类区域，否则跨区唯一匹配（reviewer 这类多区同名时只认分类区域）
find_fw () {
  local n="$1" pref="$2" hit="" ar
  [ -f "$pref/$n/SKILL.md" ] && { echo "$pref/$n/SKILL.md"; return; }
  for ar in "$FW/.claude/skills" "$FW/backend" "$FW/frontend"; do
    [ -f "$ar/$n/SKILL.md" ] && { [ -n "$hit" ] && return 0; hit="$ar/$n/SKILL.md"; }
  done
  [ -n "$hit" ] && echo "$hit"
}

OK=0; SPECIFIC=0; DRIFT=0; ERRORS=0
echo "framework 基线: $FW"
echo "目标项目:       $PROJECT"
echo

mapfile -t SKILLDIRS < <(find "$PROJECT" -type d -path '*/.claude/skills' \
  -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.bak-*/*' 2>/dev/null | sort)
[ "${#SKILLDIRS[@]}" -gt 0 ] || { echo "✗ 未发现任何 .claude/skills —— 项目尚未引入？"; exit 1; }

for SD in "${SKILLDIRS[@]}"; do
  HOST="$(cd "$SD/../.." && pwd)"
  KIND="$(classify "$HOST")"; PREF="$(area_of "$KIND")"
  REL="${HOST#$PROJECT}"; REL="${REL#/}"; [ -n "$REL" ] || REL="(root)"
  echo "── [$KIND] $REL/.claude/skills"
  for SKILL in "$SD"/*/; do
    [ -d "$SKILL" ] || continue
    name="$(basename "$SKILL")"; pf="${SKILL}SKILL.md"
    [ -f "$pf" ] || { echo "   ?  $name  项目内缺 SKILL.md"; ERRORS=$((ERRORS+1)); continue; }
    nm="$(sed -n 's/^name:[[:space:]]*//p' "$pf" | head -1 | tr -d '\r ')"
    mism=""; [ -n "$nm" ] && [ "$nm" != "$name" ] && { mism="  ⚠ name='$nm'≠目录名"; ERRORS=$((ERRORS+1)); }
    ff="$(find_fw "$name" "$PREF")"
    if [ -z "$ff" ]; then echo "   ⊘  $name  framework 无 → 项目专有，跳过$mism"; continue; fi
    if diff --strip-trailing-cr -q "$ff" "$pf" >/dev/null 2>&1; then
      echo "   ✓  $name  一致$mism"; OK=$((OK+1))
    else
      n=$(diff --strip-trailing-cr "$ff" "$pf" | grep -c '^[<>]' || true)
      if is_flow "$name"; then
        echo "   Δ  $name  流程 skill 与基线差 ${n} 行  ⚠需确认是否有意$mism"; DRIFT=$((DRIFT+1))
      else
        echo "   ℹ  $name  与基线差 ${n} 行（reviewer/规范类，多为项目专有项）$mism"; SPECIFIC=$((SPECIFIC+1))
      fi
      [ "$SHOW_DIFF" -eq 1 ] && diff --strip-trailing-cr "$ff" "$pf" | sed 's/^/        /'
    fi
  done
  echo
done

RS="$PROJECT/.claude/skills"
if [ -d "$RS" ]; then
  for f in $REQUIRED; do [ -d "$RS/$f" ] || { echo "✗ root 缺流程 skill: $f"; ERRORS=$((ERRORS+1)); }; done
else
  echo "✗ 项目根无 .claude/skills/"; ERRORS=$((ERRORS+1))
fi

echo "──────── 小结 ────────"
echo "✓ 一致 $OK   ℹ 项目专有差异 $SPECIFIC   Δ 流程漂移(需确认) $DRIFT   ✗ 结构错误 $ERRORS"
echo "提示: --show-diff 看具体差异；ℹ 多为 reviewer/规范类的正常项目沉淀，需人工/AI 判读。"
[ "$ERRORS" -gt 0 ] && exit 1
{ [ "$STRICT" -eq 1 ] && [ "$DRIFT" -gt 0 ]; } && exit 1
exit 0
