"""PostToolUse: after an edit, run the check that belongs to the edited folder.
On failure exit 2 so Claude sees the error and fixes it."""
import json
import os
import subprocess
import sys

data = json.load(sys.stdin)
path = ((data.get("tool_input") or {}).get("file_path") or "").replace("\\", "/")
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
env = dict(os.environ, LLM_MOCK="1")

checks = []
if "/contracts/" in path:
    checks.append([sys.executable, "contracts/check_contracts.py"])
if "/rules/" in path or "/engine/" in path:
    checks.append([sys.executable, "-m", "engine.selftest"])
if "/llm/" in path:
    checks.append([sys.executable, "-m", "llm.selftest"])

for c in checks:
    r = subprocess.run(c, cwd=root, env=env, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        tail = (r.stdout + r.stderr).strip().splitlines()[-15:]
        print("Check failed: " + " ".join(c[1:]) + "\n" + "\n".join(tail), file=sys.stderr)
        sys.exit(2)
sys.exit(0)
