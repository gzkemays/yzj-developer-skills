#!/usr/bin/env python3
"""git-commit 铁律 1 / 3 的机械兜底：提交信息不得含 AI 记号与进度词；主干直提须开发者本次授权。

用法：
    commit_guard.py commit-msg <msgfile>   git 原生 commit-msg hook：命中 → 退出 1 拦截并说明原因
    commit_guard.py check-text <file>      对任意 UTF-8 文本（MR 标题 / 描述等）做同一检查，命中退出 1
    commit_guard.py precheck               提交前自检：打印当前分支判定与授权提醒，恒退出 0
    commit_guard.py pretooluse             Claude Code PreToolUse hook：stdin 读 JSON，命中 git commit 时
                                           AI 记号 → deny；在主干 → ask（弹窗确认，单次授权）；否则放行

规则来源：common/skills/git-commit/SKILL.md 一、铁律 3（AI 记号 / 进度词）、2.1 分支决策表、2.5 主干直提单次授权。
纯标准库、Python 3.8+。除 commit-msg / check-text 命中外，任何异常都放行（fail-open），不阻塞开发。
"""
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

# —— 铁律 3：AI 记号（只拦署名 / 来源 / 模型名，不拦业务文案里对宿主产品的正常提及） ——
AI_MARKS = [
    (re.compile(r"(?im)^\s*co-authored-by\s*:.*$"), "Co-Authored-By 协作者尾注"),
    (re.compile(r"(?i)generated\s+with\b"), "Generated with 来源尾注"),
    # 路径 / 文件名里的 .claude/、claude-settings-hooks.json 不算署名：前后紧邻 . / - _ 或字母数字时不命中
    (re.compile(r"(?i)(?<![\w./-])(claude(\s+code)?|anthropic|opus|sonnet|haiku)(?![\w./-])"), "模型 / 工具名"),
    (re.compile(r"🤖"), "AI 署名 emoji"),
    (re.compile(r"由\s*AI\s*(生成|辅助|编写|撰写)|AI\s*(辅助|生成)"), "\"由 AI 生成 / AI 辅助\" 字样"),
]
# —— 铁律 3：进度词（描述对话 / 流程进度而非代码意图） ——
PROGRESS_WORDS = [
    (re.compile(r"\bFIXED\b"), "FIXED"),
    (re.compile(r"\bStep\s*\d+\b"), "Step N"),
    (re.compile(r"\bPhase\s*\d+\b"), "Phase N"),
    (re.compile(r"\bP\d{1,2}\s*已过"), "Px 已过"),
]
# —— 2.1 分支决策表 ——
DEV_BRANCH = re.compile(r"^(feat|opt|fix)/\d{4}\.\d{2}\.\d{2}-[a-z0-9-]+$")
TRUNK = re.compile(r"^(master|main|develop|release/.*)$")


def scan(text):
    """返回命中清单 [(类别, 规则名, 命中片段)]。git 注释行（# 开头）不计。"""
    body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    hits = []
    for rx, label in AI_MARKS:
        m = rx.search(body)
        if m:
            hits.append(("AI 记号", label, m.group(0).strip()[:60]))
    for rx, label in PROGRESS_WORDS:
        m = rx.search(body)
        if m:
            hits.append(("进度词", label, m.group(0).strip()[:60]))
    return hits


def explain(hits):
    lines = ["提交信息违反 git-commit 铁律 3："]
    lines += [f"  - {kind}「{label}」：{frag}" for kind, label, frag in hits]
    lines.append("删除后重新提交（不要加任何 AI 署名 / 来源尾注；不要用 FIXED / Step N / Phase N 描述进度）。")
    return "\n".join(lines)


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def current_branch(cwd=None):
    try:
        r = subprocess.run(["git", "symbolic-ref", "--short", "-q", "HEAD"], cwd=cwd,
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def classify(branch):
    if not branch:
        return "unknown"
    if DEV_BRANCH.match(branch):
        return "dev"
    if TRUNK.match(branch):
        return "trunk"
    return "other"


def cmd_commit_msg(path):
    hits = scan(read_text(path))
    if hits:
        print(explain(hits), file=sys.stderr)
        return 1
    return 0


def cmd_precheck():
    b = current_branch()
    kind = classify(b)
    print(f"当前分支：{b or '（无法判定 / 分离 HEAD）'}")
    if kind == "dev":
        print("开发分支，可原地提交（git-commit 2.1 首行）。")
    elif kind == "trunk":
        print("在主干：默认应从当前主干切开发分支再提交；主干直提仅凭开发者本次明确授权，单次有效（git-commit 2.5）。")
    elif kind == "other":
        print("既非主干也不匹配开发分支命名——先问开发者：按主干处理（切新分支）还是直接在此分支提交（git-commit 2.1）。")
    else:
        print("无法判定分支（分离 HEAD / 非 git 仓库）——停止并请开发者处理（git-commit 2.1）。")
    return 0


def extract_message(argv, cwd):
    """从 git commit 参数中取出提交信息：-m / --message（可多个）与 -F / --file。"""
    parts = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("-m", "--message") and i + 1 < len(argv):
            parts.append(argv[i + 1]); i += 2; continue
        if a.startswith("--message="):
            parts.append(a.split("=", 1)[1]); i += 1; continue
        if a.startswith("-m") and len(a) > 2:
            parts.append(a[2:]); i += 1; continue
        if a in ("-F", "--file") and i + 1 < len(argv):
            p = Path(argv[i + 1]); p = p if p.is_absolute() else Path(cwd or ".") / p
            if p.is_file():
                parts.append(read_text(p))
            i += 2; continue
        if a.startswith("--file="):
            p = Path(a.split("=", 1)[1]); p = p if p.is_absolute() else Path(cwd or ".") / p
            if p.is_file():
                parts.append(read_text(p))
            i += 1; continue
        i += 1
    return "\n".join(parts)


def git_commit_invocations(command):
    """把 Bash 命令按 && ; || | 切段，返回其中的 git commit 段（argv 列表）与该段的 -C 目录。"""
    out = []
    for seg in re.split(r"&&|\|\||;|\|", command):
        try:
            argv = shlex.split(seg, posix=True)
        except ValueError:
            continue
        if "git" not in argv:
            continue
        gi = argv.index("git")
        rest = argv[gi + 1:]
        if "commit" not in rest:
            continue
        cdir = None
        for j, a in enumerate(rest):
            if a == "-C" and j + 1 < len(rest):
                cdir = rest[j + 1]
        out.append((rest[rest.index("commit") + 1:], cdir))
    return out


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


def cmd_pretooluse():
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or None
    invocations = git_commit_invocations(command)
    if not invocations:
        return 0
    for argv, cdir in invocations:
        gdir = str(Path(cwd or ".") / cdir) if cdir else cwd
        hits = scan(extract_message(argv, gdir))
        if hits:
            decide("deny", explain(hits))
            return 0
        kind = classify(current_branch(gdir))
        if kind == "trunk":
            decide("ask", "当前在主干分支提交。主干直提需开发者本次明确授权，单次有效、不继承上次（git-commit 2.5）；"
                          "若已授权请允许，否则拒绝并让 AI 先切开发分支 {feat|opt|fix}/{yyyy.MM.dd}-{business}。")
            return 0
        if kind == "other":
            decide("ask", "当前分支不符合开发分支命名规则 {feat|opt|fix}/{yyyy.MM.dd}-{business}（git-commit 2.1）：确认直接在此分支提交？")
            return 0
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 0
    mode = argv[1]
    if mode == "commit-msg" and len(argv) > 2:
        return cmd_commit_msg(argv[2])
    if mode == "check-text" and len(argv) > 2:
        return cmd_commit_msg(argv[2])
    if mode == "precheck":
        return cmd_precheck()
    if mode == "pretooluse":
        return cmd_pretooluse()
    print(__doc__); return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        sys.exit(main(sys.argv))
    except SystemExit:
        raise
    except BaseException as e:  # fail-open：脚本故障不阻塞开发
        print(f"commit_guard 运行异常（{e!r}），本次未检查；请按 git-commit 铁律 3 人工自检。", file=sys.stderr)
        sys.exit(0)
