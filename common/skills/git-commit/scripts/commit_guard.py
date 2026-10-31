#!/usr/bin/env python3
"""git-commit 铁律 3 的机械兜底：提交信息不得含 AI 记号与进度词。这是提交流程里唯一的机械门禁；
授权、分支、MR 等其余要求按 git-commit 技能文字执行，脚本不判定。

用法：
    commit_guard.py commit-msg <msgfile>   git 原生 commit-msg hook：命中 → 退出 1 拦截并说明原因（硬门禁）
    commit_guard.py check-text <file>      对任意 UTF-8 文本（MR 标题 / 描述等）做同一检查，命中退出 1
    commit_guard.py pretooluse             Claude Code PreToolUse hook（Bash / PowerShell）：stdin 读 JSON，
                                           命令含 git commit / merge，或创建 / 编辑 MR（gh pr、glab mr、调
                                           pulls / merge_requests 接口）时，对整条命令文本与其引用的已存在
                                           正文文件（-F / --file / --body-file / --input / @文件）做同一检查，
                                           命中 → deny；否则放行

分层：commit-msg 检查的是最终写进提交的信息，与命令怎么写无关，是硬门禁；pretooluse 只是让 AI 在执行前就收到
拒绝理由的早期预检，不解析 shell——全文扫描，命中的若不是提交信息 / MR 正文，把提交或建 MR 拆成单独一条命令即可。
MR 文本没有 git 侧的硬门禁：pretooluse 只覆盖上述命令写法，网页上手填或其他写法靠创建前跑 check-text。
规则来源：common/skills/git-commit/SKILL.md 一、铁律 3。纯标准库、Python 3.8+。
除 commit-msg / check-text 命中外，任何异常都放行（fail-open），不阻塞开发。
"""
import json
import re
import sys
from pathlib import Path

# —— 铁律 3：AI 记号 ——
# 模型名：Claude / Claude Code / Anthropic 不区分大小写；Opus / Sonnet / Haiku 只认首字母大写，避免 "magnum opus"、
# "haiku 诗歌" 这类业务词误报。排除路径 / 文件名语境：前接 . / \（.claude/、Windows 路径 \Temp\claude\ 常出现在 -F 参数里），
# 或后接常见文件扩展名（CLAUDE.md、claude-settings-hooks.json）；claude.ai、anthropic.com、claude-sonnet-4.5 这类域名 /
# 型号写法照拦。边界只认 ASCII 字母数字——Python 的 \w 会把汉字也当单词字符，用 \w 会让中文紧贴的模型名漏检。
FILE_EXT = r"(?:md|json|py|sh|txt|ya?ml|toml|js|ts|template|local)(?![A-Za-z0-9_])"
MODEL_NAME = re.compile(
    r"(?<![A-Za-z0-9_/.\\])((?i:claude(\s*code)?|anthropic)|Opus|Sonnet|Haiku)(?![A-Za-z0-9_])(?!(?:-[\w-]*)?\." + FILE_EXT + ")"
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
# —— 铁律 3：进度词（描述对话 / 流程进度而非代码意图） ——
PROGRESS_WORDS = [
    (re.compile(r"\bFIXED\b"), "FIXED"),
    (re.compile(r"\bStep\s*\d+\b"), "Step N"),
    (re.compile(r"\bPhase\s*\d+\b"), "Phase N"),
    (re.compile(r"\bP\d{1,2}\s*已过"), "Px 已过"),
]
# git 自动生成的注释块起始行（编辑器提交时 commit-msg 文件带此块；-m / -F 提交不带，# 行会原样进历史）
GIT_TEMPLATE_MARK = re.compile(r"^#\s*(Please enter the commit message|请为您的变更输入提交说明|On branch|位于分支)", re.M)
# pretooluse 触发条件（不解析 shell，宁可多查）：命令里出现 git 且出现 commit / merge；或创建 / 编辑 MR——
# gh pr create / edit、glab mr create / update，或 curl / gh api / Invoke-RestMethod 等调 pulls / merge_requests 接口
GIT_WORD = re.compile(r"(?<![\w.-])git(\.exe)?(?![\w.-])", re.I)
COMMIT_WORD = re.compile(r"(?<![\w-])(commit|merge)(?![\w-])")
MR_CLI = re.compile(r"(?<![\w.-])(gh(\.exe)?\s+pr\s+(create|edit)|glab(\.exe)?\s+mr\s+(create|update))(?![\w-])", re.I)
API_CLIENT = re.compile(r"(?<![\w.-])(curl(\.exe)?|gh(\.exe)?\s+api|Invoke-RestMethod|Invoke-WebRequest|irm|iwr)(?![\w-])", re.I)
MR_API = re.compile(r"/(pulls|merge_requests)(?![\w-])", re.I)
# 引用的正文文件（只取已存在的文件读入；同一条命令里才写出的文件，正文本就在命令文本里）：-F / --file（git commit 的
# 消息文件，也是 gh pr 的正文文件）、--body-file、--input（gh api），以及 curl / gh api 的 @文件（-d @x、-F body=@x）
MSG_FILE = re.compile(r"(?:^|\s)(?:-[a-zA-Z]*F|--file|--body-file|--input)(?:=|\s+)(\"[^\"]+\"|'[^']+'|[^\s;&|<>()]+)")
AT_FILE = re.compile(r"(?:^|[\s=])[\"']?@(\"[^\"]+\"|'[^']+'|[^\s;&|<>()\"']+)")
MSYS_PATH = re.compile(r"^/([A-Za-z])(/|$)")  # Git Bash 的 /c/… 路径，Windows 上 Path 不认为是绝对路径
HOOK_TOOLS = {"Bash", "PowerShell"}


def scan(text, strip_git_comments=False):
    """返回命中清单 [(类别, 规则名, 命中片段)]。只有 commit-msg 模式且文件带 git 注释块时才忽略 # 行。"""
    body = text
    if strip_git_comments and GIT_TEMPLATE_MARK.search(text):
        body = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
    # printf / echo -e 里的字面 \n 会在提交时变成换行：先展开，否则行首规则与边界规则看不到
    body = body.replace("\\r\\n", "\n").replace("\\n", "\n")
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
    lines = ["提交信息 / MR 文本违反 git-commit 铁律 3："]
    lines += [f"  - {kind}「{label}」：{frag}" for kind, label, frag in hits]
    lines.append("删除后重新提交（不要加任何 AI 署名 / 来源尾注；不要用 FIXED / Step N / Phase N 描述进度）。")
    return "\n".join(lines)


def read_text(path):
    return Path(path).read_text(encoding="utf-8", errors="replace")


def cmd_commit_msg(path, strip_git_comments):
    hits = scan(read_text(path), strip_git_comments=strip_git_comments)
    if hits:
        print(explain(hits), file=sys.stderr)
        return 1
    return 0


def is_target(command):
    if GIT_WORD.search(command) and COMMIT_WORD.search(command):
        return True
    return bool(MR_CLI.search(command) or (API_CLIENT.search(command) and MR_API.search(command)))


def referenced_files(command, cwd):
    """命令里 -F / --file / --body-file / --input / @文件 指向的、此刻已存在的正文文件内容。"""
    texts = []
    for m in list(MSG_FILE.finditer(command)) + list(AT_FILE.finditer(command)):
        p = m.group(1).strip("\"'")
        if p == "-":
            continue
        try:
            pp = Path(MSYS_PATH.sub(lambda x: x.group(1).upper() + ":/", p))
            pp = pp if pp.is_absolute() else Path(cwd or ".") / pp
            if pp.is_file():
                texts.append(read_text(pp))
        except Exception:
            continue
    return texts


def decide(decision, reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))


def cmd_pretooluse():
    try:
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")  # 宿主以 UTF-8 写入；中文 Windows 默认 GBK 会毁掉中文规则
    except Exception:
        pass
    payload = json.load(sys.stdin)
    if payload.get("tool_name") not in HOOK_TOOLS:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not is_target(command):
        return 0
    hits = scan(command)
    for text in referenced_files(command, payload.get("cwd") or None):
        hits += [h for h in scan(text) if h not in hits]
    if hits:
        decide("deny", explain(hits) + "\n（按整条命令全文检查；命中的若不是提交信息 / MR 正文，把提交或建 MR 拆成单独一条命令）")
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 0
    mode = argv[1]
    if mode == "commit-msg" and len(argv) > 2:
        return cmd_commit_msg(argv[2], strip_git_comments=True)
    if mode == "check-text" and len(argv) > 2:
        return cmd_commit_msg(argv[2], strip_git_comments=False)
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
