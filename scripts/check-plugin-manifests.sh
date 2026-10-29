#!/usr/bin/env bash
# check-plugin-manifests.sh — 校验本仓库的 marketplace / 插件清单与技能源一致（发布前必跑）。
#
# 本仓库同时是 Claude Code 与 Codex 的插件 marketplace，清单只是元数据，技能内容仍是单一源：
#   .claude-plugin/marketplace.json          Claude Code 目录清单
#   .agents/plugins/marketplace.json         Codex 目录清单
#   {common,backend,frontend}/.claude-plugin/plugin.json   Claude Code 插件清单
#   {common,backend,frontend}/plugin.json                  Codex 插件清单（portable 格式）
#
# 检查项：每个插件两份清单的 name/version/description/skills 逐字一致；所有插件 version 相同，且等于
# README「当前基线」日期去前导零（2026-10-29 → 2026.10.29）；两份目录清单恰好列出三个插件且 source
# 指向对应目录；插件内每个技能目录有 SKILL.md、frontmatter name 与目录名一致、插件内无同名技能。
# 清单由人工维护、格式固定（每字段一行），故按行提取而不引入 JSON 解析依赖。
#
# 用法（Git Bash / WSL；PowerShell 用 `bash scripts/check-plugin-manifests.sh`）：
#   bash scripts/check-plugin-manifests.sh
set -uo pipefail

FW="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$FW" || exit 2
ERR=0
fail () { echo "✗ $*"; ERR=$((ERR+1)); }

# 插件名 : 插件根目录 : 技能所在目录（相对插件根）
PLUGINS="yzj-flow:common:skills yzj-backend:backend:. yzj-frontend:frontend:."

# 取 JSON 中某字段（"key": "value" 同行）的第一个值
field () { sed -n "s/^[[:space:]]*\"$2\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$1" | head -1; }

BASE="$(sed -n 's/.*\*\*当前基线\*\*：`\([0-9-]*\)`.*/\1/p' README.md | head -1)"
[ -n "$BASE" ] || fail "README.md 未找到「当前基线」日期"
EXPECT="$(echo "$BASE" | awk -F- '{ printf "%d.%d.%d", $1, $2, $3 }')"
echo "当前基线 $BASE → 期望插件版本 $EXPECT"

for p in $PLUGINS; do
  name="${p%%:*}"; rest="${p#*:}"; dir="${rest%%:*}"; sub="${rest#*:}"
  cc="$dir/.claude-plugin/plugin.json"; cx="$dir/plugin.json"
  for f in "$cc" "$cx"; do [ -f "$f" ] || fail "缺插件清单 $f"; done
  [ -f "$cc" ] && [ -f "$cx" ] || continue
  for k in name version description skills; do
    a="$(field "$cc" "$k")"; b="$(field "$cx" "$k")"
    [ -n "$a" ] || fail "$cc 缺 $k"
    [ "$a" = "$b" ] || fail "$name 两份清单 $k 不一致：'$a' vs '$b'"
  done
  [ "$(field "$cc" name)" = "$name" ] || fail "$cc name 应为 $name"
  [ "$(field "$cc" version)" = "$EXPECT" ] || fail "$name version='$(field "$cc" version)'，应为 $EXPECT（发布时随 README「当前基线」同步）"

  # 技能目录：有 SKILL.md、name 与目录名一致、插件内不重名
  seen=" "
  for d in "$dir/$sub"/*/; do
    d="${d%/}"; n="$(basename "$d")"
    [ -f "$d/SKILL.md" ] || { fail "$d 不是技能目录（缺 SKILL.md）——插件技能目录下只放技能"; continue; }
    fm="$(awk 'NR==1{sub(/^\xef\xbb\xbf/,""); if($0!~/^---\r?$/) exit; next} /^---\r?$/{exit} /^name:/{sub(/^name:[[:space:]]*/,""); sub(/\r$/,""); gsub(/"/,""); print; exit}' "$d/SKILL.md")"
    [ "$fm" = "$n" ] || fail "$d/SKILL.md name='$fm' 与目录名不一致"
    case "$seen" in *" $n "*) fail "$name 内技能重名：$n";; esac
    seen="$seen$n "
  done
  echo "  $name ($dir): $(echo $seen | wc -w) 个技能"
done

# 目录清单：恰好三个插件，source 指向对应目录
for m in .claude-plugin/marketplace.json .agents/plugins/marketplace.json; do
  [ -f "$m" ] || { fail "缺目录清单 $m"; continue; }
  [ "$(field "$m" name)" = "yzj-skills" ] || fail "$m 顶层 name 应为 yzj-skills"
  for p in $PLUGINS; do
    name="${p%%:*}"; rest="${p#*:}"; dir="${rest%%:*}"
    grep -q "\"name\"[[:space:]]*:[[:space:]]*\"$name\"" "$m" || fail "$m 未列出 $name"
    grep -q "\"\\./$dir\"" "$m" || fail "$m 无指向 ./$dir 的 source"
  done
  # 每个插件条目恰有一行 "source"（Codex 的 source 对象写在同一行）
  cnt="$(grep -c '"source"' "$m")"
  [ "$cnt" -eq 3 ] || fail "$m 列出 $cnt 个插件，应为 3"
  grep -q '"version"' "$m" && fail "$m 不得声明 version（版本只写在插件清单，两处都写时 Claude Code 静默取 plugin.json）"
done

echo
[ "$ERR" -eq 0 ] && { echo "✔ 插件清单一致"; exit 0; }
echo "✗ $ERR 处问题"; exit 1
