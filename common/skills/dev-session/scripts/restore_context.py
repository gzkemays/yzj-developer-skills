#!/usr/bin/env python3
"""上下文压缩后的恢复定位：输出红线 + 本需求恢复卡 + STATUS 对应行 + 需重读文件清单。

用法（从项目根、子仓或 worktree 内任意目录运行均可）：
    python restore_context.py                # 按 worktree 路径 / 当前分支名自动定位需求
    python restore_context.py --task <slug>  # 指定需求（恢复卡文件名去 .md，或其 business 段）
    python restore_context.py --list         # 只列出所有恢复卡
    python restore_context.py --root <path>  # 显式指定项目根（含 .document/）

只读、纯标准库、Python 3.8+；任何情况下退出码为 0（fail-open），缺文件时输出手动恢复提示。
不输出、不记录任何授权状态——授权按 red-lines.md 第 5 条一律重新确认。
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

RULE_DIRS = (".claude/rules", "common/rules")
SKILL_DIRS = (".claude/skills", "common/skills")
BRANCH_RE = re.compile(r"^(?:feat|opt|fix)/\d{4}\.\d{2}\.\d{2}-(.+)$")


def out(line=""):
    print(line)


def find_root(start, explicit):
    """项目根 = 含 .document/ 的目录；cwd 在 .worktree 内时取 .worktree 的父目录（树内可能有 .document 副本）。"""
    if explicit:
        p = Path(explicit).resolve()
        return p if (p / ".document").is_dir() else None
    start = Path(start).resolve()
    parts = start.parts
    if ".worktree" in parts:
        candidate = Path(*parts[: parts.index(".worktree")])
        if (candidate / ".document").is_dir():
            return candidate
    # .document/ 全项目只有根这一份（git-commit 8.4）：取最靠上的、带台账的那个，避免子仓 / 树内副本抢先命中
    chain = [p for p in (start, *start.parents) if (p / ".document").is_dir()]
    with_status = [p for p in chain if (p / ".document" / "plan" / "STATUS.md").is_file()]
    if with_status:
        return with_status[-1]
    return chain[0] if chain else None


def git_branch(cwd):
    # symbolic-ref 在尚无提交的新分支上也能取到名字；分离 HEAD 时返回非 0，视为无线索
    try:
        r = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            cwd=str(cwd), capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:  # git 不存在 / 超时等一律视为无线索
        return ""


def business_hint(cwd):
    """定位线索：worktree 目录段优先，其次当前分支名的 business 段。"""
    parts = Path(cwd).resolve().parts
    if ".worktree" in parts:
        i = parts.index(".worktree")
        if i + 1 < len(parts):
            return parts[i + 1], "worktree 路径"
    m = BRANCH_RE.match(git_branch(cwd))
    if m:
        return m.group(1), "当前分支名"
    return "", ""


def list_cards(root):
    d = root / ".document" / "plan" / "context"
    if not d.is_dir():
        return []
    return sorted(p for p in d.glob("*.md") if p.name.lower() != "readme.md")


def pick_card(cards, task, hint):
    key = task or hint
    if not key:
        return cards if len(cards) == 1 else []
    exact = [c for c in cards if c.stem == key]
    if exact:
        return exact
    suffix = [c for c in cards if c.stem.endswith("_" + key) or c.stem.endswith("-" + key)]
    if suffix:
        return suffix
    return [c for c in cards if key in c.stem]


def status_rows(root, slug):
    f = root / ".document" / "plan" / "STATUS.md"
    if not f.is_file():
        return None, []
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    header, rows = "", []
    for ln in lines:
        if ln.startswith("| 需求 |") and "阶段" in ln:
            header = ln
        elif ln.startswith("| 需求 |") and not header:
            header = ln
        if ln.startswith("|") and slug in ln:
            rows.append(ln)
    return header, rows


def reread_items(card_text):
    """取「需重读」小节下的 - 条目。"""
    items, on = [], False
    for ln in card_text.splitlines():
        if ln.startswith("## "):
            on = "需重读" in ln
            continue
        if on and ln.lstrip().startswith("- "):
            items.append(ln.lstrip()[2:].strip())
    return items


def resolve_skill(root, item):
    """按 '技能名（章节）' 的技能名在项目根 / 各子目录的技能布局中找 SKILL.md；找不到则提示按名称加载（插件安装）。"""
    name = re.split(r"[（(\s]", item, maxsplit=1)[0].strip().strip("`")
    if not name:
        return None
    rel = name.split("/")[-1]  # backend/reviewer → reviewer（前缀只表达所属端）
    hits = []
    for sd in SKILL_DIRS:
        for base in (root, *[p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]):
            cand = base / sd / rel / "SKILL.md"
            if cand.is_file():
                hits.append(cand)
    # backend/ 前缀时优先含 backend 字样的路径，frontend 同理
    side = name.split("/")[0] if "/" in name else ""
    if side and len(hits) > 1:
        pref = [h for h in hits if side in str(h).lower()]
        hits = pref or hits
    return hits


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--task", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--root", default="")
    args = ap.parse_args()

    cwd = Path.cwd()
    root = find_root(cwd, args.root)
    out("# 压缩恢复（restore_context）")
    if root is None:
        out("未找到含 .document/ 的项目根——按 red-lines.md「压缩恢复协议」手动恢复：读 STATUS.md 对应行与恢复卡。")
        return 0
    out(f"项目根：{root}")

    # 1. 红线
    red = next((root / d / "red-lines.md" for d in RULE_DIRS if (root / d / "red-lines.md").is_file()), None)
    out("\n## 红线")
    if red:
        out(f"（来源 {red.relative_to(root).as_posix()}）\n")
        out(red.read_text(encoding="utf-8", errors="replace").rstrip())
    else:
        out("未找到 red-lines.md（.claude/rules 或 common/rules）——请从 framework templates/common/rules 补装；硬门禁以 dev-session 原文为准。")

    # 2. 恢复卡
    cards = list_cards(root)
    out("\n## 恢复卡")
    if args.list or not cards:
        out("plan/context/ 下恢复卡：" + (", ".join(c.stem for c in cards) if cards else "无"))
        if not cards:
            out("无恢复卡：若需求已在进行中，先按 dev-session P1 第 7 步补建；否则从 STATUS.md「进行中」定位。")
        if args.list:
            return 0
    hint, src = business_hint(cwd)
    chosen = pick_card(cards, args.task, hint) if cards else []
    if cards and not chosen:
        out(f"定位线索：{src + ' = ' + hint if hint else '无（不在 worktree 内，分支名也非 feat|opt|fix/日期-business 形式）'}")
        out("无法唯一确定本需求，请用 --task 指定其一：")
        for c in cards:
            out(f"  - {c.stem}")
    elif len(chosen) > 1:
        out(f"线索 {hint!r} 匹配到多张卡，请用 --task 指定其一：")
        for c in chosen:
            out(f"  - {c.stem}")
        chosen = []
    card = chosen[0] if chosen else None
    if card:
        out(f"（{card.relative_to(root).as_posix()}" + (f"，由{src}定位" if src and not args.task else "") + "）\n")
        text = card.read_text(encoding="utf-8", errors="replace")
        out(text.rstrip())

        # 3. STATUS 行
        out("\n## STATUS 对应行")
        header, rows = status_rows(root, card.stem)
        if header is None:
            out("未找到 .document/plan/STATUS.md")
        elif rows:
            out(header)
            for r in rows:
                out(r)
        else:
            out(f"STATUS.md 中没有 {card.stem} 的行——台账与恢复卡不一致，先向开发者报告再继续（dev-session「进度判定」）。")

        # 4. 需重读
        out("\n## 需重读（文件定位）")
        items = reread_items(text)
        if not items:
            out("恢复卡未填「需重读」——至少重读 dev-session 当前阶段章节；P4 阶段重读 reviewer 全文。")
        for it in items:
            hits = resolve_skill(root, it)
            if hits is None:
                out(f"- {it}")
            elif hits:
                out(f"- {it} → " + " | ".join(h.relative_to(root).as_posix() for h in hits))
            else:
                out(f"- {it} → 未在项目技能目录中定位（插件安装的技能按名称加载）")

    out("\n## 下一步")
    out("按「需重读」重读后输出：[恢复 | 需求 … | 阶段 Px | 已过 … | 下一步 …]；授权一律重新确认。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # fail-open：脚本自身故障不阻塞恢复
        print(f"restore_context 运行异常（{e!r}）——按 red-lines.md「压缩恢复协议」手动恢复。")
        sys.exit(0)
