#!/usr/bin/env python3
"""reviewer Step 2 机械扫描：把能用规则判定的规范交给脚本，结果原样附进审查报告。

只用标准库（Python 3.8+）。只扫本次变更：新增文件扫全文，修改文件只扫改动行。
HIT 是确定违规（任何一条 HIT 都不能给出 ✅ 通过）；CANDIDATE 是候选，必须逐条判定后写进报告。
脚本不覆盖的维度在输出末尾列出，必须人工审查，不能因为脚本没报就当通过。

用法：
  python review-scan.py --repo <仓库目录> --base <基线提交或分支>            # 对比工作区（含未跟踪文件）
  python review-scan.py --repo <仓库目录> --base <基线> --head <提交>         # 对比两个提交
  python review-scan.py --repo <仓库目录> --files A.java B.java              # 指定文件，按全文扫描
退出码：0 无 HIT；1 有 HIT；2 参数或 git 错误。
"""
import argparse
import json
import re
import subprocess
import sys

VERSION = "1"

# 检查项：id -> (规则出处, 类型, 说明)
CHECKS = {
    "line-length": ("第三节", "HIT", "单行超过 120 字符（按字符计，中文算 1）"),
    "single-line-control": ("#59", "HIT", "if / else / for / while 不带花括号写成一行"),
    "multi-statement": ("#59", "HIT", "一行写了多条语句"),
    "wildcard-import": ("#60", "HIT", "通配 import（含 import static …*）"),
    "fqn": ("#60", "CANDIDATE", "代码里出现全限定类名（类内有重名时可保留，需写明）"),
    "javadoc-single-line": ("#61", "HIT", "方法 / 构造器使用单行 /** … */"),
    "javadoc-no-title": ("#61", "HIT", "Javadoc 只有标签没有标题"),
    "javadoc-no-blank": ("#61", "HIT", "Javadoc 标题 / 段落与标签之间没有空 * 行"),
    "type-doc": ("#58", "HIT", "新增类型缺类注释或缺 @author / @since"),
    "field-doc": ("#62", "CANDIDATE", "常量 / 配置 / 模型字段前没有 /** */"),
    "private-method-doc": ("#37", "CANDIDATE", "私有方法前没有 Javadoc"),
    "long-method-layout": ("#62", "CANDIDATE", "方法体 ≥15 行但没有空行分段或没有 // 说明"),
    "this-prefix": ("#35", "HIT", "调用本文件声明的实例方法未加 this."),
    "boolean-is": ("#4", "HIT", "布尔字段以 is 开头"),
    "copy-properties": ("#56", "CANDIDATE", "反射复制属性，需写明字段、null 与保留依据"),
    "runtime-exception": ("#22", "HIT", "直接抛 RuntimeException"),
    "requires-new": ("#46", "HIT", "REQUIRES_NEW 绕开主事务"),
    "stdout": ("logging #1/#2", "HIT", "System.out / System.err / printStackTrace"),
    "bigdecimal-literal": ("#43", "HIT", "用数值或 double 构造 BigDecimal"),
    "weak-crypto": ("#45", "HIT", "MD5 / SHA-1 / Math.random / new Random"),
    "hardcoded-secret": ("#47", "HIT", "硬编码密钥或密码"),
    "mapper-dollar": ("#41", "HIT", "mapper XML 使用 ${} 拼接"),
}

MANUAL = [
    "命名语义（缩写、动词位置、Service 方法命名）",
    "注释内容是否说清作用、契约（@param / @return 的含义）与反直觉点",
    "继承来的实例方法调用是否加了 this.（脚本只认本文件声明的方法）",
    "Entity / TableDef 同步与 TableDefCollect 注册（Step 3）",
    "DTO / Model 继承与字段映射（Step 4）",
    "Controller / Flow 职责与对外文档同步（Step 5）",
    "安全、金融专项（Step 5+）",
    "业务枚举 / 常量复用、转换映射的字段与 null 边界",
    "漏检史清单逐项核对",
]

KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "new", "else", "throw", "synchronized", "try", "do"}
MODS = r"(?:(?:public|protected|private|static|final|synchronized|abstract|default|native|strictfp)\s+)*"
SIG = re.compile(r"^\s*" + MODS + r"(?:<[^>]+>\s+)?[\w$.\[\]?<>,]+(?:<[^;{()]*>)?\s+(\w+)\s*\(")
CTOR = re.compile(r"^\s*(?:public|protected|private)\s+([A-Z]\w*)\s*\(")
FIELD = re.compile(r"^\s*(?:(?:private|protected|public|static|final|transient|volatile)\s+)+"
                   r"[\w$.\[\]?]+(?:<[^;()]*>)?\s+(\w+)\s*(?:=.*)?;\s*$")
TYPE_DECL = re.compile(r"^(?:(?:public|final|abstract|sealed|non-sealed|static)\s+)*"
                       r"(?:class|interface|enum|record|@interface)\s+\w+")
INJECT = re.compile(r"^\s*@(Resource|Autowired|Inject|Mock|MockBean|InjectMocks|Spy|SpyBean|Captor)\b")
CONTROL = re.compile(r"^\s*(?:\}\s*)?(?:if|else\s+if|for|while)\s*\(.*\)\s*[^{\s].*;\s*$")
ELSE_LINE = re.compile(r"^\s*(?:\}\s*)?else\s+(?!if\b)[^{\s].*;\s*$")
FQN = re.compile(r"(?<![\w.@$])(?:java|javax|jakarta|com|org|cn|io|net)\.(?:[a-z_][\w]*\.)+[A-Z]\w*")
STRING = re.compile(r'"(?:\\.|[^"\\])*"')
CHAR = re.compile(r"'(?:\\.|[^'\\])'")


def git(repo, *args):
    """执行 git 并返回 stdout 文本，失败时退出码 2"""
    r = subprocess.run(["git", "-C", repo] + list(args), capture_output=True)
    if r.returncode != 0:
        sys.stderr.write("git %s 失败：%s\n" % (" ".join(args), r.stderr.decode("utf-8", "replace")))
        sys.exit(2)
    return r.stdout.decode("utf-8", "replace")


def changed_files(repo, base, head):
    """返回 {路径: 'A' 或 'M'}，只收 .java 与 mapper .xml"""
    rng = [base, head] if head else [base]
    files = {}
    for line in git(repo, "diff", "--name-status", "--diff-filter=AMR", *rng).splitlines():
        parts = line.split("\t")
        status, path = parts[0][0], parts[-1]
        files[path] = "A" if status == "A" else "M"
    if not head:
        for path in git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
            files[path] = "A"
    return {p: s for p, s in files.items() if p.endswith(".java") or p.endswith(".xml")}


def changed_lines(repo, base, head, path):
    """解析 git diff -U0，返回修改文件中新增 / 改动行号集合"""
    rng = [base, head] if head else [base]
    lines = set()
    for line in git(repo, "diff", "-U0", *rng, "--", path).splitlines():
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            start, count = int(m.group(1)), int(m.group(2) or "1")
            lines.update(range(start, start + count))
    return lines


def read(repo, head, path):
    """读文件内容：指定 head 时取提交里的版本，否则读工作区"""
    if head:
        return git(repo, "show", "%s:%s" % (head, path))
    with open(repo + "/" + path, encoding="utf-8", errors="replace") as f:
        return f.read()


def code_view(lines):
    """逐行去掉字符串、字符字面量与注释，返回 (代码文本, 是否注释行) 列表"""
    out = []
    in_block = False
    for raw in lines:
        s = CHAR.sub("''", STRING.sub('""', raw))
        code = ""
        i = 0
        while i < len(s):
            if in_block:
                end = s.find("*/", i)
                if end < 0:
                    i = len(s)
                else:
                    in_block = False
                    i = end + 2
                continue
            if s.startswith("//", i):
                break
            if s.startswith("/*", i):
                in_block = True
                i += 2
                continue
            code += s[i]
            i += 1
        out.append((code, not code.strip()))
    return out


def count_top_semicolons(code):
    """统计括号外的分号数（排除 for 头部）"""
    depth = 0
    n = 0
    for ch in code:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            n += 1
    return n


def doc_end_before(lines, i):
    """从声明行往上找紧邻的注释结尾（跳过空行与多行注解），找到返回下标，否则返回 -1"""
    j = i - 1
    while j >= 0:
        s = lines[j].strip()
        if s.endswith("*/"):
            return j
        if s.startswith("//") or s.endswith((";", "{", "}")):
            return -1
        j -= 1
    return -1


def next_code_index(lines, i):
    """从第 i 行往下找，跳过空行与注解（含多行注解参数），返回第一行代码的下标"""
    j = i + 1
    while j < len(lines):
        s = lines[j].strip()
        if not s:
            j += 1
            continue
        if s.startswith("@"):
            depth = s.count("(") - s.count(")")
            j += 1
            while depth > 0 and j < len(lines):
                depth += lines[j].count("(") - lines[j].count(")")
                j += 1
            continue
        break
    return j


def is_method_sig(code):
    """判断是否为方法或构造器声明行"""
    if TYPE_DECL.match(code.strip()):
        return False
    m = SIG.match(code)
    if m and m.group(1) not in KEYWORDS and not re.match(r"^\s*(return|new|throw|else)\b", code):
        return True
    return bool(CTOR.match(code))


def scan_java(path, text, status, changed, hits):
    """扫描一个 Java 文件，命中写入 hits"""
    lines = text.splitlines()
    view = code_view(lines)

    def touched(a, b=None):
        if status == "A":
            return True
        return any(n in changed for n in range(a + 1, (b if b is not None else a) + 2))

    def add(check, idx, detail=""):
        hits.append({"check": check, "file": path, "line": idx + 1,
                     "text": (detail or lines[idx].strip())[:110]})

    # 本文件声明的实例方法（有同名静态方法的不算，避免误报）
    instance_methods, static_methods = set(), set()
    for code, _ in view:
        m = SIG.match(code)
        if m and is_method_sig(code):
            target = static_methods if re.search(r"\bstatic\b", code.split("(")[0]) else instance_methods
            target.add(m.group(1))
    instance_methods -= static_methods

    # 逐行规则
    for i, raw in enumerate(lines):
        if not touched(i):
            continue
        code, comment_only = view[i]
        if len(raw.rstrip("\r\n")) > 120:
            add("line-length", i, "%d 字符：%s" % (len(raw.rstrip()), raw.strip()))
        if raw.lstrip().startswith("import "):
            if re.match(r"^\s*import\s+(static\s+)?[\w.]+\.\*\s*;", raw):
                add("wildcard-import", i)
            continue
        if comment_only or raw.lstrip().startswith("package "):
            continue
        if CONTROL.match(code) or ELSE_LINE.match(code):
            add("single-line-control", i)
        if count_top_semicolons(code) > 1 and not re.match(r"^\s*for\s*\(", code):
            add("multi-statement", i)
        if FQN.search(code):
            add("fqn", i)
        if re.search(r"private\s+(Boolean|boolean)\s+is[A-Z]", code):
            add("boolean-is", i)
        if re.search(r"copyProperties\s*\(", code):
            add("copy-properties", i)
        if "throw new RuntimeException" in code:
            add("runtime-exception", i)
        if "REQUIRES_NEW" in code:
            add("requires-new", i)
        if re.search(r"System\.(out|err)\.print|\.printStackTrace\(", code):
            add("stdout", i)
        if re.search(r"new BigDecimal\(\s*-?[0-9]|new BigDecimal\(\s*\w*[dD]ouble", code):
            add("bigdecimal-literal", i)
        if re.search(r"Math\.random\(|new Random\(", code) or re.search(r'"(MD5|SHA-1)"', raw):
            add("weak-crypto", i)
        if re.search(r'(?i)(secret|password)\s*=\s*"[^"]+"|@Encryption\(key\s*=\s*"', raw):
            add("hardcoded-secret", i)
        if not is_method_sig(code):
            for name in instance_methods:
                if re.search(r"(?<![\w.$:])" + name + r"\s*\(", code) \
                        and not re.search(r"\bnew\s+" + name + r"\s*\(", code):
                    add("this-prefix", i)
                    break

    # Javadoc 块
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s.startswith("/**"):
            i += 1
            continue
        start = i
        if s.endswith("*/") and len(s) > 3:
            nxt = next_code_index(lines, i)
            if nxt < len(lines) and is_method_sig(view[nxt][0]) and touched(start, nxt):
                add("javadoc-single-line", start)
            i += 1
            continue
        end = start
        while end < len(lines) and "*/" not in lines[end]:
            end += 1
        if touched(start, end):
            body = [re.sub(r"^\s*\*\s?", "", ln).strip() for ln in lines[start + 1:end]]
            content = [b for b in body if b]
            if content and content[0].startswith("@"):
                add("javadoc-no-title", start)
            for k, b in enumerate(body):
                if b.startswith("@"):
                    if k > 0 and body[k - 1]:
                        add("javadoc-no-blank", start + 1 + k)
                    break
        i = end + 1

    # 类型、字段、方法
    for i, raw in enumerate(lines):
        code = view[i][0]
        if TYPE_DECL.match(code) and touched(i):
            p = doc_end_before(lines, i)
            doc = ""
            if p >= 0:
                q = p
                while q >= 0 and "/**" not in lines[q]:
                    q -= 1
                doc = "\n".join(lines[q:p + 1])
            if "@author" not in doc or "@since" not in doc:
                if status == "A":
                    add("type-doc", i)
        if FIELD.match(code) and touched(i):
            name = FIELD.match(code).group(1)
            p = i - 1
            injected = False
            while p >= 0 and lines[p].strip().startswith("@"):
                injected = injected or bool(INJECT.match(lines[p]))
                p -= 1
            mocked = re.search(r"=\s*(mock|spy)\(", code)
            if not injected and not mocked and name not in ("serialVersionUID", "log", "logger", "LOGGER") \
                    and not (p >= 0 and lines[p].strip().endswith("*/")):
                add("field-doc", i)
        if is_method_sig(code) and "{" in code and not code.strip().endswith(";"):
            documented = doc_end_before(lines, i) >= 0
            if re.search(r"\bprivate\b", code.split("(")[0]) and not documented and touched(i):
                add("private-method-doc", i)
            depth = 0
            end = i
            for j in range(i, len(lines)):
                depth += view[j][0].count("{") - view[j][0].count("}")
                if depth <= 0 and j > i:
                    end = j
                    break
            else:
                end = len(lines) - 1
            body = range(i + 1, end)
            if len(body) >= 15 and touched(i, end):
                blank = any(not lines[k].strip() for k in body)
                comment = any(lines[k].strip().startswith("//") for k in body)
                if not (blank and comment):
                    add("long-method-layout", i, "%d 行，空行=%s，// 说明=%s：%s"
                        % (len(body), "有" if blank else "无", "有" if comment else "无", raw.strip()))


def scan_xml(path, text, status, changed, hits):
    """扫描 mapper XML 中的 ${} 拼接"""
    if "<mapper" not in text:
        return
    for i, raw in enumerate(text.splitlines()):
        if (status == "A" or (i + 1) in changed) and "${" in raw:
            hits.append({"check": "mapper-dollar", "file": path, "line": i + 1, "text": raw.strip()[:110]})


def main():
    ap = argparse.ArgumentParser(description="reviewer Step 2 机械扫描")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", help="基线提交 / 分支（与 --files 二选一）")
    ap.add_argument("--head", help="对比的提交；不填则扫工作区（含未跟踪文件）")
    ap.add_argument("--files", nargs="*", help="指定文件，按全文扫描")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--max-per-check", type=int, default=30, help="每项最多列出的明细条数")
    args = ap.parse_args()
    if not args.base and not args.files:
        ap.error("需要 --base 或 --files")

    if args.files:
        targets = {f.replace("\\", "/"): "A" for f in args.files}
    else:
        targets = changed_files(args.repo, args.base, args.head)

    hits = []
    stats = {"A": 0, "M": 0}
    for path, status in sorted(targets.items()):
        text = read(args.repo, args.head, path) if not args.files else open(path, encoding="utf-8", errors="replace").read()
        changed = set() if status == "A" else changed_lines(args.repo, args.base, args.head, path)
        stats[status] += 1
        if path.endswith(".java"):
            scan_java(path, text, status, changed, hits)
        else:
            scan_xml(path, text, status, changed, hits)

    hard = [h for h in hits if CHECKS[h["check"]][1] == "HIT"]
    if args.json:
        print(json.dumps({"version": VERSION, "files": stats, "hits": hits}, ensure_ascii=False, indent=1))
        sys.exit(1 if hard else 0)

    scope = "--files 全文" if args.files else "%s..%s" % (args.base, args.head or "工作区")
    print("## reviewer 机械扫描（review-scan v%s）\n" % VERSION)
    print("范围：%s；新增 %d 个文件扫全文，修改 %d 个文件只扫改动行。\n" % (scope, stats["A"], stats["M"]))
    print("| 检查 | 规则 | 类型 | 命中 |\n|---|---|---|---:|")
    for cid, (rule, kind, desc) in CHECKS.items():
        n = sum(1 for h in hits if h["check"] == cid)
        print("| %s：%s | %s | %s | %d |" % (cid, desc, rule, kind, n))
    print("\nHIT 合计 %d（存在 HIT 不得判 ✅ 通过）；CANDIDATE 合计 %d（须逐条判定写进报告）。"
          % (len(hard), len(hits) - len(hard)))
    for cid in CHECKS:
        rows = [h for h in hits if h["check"] == cid]
        if not rows:
            continue
        print("\n### %s（%d）" % (cid, len(rows)))
        for h in rows[:args.max_per_check]:
            print("- %s:%d  `%s`" % (h["file"], h["line"], h["text"].replace("`", "'")))
        if len(rows) > args.max_per_check:
            print("- …其余 %d 条，加 --json 查看全部" % (len(rows) - args.max_per_check))
    print("\n### 脚本不覆盖，必须人工审查并写结论")
    for m in MANUAL:
        print("- " + m)
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    main()
