#!/usr/bin/env bash
# verify-baseline.sh — 校验目标项目的 skill 是否与 framework 基线对齐。
#
# 布局无关：按「标志文件」自动识别项目里每个技能目录（.claude/skills 或 common/skills，
# 分别对应 Claude Code 与其他宿主的加载布局）属于 后端 / 前端 / 根，
# 再对应到 framework 的 backend/ · frontend/ · common/skills/ 逐一比对。不依赖仓库目录叫什么名字。
#
# 单栈项目（根目录本身就是后端/前端仓，根级直接有 pom.xml / src/views 等标志）允许根技能目录
# 混放「通用 + 单端规范」，按本级标志消歧；只认本级标志、不认一层嵌套——含前后端子仓的公共根仍按纯 root 处理。
# 已识别安装某端规范的技能目录必须含该端 reviewer（P4 硬流程必需），缺失计结构错误。
# 同一技能目录同时命中前后端基线技能 → 报混装结构错误。已知残角：单栈根只被混入另一端的
# reviewer（无其他该端技能同目录）时，会解析到本端基线、以 ℹ 大差异呈现而非报错——由
# project-onboarding dry-run 门禁的人工判读兜底。
#
# 用法（在 Git Bash / WSL 运行；PowerShell 用 `bash scripts/verify-baseline.sh ...`）：
#   bash verify-baseline.sh <project-root> [framework-skills-root] [--show-diff] [--strict]
#     framework-skills-root  省略时 = 本脚本所在的 skills 仓库
#     --show-diff            打印每个差异 skill 的具体 diff
#     --strict               流程 skill 出现漂移即非零退出（默认仅结构错误才非零）
#
# 流程 skill 在 frontmatter 结束后 20 行内带「本文件 = framework 基线」引用块声明（project-onboarding
# 「📌 项目覆写约定」的文件头差异清单）时报 📌 而非 Δ，--strict 下不算漂移；只有正文 📌、声明在
# frontmatter 内或无声明的，一律按普通漂移处理。frontmatter 做轻量检查（块内 name/description 非空），
# 刻意不做完整 YAML 校验。
# marketplace 安装模式（项目级 .claude/settings.json 的 enabledPlugins / .codex/config.toml 的
# [plugins."<插件>@yzj-skills"]）：技能在宿主插件缓存，不做逐字比对；只查端插件放置、前后端混装、
# 插件与本地副本双装，根启用 yzj-flow 视为流程层齐备。
# 扫描时跳过 .worktree/（git-commit 第八章的 worktree 副本）、.claude/worktrees/（宿主托管 worktree）、
# .scratch/（临时参考副本）、node_modules、.git、.bak-*，避免同一 skill 被重复计数。
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
# 基线路径必须真实有效，否则所有技能都会被误判为「项目专有」而静默通过
FW="$(cd "$FW" 2>/dev/null && pwd)" || { echo "✗ 基线路径不存在: $FW"; exit 2; }
{ [ -d "$FW/common/skills" ] && [ -d "$FW/backend" ] && [ -d "$FW/frontend" ]; } \
  || { echo "✗ 基线无效：$FW 下缺 common/skills / backend / frontend（不是 skills 仓库？）"; exit 2; }
# 哨兵文件：目录存在但为空（不完整检出）同样不能作为比较基线
for s in common/skills/dev-session backend/reviewer frontend/reviewer; do
  [ -f "$FW/$s/SKILL.md" ] || { echo "✗ 基线无效：缺 $FW/$s/SKILL.md（空目录 / 不完整检出不能作为比较基线）"; exit 2; }
done

# 流程方法论 skill：与栈无关，应与基线逐字一致（漂移→需确认是否有意增补）
FLOW="dev-session pre-dev-alignment progress-tracker iteration-planner team-memory capability-registry similar-issue-sweep dev-output project-onboarding git-commit neat-freak"
# 其中应在项目根「存在」的（project-onboarding 是引入器，项目不强制具备）
REQUIRED="dev-session pre-dev-alignment progress-tracker iteration-planner team-memory capability-registry similar-issue-sweep dev-output git-commit"
is_flow () { case " $FLOW " in *" $1 "*) return 0;; *) return 1;; esac; }

# glob 是否匹配到东西（compgen -G 逐模式判断，避开 `ls a b c` 任一不存在即非零的坑）
has_glob () { compgen -G "$1" >/dev/null 2>&1; }

# 轻量 frontmatter 读取（刻意不做完整 YAML 校验）：只认文件开头 '---' 包围且**已闭合**的块内字段，
# 正文里的 name:/description:（如代码示例）不作数；未闭合的 frontmatter 整体无效。
# 值统一规范化：先去首尾空白 → 剥成对双引号 → 再去首尾空白（兼容 `name: "cache"  ` 这类写法）。
# 输出 "name<TAB>descok<TAB>fm_end"：descok=1 表示 description 值非空（内联值或块标量的后续缩进行）；
# fm_end 为闭合分隔符行号（0 = 无有效 frontmatter），覆写声明窗口据此计算，BOM 处理只做这一次。
read_fm () {
  awk '
    function norm(v) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", v)
      if (v ~ /^".*"$/) { sub(/^"/, "", v); sub(/"$/, "", v); gsub(/^[[:space:]]+|[[:space:]]+$/, "", v) }
      return v
    }
    NR==1 { sub(/^\xef\xbb\xbf/,""); if ($0 !~ /^---\r?$/) exit; open=1; next }
    open && /^---\r?$/ { closed=NR; exit }
    open {
      line=$0; sub(/\r$/,"",line)
      if (line ~ /^name:/) { v=line; sub(/^name:[[:space:]]*/,"",v); name=norm(v); waiting=0 }
      else if (line ~ /^description:/) {
        v=line; sub(/^description:[[:space:]]*/,"",v); v=norm(v)
        if (v != "" && v != ">" && v != "|" && v != ">-" && v != "|-") desc=1; else waiting=1
      }
      else if (line ~ /^[[:space:]]+[^[:space:]]/) { if (waiting) { desc=1; waiting=0 } }
      else { waiting=0 }
    }
    END { if (!closed) { name=""; desc=0; closed=0 } printf "%s\t%d\t%d", name, desc+0, closed+0 }
  ' "$1"
}

# 按标志文件分类「含技能目录的宿主目录」为 backend / frontend / root（布局无关，支持嵌套 Maven / 子目录前端）
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
area_of () { case "$1" in backend) echo "$FW/backend";; frontend) echo "$FW/frontend";; *) echo "$FW/common/skills";; esac; }

# 根目录的本级栈标志（单栈项目：根同时就是后端/前端仓）。只认本级、不认一层嵌套——
# 含前后端子仓的公共根不得因 apps/api/pom.xml 之类被判成单栈。
stack_hints () {
  local d="$1"
  if has_glob "$d/pom.xml" || has_glob "$d/build.gradle*" \
     || { [ -d "$d/domain" ] && [ -d "$d/integration" ]; } || [ -d "$d/src/main/java" ]; then echo backend; fi
  if [ -d "$d/src/views" ]; then echo frontend; return; fi
  [ -f "$d/package.json" ] && grep -q '"vue"' "$d/package.json" 2>/dev/null && echo frontend
}

# framework 中定位某 skill：先按优先区域（$2 起的各参数：分类区域 + 单栈根的本级栈区域）查，
# 否则跨区唯一匹配；多区同名且无法消歧 → 返回歧义标记（前后端 reviewer 同名即此类）。
# 优先区域以独立参数传入并带引号展开，基线路径含空格不影响。
find_fw () {
  local n="$1" ar; shift; local -a hits=()
  for ar in "$@"; do
    [ -f "$ar/$n/SKILL.md" ] && { echo "$ar/$n/SKILL.md"; return; }
  done
  for ar in "$FW/common/skills" "$FW/backend" "$FW/frontend"; do
    [ -f "$ar/$n/SKILL.md" ] && hits+=("$ar/$n/SKILL.md")
  done
  if [ "${#hits[@]}" -eq 1 ]; then echo "${hits[0]}"
  elif [ "${#hits[@]}" -gt 1 ]; then echo "__AMBIGUOUS__ ${hits[*]}"
  fi
}

# marketplace 安装：插件名 → 对应的基线技能区域
MKT="yzj-skills"; PLUGIN_NAMES="yzj-flow yzj-backend yzj-frontend"
plugin_area () { case "$1" in yzj-backend) echo "$FW/backend";; yzj-frontend) echo "$FW/frontend";; *) echo "$FW/common/skills";; esac; }
# 某目录在某宿主的项目级配置里是否启用了插件：Claude Code 读该目录 .claude/settings.json 的 enabledPlugins；
# Codex 读 .codex/config.toml 的 [plugins."<插件>@yzj-skills"] enabled = true
plugin_on () {
  local d="$1" host="$2" n="$3"
  case "$host" in
    claude) [ -f "$d/.claude/settings.json" ] \
              && grep -Eq "\"$n@$MKT\"[[:space:]]*:[[:space:]]*true" "$d/.claude/settings.json" ;;
    codex)  [ -f "$d/.codex/config.toml" ] \
              && awk -v key="[plugins.\"$n@$MKT\"]" '
                   { sub(/\r$/,""); line=$0; gsub(/^[[:space:]]+|[[:space:]]+$/,"",line) }
                   line==key { s=1; next } line ~ /^\[/ { s=0 }
                   s && line ~ /^enabled[[:space:]]*=[[:space:]]*true/ { f=1 }
                   END { exit !f }' "$d/.codex/config.toml" ;;
  esac
}
# 宿主 → 该宿主读取的本地技能目录（双装检查用）
local_skills_of () { case "$1" in claude) echo ".claude/skills";; codex) echo "common/skills";; esac; }

OK=0; SPECIFIC=0; DRIFT=0; OVERRIDE=0; ERRORS=0; PLUGINS=0
echo "framework 基线: $FW"
echo "目标项目:       $PROJECT"
echo

EXCL=(-not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/.bak-*/*' -not -path '*/.worktree/*'
  -not -path '*/.claude/worktrees/*' -not -path '*/.scratch/*')
mapfile -t SKILLDIRS < <(find "$PROJECT" -type d \( -path '*/.claude/skills' -o -path '*/common/skills' \) \
  "${EXCL[@]}" 2>/dev/null | sort)
# 启用了本 marketplace 插件的目录（项目级配置所在目录 = 该宿主会话的启动目录）
mapfile -t PLUGINHOSTS < <(find "$PROJECT" -type f \( -path '*/.claude/settings.json' -o -path '*/.codex/config.toml' \) \
  "${EXCL[@]}" 2>/dev/null | xargs -r -d '\n' grep -l "@$MKT" 2>/dev/null | while read -r f; do cd "$(dirname "$f")/.." && pwd; done | sort -u)
[ "${#SKILLDIRS[@]}" -gt 0 ] || [ "${#PLUGINHOSTS[@]}" -gt 0 ] \
  || { echo "✗ 未发现任何技能目录（.claude/skills 或 common/skills）或 marketplace 插件启用配置—— 项目尚未引入？"; exit 1; }

for SD in "${SKILLDIRS[@]}"; do
  HOST="$(cd "$SD/../.." && pwd)"
  KIND="$(classify "$HOST")"; PREFS=("$(area_of "$KIND")")
  HINTS=""
  if [ "$KIND" = root ]; then
    HINTS="$(stack_hints "$HOST")"
    # 仅恰好单一栈标志时按单栈消歧；根级同时有前后端标志 → 不加优先区域，同名技能照报来源歧义
    [ "$(echo $HINTS | wc -w)" -eq 1 ] && PREFS+=("$FW/$HINTS") || HINTS=""
  fi
  # 该目录必须具备的 reviewer 端：backend/frontend 目录，或恰好单一栈标志的单栈根
  REQAREA=""
  case "$KIND" in
    backend|frontend) REQAREA="$KIND" ;;
    root) [ -n "$HINTS" ] && REQAREA="$HINTS" ;;
  esac
  B_HIT=0; F_HIT=0
  REL="${HOST#$PROJECT}"; REL="${REL#/}"; [ -n "$REL" ] || REL="(root)"
  SUB="${SD#"$HOST"/}"
  echo "── [$KIND${HINTS:+ 单栈:$HINTS}] $REL/$SUB"
  for SKILL in "$SD"/*/; do
    [ -d "$SKILL" ] || continue
    name="$(basename "$SKILL")"; pf="${SKILL}SKILL.md"
    [ -f "$pf" ] || { echo "   ?  $name  项目内缺 SKILL.md"; ERRORS=$((ERRORS+1)); continue; }
    # 用参数展开拆分（IFS read 会吞掉空的首字段，导致空 name 被误读为后续标志）
    fm_out="$(read_fm "$pf")"
    nm="${fm_out%%$'\t'*}"; fm_rest="${fm_out#*$'\t'}"
    descok="${fm_rest%%$'\t'*}"; fm_end="${fm_rest##*$'\t'}"
    mism=""
    if [ -z "$nm" ]; then
      mism="  ✗ 缺 frontmatter name（或 frontmatter 块缺失 / 未闭合）"; ERRORS=$((ERRORS+1))
    elif [ "$nm" != "$name" ]; then
      mism="  ⚠ name='$nm'≠目录名"; ERRORS=$((ERRORS+1))
    fi
    [ "${descok:-0}" = 1 ] \
      || { mism="$mism  ✗ 缺 frontmatter description 或值为空"; ERRORS=$((ERRORS+1)); }
    ff="$(find_fw "$name" "${PREFS[@]}")"
    if [ -z "$ff" ]; then echo "   ⊘  $name  framework 无 → 项目专有，跳过$mism"; continue; fi
    case "$ff" in __AMBIGUOUS__*)
      echo "   ✗  $name  来源歧义：基线多处同名（${ff#__AMBIGUOUS__ }），该目录分类为 [$KIND] 无法消歧——前后端规范应装各自目录（单栈项目需根级有 pom.xml / src/views 等本级标志）$mism"
      ERRORS=$((ERRORS+1)); continue;;
    esac
    case "$ff" in "$FW/backend/"*) B_HIT=1;; "$FW/frontend/"*) F_HIT=1;; esac
    if diff --strip-trailing-cr -q "$ff" "$pf" >/dev/null 2>&1; then
      echo "   ✓  $name  一致$mism"; OK=$((OK+1))
    else
      n=$(diff --strip-trailing-cr "$ff" "$pf" | grep -c '^[<>]' || true)
      if is_flow "$name"; then
        # 项目覆写只认「文件头差异清单」声明：frontmatter 结束后 20 行内、`>` 引用块行、固定首句。
        # 不扫全文符号（避免基线正文自带 📌 的文件任何改动都被误判），也不认 frontmatter 内的
        # 描述性文字；fm_end 来自 read_fm 的同一次读取（BOM / 闭合处理一致）；
        # LC_ALL=C 按字节匹配，规避多字节文本在不同语言环境下的 grep 行为差异
        if [ "${fm_end:-0}" -gt 0 ] && sed -n "$((fm_end+1)),$((fm_end+20))p" "$pf" 2>/dev/null \
             | LC_ALL=C grep -q '^>.*本文件 = framework 基线'; then
          echo "   📌  $name  流程 skill 带项目覆写标记，与基线差 ${n} 行（按文件头差异清单核对）$mism"; OVERRIDE=$((OVERRIDE+1))
        else
          echo "   Δ  $name  流程 skill 与基线差 ${n} 行  ⚠需确认是否有意$mism"; DRIFT=$((DRIFT+1))
        fi
      else
        echo "   ℹ  $name  与基线差 ${n} 行（reviewer/规范类，多为项目专有项）$mism"; SPECIFIC=$((SPECIFIC+1))
      fi
      [ "$SHOW_DIFF" -eq 1 ] && diff --strip-trailing-cr "$ff" "$pf" | sed 's/^/        /'
    fi
  done
  # 同一技能目录同时命中前后端基线技能 → 混装（两端 reviewer 同名互相覆盖的前兆），计结构错误
  if [ "$B_HIT" -eq 1 ] && [ "$F_HIT" -eq 1 ]; then
    echo "   ✗  混装：$REL/$SUB 同时含前后端规范技能——不得装入同一目录（见 project-onboarding）"
    ERRORS=$((ERRORS+1))
  fi
  # 已安装某端规范（命中该端基线技能 ≥1）的目录必须有该端 reviewer——P4 硬流程必需；
  # 只放项目专有技能的目录不触发此检查
  AREA_HIT=0
  case "$REQAREA" in backend) AREA_HIT=$B_HIT;; frontend) AREA_HIT=$F_HIT;; esac
  if [ -n "$REQAREA" ] && [ "$AREA_HIT" -eq 1 ] && [ ! -f "$SD/reviewer/SKILL.md" ]; then
    echo "   ✗  缺必备审查技能：$REL/$SUB/reviewer —— 已安装 $REQAREA 规范但缺 reviewer（P4 硬流程必需）"
    ERRORS=$((ERRORS+1))
  fi
  echo
done

# marketplace 插件安装：技能在宿主的插件缓存里，项目内只有启用配置，故不做逐字比对
# （版本由各成员 `plugin update` / `marketplace upgrade` 拉取）；这里查放置与双装。
for HOST in "${PLUGINHOSTS[@]}"; do
  KIND="$(classify "$HOST")"; HINTS=""
  [ "$KIND" = root ] && { HINTS="$(stack_hints "$HOST")"; [ "$(echo $HINTS | wc -w)" -eq 1 ] || HINTS=""; }
  REL="${HOST#$PROJECT}"; REL="${REL#/}"; [ -n "$REL" ] || REL="(root)"
  echo "── [$KIND${HINTS:+ 单栈:$HINTS}] $REL  marketplace 插件"
  for h in claude codex; do
    ON=""
    for n in $PLUGIN_NAMES; do plugin_on "$HOST" "$h" "$n" && ON="$ON $n"; done
    [ -n "$ON" ] || continue
    echo "   🧩  $h 启用:$ON"; PLUGINS=$((PLUGINS+1))
    case " $ON " in *" yzj-backend "*) case " $ON " in *" yzj-frontend "*)
      echo "   ✗  混装：$REL 同时启用 yzj-backend 与 yzj-frontend——两端 reviewer 会同时加载，按端分仓启用"
      ERRORS=$((ERRORS+1));;
    esac;; esac
    for n in $ON; do
      # 端插件只能启用在同端目录（或该端的单栈根）
      case "$n" in
        yzj-backend|yzj-frontend)
          want="${n#yzj-}"
          if [ "$KIND" != "$want" ] && [ "$HINTS" != "$want" ]; then
            echo "   ✗  $n 启用在 [$KIND] 目录——应启用在 $want 仓的项目级配置"; ERRORS=$((ERRORS+1))
          fi;;
      esac
      # 双装：同一技能既由插件提供、又有本宿主读取的本地副本 → 会话里加载两份
      LS="$HOST/$(local_skills_of "$h")"
      for s in "$(plugin_area "$n")"/*/; do
        s="$(basename "$s")"
        [ -d "$LS/$s" ] && { echo "   ✗  双装：$s 同时来自插件 $n 与本地 ${LS#$PROJECT/}/$s——二选一（需 📌 覆写的层改回复制安装并停用插件）"; ERRORS=$((ERRORS+1)); }
      done
    done
  done
  echo
done

# root 必备流程 skill：按「已启用的宿主布局」逐一检查——双宿主项目两套目录各自都要齐，
# 不得以一侧副本掩盖另一侧缺失（各宿主只读各自的目录）；该宿主在根启用了 yzj-flow 插件即视为齐备
ROOT_LAYOUTS=0
for h in claude codex; do
  RS="$PROJECT/$(local_skills_of "$h")"
  if plugin_on "$PROJECT" "$h" yzj-flow; then ROOT_LAYOUTS=$((ROOT_LAYOUTS+1)); continue; fi
  [ -d "$RS" ] || continue
  ROOT_LAYOUTS=$((ROOT_LAYOUTS+1))
  for f in $REQUIRED; do
    [ -d "$RS/$f" ] || { echo "✗ root 缺流程 skill: ${RS#$PROJECT/}/$f"; ERRORS=$((ERRORS+1)); }
  done
done
[ "$ROOT_LAYOUTS" -gt 0 ] || { echo "✗ 项目根无技能目录（.claude/skills 或 common/skills），也未在根启用 yzj-flow 插件"; ERRORS=$((ERRORS+1)); }
# 常驻规则层为软检查：缺失只提示，不计错误（两种布局任一即可）
RULES=""
[ -d "$PROJECT/.claude/rules" ] && RULES="$PROJECT/.claude/rules"
[ -z "$RULES" ] && [ -d "$PROJECT/common/rules" ] && RULES="$PROJECT/common/rules"
if [ -n "$RULES" ]; then
  for f in collaboration.md api-contract.md; do
    [ -f "$RULES/$f" ] || echo "ℹ ${RULES#$PROJECT/} 缺 $f（可从 templates/common/rules 补；契约表留在入口文件亦可）"
  done
else
  echo "ℹ 项目根无常驻规则层（.claude/rules 或 common/rules）—— 建议从 templates/common/rules 补 collaboration.md / api-contract.md"
fi

echo "──────── 小结 ────────"
echo "✓ 一致 $OK   ℹ 项目专有差异 $SPECIFIC   📌 项目覆写 $OVERRIDE   Δ 流程漂移(需确认) $DRIFT   🧩 插件启用层 $PLUGINS   ✗ 结构错误 $ERRORS"
echo "提示: --show-diff 看具体差异；ℹ 多为 reviewer/规范类的正常项目沉淀，需人工/AI 判读；📌 按该文件头部差异清单核对。"
[ "$ERRORS" -gt 0 ] && exit 1
{ [ "$STRICT" -eq 1 ] && [ "$DRIFT" -gt 0 ]; } && exit 1
exit 0
