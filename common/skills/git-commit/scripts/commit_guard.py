#!/usr/bin/env python3
"""git-commit 铁律 1 / 3 的机械兜底：提交信息不得含 AI 记号与进度词；主干直提须开发者本次授权。

用法：
    commit_guard.py commit-msg <msgfile>   git 原生 commit-msg hook：命中 → 退出 1 拦截并说明原因
    commit_guard.py check-text <file>      对任意 UTF-8 文本（MR 标题 / 描述等）做同一检查，命中退出 1
    commit_guard.py precheck               提交前自检：打印当前分支判定与授权提醒，恒退出 0
    commit_guard.py pretooluse             Claude Code PreToolUse hook：stdin 读 JSON，命中 git commit / merge /
                                           cherry-pick / revert 时：AI 记号 → deny；在主干或分支无法判定 → ask
                                           （弹窗确认，单次授权）；提交信息经变量 / 命令替换传入 → ask；否则放行

主干名：默认 master / main / develop / release/*；项目另有主干名时在该仓 `git config --add yzj.trunk <name>`
（可多次，project-onboarding A-5 接入时执行）；临时环境也可设 YZJ_TRUNK_BRANCHES=a,b。

规则来源：common/skills/git-commit/SKILL.md 一、铁律 3（AI 记号 / 进度词）、2.1 分支决策表、2.5 主干直提单次授权、
2.6 禁止动作（AI 不合并到主干）。纯标准库、Python 3.8+。除 commit-msg / check-text 命中外，任何异常都放行（fail-open），
不阻塞开发；pretooluse 解析不了命令时退化为对整条命令全文扫描——宁可误拒，不静默放行。
分支按命令实际作用的目录判定：payload cwd + 前置 `cd` / `pushd` 段 + `git -C`；`--git-dir` / `--work-tree`、
分离 HEAD、目录不可解析一律 ask。
已知盲区（由 git 原生 hook 兜底）：`--trailer`、`--amend --no-edit` / `-C <commit>` 复用旧消息；
cherry-pick 搬入的旧提交信息两层都看不到（git 不对 cherry-pick 跑 commit-msg）。
"""
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# —— 铁律 3：AI 记号 ——
# 模型名：排除路径 / 文件名语境（前接 . /、后接 -xxx.ext 或 .ext），其余一律命中（含句末 "Claude."、"Claude-generated"、
# 紧贴中文的 "由Claude生成"）。边界只认 ASCII 字母数字——Python 的 \w 会把汉字也当单词字符，用 \w 会让中文紧贴的模型名漏检。
# Opus / Sonnet / Haiku 只认首字母大写，避免 "magnum opus"、"haiku 诗歌" 这类业务词误报。
MODEL_NAME = re.compile(
    r"(?<![A-Za-z0-9_/.])([Cc]laude(\s*[Cc]ode)?|[Aa]nthropic|Opus|Sonnet|Haiku)(?![A-Za-z0-9_])(?!-[\w-]*\.\w+)(?!\.\w)"
)
AI_MARKS = [
    (re.compile(r"(?im)^\s*co-authored-by\s*[:：].*$"), "Co-Authored-By 协作者尾注"),
    (re.compile(r"(?i)generated[\s-]+(with|by)\b"), "Generated with / by 来源尾注"),
    (MODEL_NAME, "模型 / 工具名"),
    (re.compile(r"🤖"), "AI 署名 emoji"),
    # "由 AI 生成 / AI 辅助（完成）" 与 "AI-generated / AI-assisted" 作为署名出现在句尾才算；"AI 辅助诊断模块" 这类业务名词不拦
    (re.compile(r"(?m)(由\s*AI\s*(生成|辅助|编写|撰写)|AI\s*(辅助|生成|编写|撰写))\s*(完成)?\s*[。.!！）)]?\s*$"), "\"由 AI 生成 / AI 辅助\" 署名"),
    (re.compile(r"(?im)\bAI[\s-]+(generated|assisted|written)\s*[.!)]?\s*$"), "\"AI-generated / AI-assisted\" 署名"),
]
# 作者 / 提交者身份里的 AI 记号（--author、-c user.name/email、GIT_AUTHOR_* 环境变量）；commit-msg hook 层看不到这些
IDENTITY_MARK = re.compile(r"(?i)claude|anthropic")
# —— 铁律 3：进度词（描述对话 / 流程进度而非代码意图） ——
PROGRESS_WORDS = [
    (re.compile(r"\bFIXED\b"), "FIXED"),
    (re.compile(r"\bStep\s*\d+\b"), "Step N"),
    (re.compile(r"\bPhase\s*\d+\b"), "Phase N"),
    (re.compile(r"\bP\d{1,2}\s*已过"), "Px 已过"),
]
# —— 2.1 分支决策表 ——
DEV_BRANCH = re.compile(r"^(feat|opt|fix)/\d{4}\.\d{2}\.\d{2}-[a-z0-9-]+$")
DEFAULT_TRUNK = re.compile(r"^(master|main|develop|release/.*)$")
# git 自动生成的注释块起始行（编辑器提交时 commit-msg 文件带此块；-m / -F 提交不带，# 行会原样进历史）
GIT_TEMPLATE_MARK = re.compile(r"^#\s*(Please enter the commit message|请为您的变更输入提交说明|On branch|位于分支)", re.M)
GIT_TOKEN = re.compile(r"(^|[\\/])git(\.exe)?$", re.I)
OPERATORS = {";", "&&", "||", "|", "&", "(", ")"}
# 会产生提交的 git 子命令：commit 之外，merge / cherry-pick / revert 在主干上同样直接产生主干提交
COMMIT_LIKE = {"commit", "merge", "cherry-pick", "revert"}
# git 全局选项：带参数的（-C / -c 单独处理）与纯开关的；其余以 - 开头的按开关处理
GLOBAL_WITH_ARG = {"--namespace", "--super-prefix", "--config-env", "--list-cmds", "--attr-source", "--exec-path"}
IDENT_ENV = re.compile(r"^GIT_(AUTHOR|COMMITTER)_(NAME|EMAIL)=(.*)$")
IDENT_CFG = re.compile(r"^(user|author|committer)\.(name|email)=(.*)$", re.I)
UNRESOLVED = object()  # 目录经变量 / `cd -` / --git-dir 等无法静态解析


def scan(text, strip_git_comments=False):
    """返回命中清单 [(类别, 规则名, 命中片段)]。只有 commit-msg 模式且文件带 git 注释块时才忽略 # 行。"""
    body = text
    if strip_git_comments and GIT_TEMPLATE_MARK.search(text):
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


def git(args, cwd=None):
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def current_branch(cwd=None):
    return git(["symbolic-ref", "--short", "-q", "HEAD"], cwd)


def trunk_names(cwd=None):
    names = set()
    for n in git(["config", "--get-all", "yzj.trunk"], cwd).splitlines():
        if n.strip():
            names.add(n.strip())
    for n in os.environ.get("YZJ_TRUNK_BRANCHES", "").split(","):
        if n.strip():
            names.add(n.strip())
    return names


def classify(branch, cwd=None):
    if not branch:
        return "unknown"
    if DEV_BRANCH.match(branch):
        return "dev"
    if DEFAULT_TRUNK.match(branch) or branch in trunk_names(cwd):
        return "trunk"
    return "other"


def cmd_commit_msg(path, strip_git_comments):
    hits = scan(read_text(path), strip_git_comments=strip_git_comments)
    if hits:
        print(explain(hits), file=sys.stderr)
        return 1
    return 0


def cmd_precheck():
    b = current_branch()
    kind = classify(b)
    print(f"当前分支：{b or '（无法判定 / 分离 HEAD）'}")
    extra = trunk_names()
    if extra:
        print(f"项目声明的主干：{', '.join(sorted(extra))}")
    if kind == "dev":
        print("开发分支，可原地提交（git-commit 2.1 首行）。")
    elif kind == "trunk":
        print("在主干：默认应从当前主干切开发分支再提交；主干直提仅凭开发者本次明确授权，单次有效（git-commit 2.5）。")
    elif kind == "other":
        print("既非主干也不匹配开发分支命名——先问开发者：按主干处理（切新分支）还是直接在此分支提交（git-commit 2.1）。")
    else:
        print("无法判定分支（分离 HEAD / 非 git 仓库）——停止并请开发者处理（git-commit 2.1）。")
    return 0


SHORT_CLUSTER = re.compile(r"^-([a-zA-Z]*)([mF])(.*)$")


def shellish(v):
    """值含变量 / 命令替换 / ~ 路径：hook 拿到的是未展开的字面量，无法核实真实内容。"""
    return bool(re.search(r"[$`]", v)) or v.startswith("~")


def extract_message(argv, cwd):
    """从 git commit / merge 参数中取出提交信息与作者身份。
    返回 dict：text（-m / -F 内容）、idents（--author 值）、full_scan（信息来自 stdin / 尚不存在的文件，须改扫整条命令）、
    unverifiable（信息经变量 / 命令替换 / ~ 路径传入，无法核实）。"""
    st = {"parts": [], "idents": [], "full_scan": False, "unverifiable": False}

    def from_file(p):
        if p == "-":
            st["full_scan"] = True  # heredoc / 管道正文就在命令里，改扫全文
            return ""
        if shellish(p):
            st["unverifiable"] = True
            return ""
        pp = Path(p)
        pp = pp if pp.is_absolute() else Path(cwd or ".") / pp
        if pp.is_file():
            return read_text(pp)
        st["full_scan"] = True  # 文件在同一条命令里才生成（printf > f && git commit -F f）：正文在命令里
        return ""

    def add_msg(v):
        if shellish(v):
            st["unverifiable"] = True
        st["parts"].append(v)

    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--message="):
            add_msg(a.split("=", 1)[1]); i += 1; continue
        if a == "--message" and i + 1 < len(argv):
            add_msg(argv[i + 1]); i += 2; continue
        if a.startswith("--file="):
            st["parts"].append(from_file(a.split("=", 1)[1])); i += 1; continue
        if a == "--file" and i + 1 < len(argv):
            st["parts"].append(from_file(argv[i + 1])); i += 2; continue
        if a.startswith("--author="):
            st["idents"].append(a.split("=", 1)[1]); i += 1; continue
        if a == "--author" and i + 1 < len(argv):
            st["idents"].append(argv[i + 1]); i += 2; continue
        m = SHORT_CLUSTER.match(a) if not a.startswith("--") else None
        if m:
            opt, rest = m.group(2), m.group(3)
            if rest:  # -mfoo / -amfoo
                val = rest
            elif i + 1 < len(argv):
                val = argv[i + 1]; i += 1
            else:
                val = ""
            if opt == "m":
                add_msg(val)
            else:
                st["parts"].append(from_file(val))
        i += 1
    st["text"] = "\n".join(st["parts"])
    return st


def tokenize(command):
    """整体分词（引号内的 ; | && 不会被当成分隔符），返回 [("op", 运算符) | ("seg", argv)]。解析失败抛 ValueError。"""
    lex = shlex.shlex(command, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    items, cur = [], []
    for tok in lex:
        if tok in OPERATORS:
            if cur:
                items.append(("seg", cur))
                cur = []
            items.append(("op", tok))
        else:
            cur.append(tok)
    if cur:
        items.append(("seg", cur))
    return items


def parse_git(argv):
    """一段命令若是会产生提交的 git 调用，返回 {sub, args, cdir, unresolvable, idents}，否则 None。
    子命令 = git 之后第一个非全局选项的 token（`git help commit`、`git log -- commit` 不算）。"""
    idents, gi = [], None
    for k, t in enumerate(argv):
        if GIT_TOKEN.search(t):
            gi = k
            break
        m = IDENT_ENV.match(t)  # GIT_AUTHOR_NAME=x git commit …
        if m:
            idents.append(m.group(3))
    if gi is None:
        return None
    rest = argv[gi + 1:]
    cdir, unresolvable, sub, args = None, False, None, []
    j = 0
    while j < len(rest):
        a = rest[j]
        if a == "-C" and j + 1 < len(rest):
            cdir = rest[j + 1]; j += 2; continue
        if a == "-c" and j + 1 < len(rest):
            m = IDENT_CFG.match(rest[j + 1])
            if m:
                idents.append(m.group(3))
            j += 2; continue
        if a.startswith("--git-dir") or a.startswith("--work-tree"):
            unresolvable = True
            j += 1 if "=" in a else 2; continue
        if a.startswith("-"):
            j += 2 if (a in GLOBAL_WITH_ARG and "=" not in a) else 1
            continue
        sub, args = a, rest[j + 1:]
        break
    if sub not in COMMIT_LIKE:
        return None
    return {"sub": sub, "args": args, "cdir": cdir, "unresolvable": unresolvable, "idents": idents}


def git_commit_invocations(command):
    """返回会产生提交的 git 调用列表（含其前置 cd / pushd 累积的目录偏移）；分词失败抛 ValueError 交上层退化处理。"""
    out, shift, stack = [], None, []
    for kind, val in tokenize(command):
        if kind == "op":
            if val == "(":
                stack.append(shift)
            elif val == ")" and stack:
                shift = stack.pop()
            continue
        argv = val
        if argv and argv[0] in ("cd", "pushd"):
            target = argv[1] if len(argv) > 1 else None
            if target is None or target == "-" or shellish(target):
                shift = UNRESOLVED
            elif shift is not UNRESOLVED:
                shift = target if (shift is None or Path(target).is_absolute()) else str(Path(shift) / target)
            continue
        g = parse_git(argv)
        if g:
            g["shift"] = shift
            out.append(g)
    return out


def resolve_dir(cwd, g):
    """命令实际作用的仓库目录；无法静态解析返回 None。"""
    if g["unresolvable"] or g["shift"] is UNRESOLVED:
        return None
    base = Path(cwd or ".")
    if g["shift"]:
        base = base / g["shift"]
    if g["cdir"]:
        if shellish(g["cdir"]):
            return None
        base = base / g["cdir"]
    return str(base)


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


TRUNK_ASK = ("当前在主干分支提交。主干直提需开发者本次明确授权，单次有效、不继承上次（git-commit 2.5）；"
             "若已授权请允许，否则拒绝并让 AI 先切开发分支 {feat|opt|fix}/{yyyy.MM.dd}-{business}。")
OTHER_ASK = "当前分支不符合开发分支命名规则 {feat|opt|fix}/{yyyy.MM.dd}-{business}（git-commit 2.1）：确认直接在此分支提交？"
UNKNOWN_ASK = ("无法判定本次提交作用的分支（分离 HEAD / 非 git 仓库 / 目录经 --git-dir、变量或 `cd -` 指定，hook 无法静态解析）："
               "确认目标分支不是主干、且已获授权后再允许（git-commit 2.1 / 2.5）。")
MERGE_ASK = ("当前在主干分支执行 merge：AI 不得自行合并到主干（git-commit 2.6），只能由开发者本次明确授权；"
             "若已授权请允许，否则拒绝。")
REPLAY_ASK = ("当前在主干分支执行 {sub}，会直接产生主干提交（git-commit 2.5 主干直提单次授权）；"
              "搬入的旧提交信息 hook 看不到，请同时确认其中没有 AI 记号。")
UNVERIFIABLE_ASK = ("提交信息经变量 / 命令替换 / ~ 路径传入，hook 拿到的是未展开的字面量，无法核实是否含 AI 记号或进度词："
                    "确认信息已按 git-commit 铁律 3 人工自检后再允许。")


def cmd_pretooluse():
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # 宿主以 UTF-8 写入；中文 Windows 默认 GBK 会毁掉中文规则
    except Exception:
        pass
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or None
    if not re.search(r"\bgit\b", command) or not any(s in command for s in COMMIT_LIKE):
        return 0
    try:
        invocations = git_commit_invocations(command)
    except ValueError:
        # 分词失败（引号不配对等）：退化为全文扫描，宁可误拒不静默放行；分支按 cwd 判
        hits = scan(command)
        if hits:
            decide("deny", explain(hits) + "\n（命令无法完整解析，已按全文检查）")
            return 0
        invocations = [{"sub": "commit", "args": [], "cdir": None, "unresolvable": False, "idents": [], "shift": None}]
    if not invocations:
        return 0
    # 先查所有段的 AI 记号（任一命中即 deny），再做分支判定——避免 ask 抢在 deny 前返回
    unverifiable = False
    for g in invocations:
        gdir = resolve_dir(cwd, g) or cwd
        hits = []
        if g["sub"] in ("commit", "merge"):
            msg = extract_message(g["args"], gdir)
            hits += scan(msg["text"])
            if msg["full_scan"]:
                hits += [h for h in scan(command) if h not in hits]
            unverifiable = unverifiable or msg["unverifiable"]
            g["idents"] = g["idents"] + msg["idents"]
        for v in g["idents"]:
            if IDENTITY_MARK.search(v):
                hits.append(("AI 记号", "作者 / 提交者身份", v.strip()[:60]))
        if hits:
            decide("deny", explain(hits))
            return 0
    for g in invocations:
        gdir = resolve_dir(cwd, g)
        kind = classify(current_branch(gdir), gdir) if gdir is not None else "unknown"
        if kind == "unknown":
            decide("ask", UNKNOWN_ASK)
            return 0
        if kind == "trunk":
            if g["sub"] == "merge":
                decide("ask", MERGE_ASK)
            elif g["sub"] in ("cherry-pick", "revert"):
                decide("ask", REPLAY_ASK.format(sub=g["sub"]))
            else:
                decide("ask", TRUNK_ASK)
            return 0
        if kind == "other" and g["sub"] == "commit":
            decide("ask", OTHER_ASK)
            return 0
    if unverifiable:
        decide("ask", UNVERIFIABLE_ASK)
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 0
    mode = argv[1]
    if mode == "commit-msg" and len(argv) > 2:
        return cmd_commit_msg(argv[2], strip_git_comments=True)
    if mode == "check-text" and len(argv) > 2:
        return cmd_commit_msg(argv[2], strip_git_comments=False)
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
