"""PreToolUse guard: blocks secrets and dangerous commands. Works on macOS, Linux, Windows.
Exit 2 = block, the stderr text goes back to Claude."""
import json
import re
import sys

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
inp = data.get("tool_input") or {}
path = (inp.get("file_path") or "").replace("\\", "/")
cmd = inp.get("command") or ""
name = path.rsplit("/", 1)[-1]

def block(msg):
    print(f"Blocked by .claude/hooks/guard.py: {msg}", file=sys.stderr)
    sys.exit(2)

if tool in ("Edit", "Write", "MultiEdit", "Read") and name.startswith(".env") and name != ".env.example":
    block(f"{name} holds secrets. Ask the user to edit it by hand.")
if tool in ("Edit", "Write", "MultiEdit"):
    text = json.dumps(inp)
    if re.search(r"sk-ant-[A-Za-z0-9_-]{10,}|sk-or-[A-Za-z0-9_-]{10,}|ghp_[A-Za-z0-9]{20,}", text):
        block("this edit contains what looks like an API key or token.")
if tool in ("Bash", "PowerShell"):
    if re.search(r"\b(cat|type|more|less|head|tail|Get-Content)\b[^|;&]*\.env(\s|$|\")", cmd):
        block("reading .env is not allowed.")
    if re.search(r"git\s+push\s+.*(--force|-f\b)", cmd):
        block("force push is not allowed. Open a PR instead.")
    if re.search(r"git\s+push\s+(origin\s+)?main\b", cmd):
        block("pushing to main directly is not allowed (CONTRIBUTING.md). Push a branch and open a PR.")
    if re.search(r"\brm\s+-rf?\s+(/|~|\.\s*$|\*)", cmd):
        block("broad rm -rf is not allowed.")
sys.exit(0)
