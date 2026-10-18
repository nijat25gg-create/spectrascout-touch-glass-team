"""SessionStart (matcher: compact): re-inject the key rules after context compaction."""
import subprocess

print("Reminder after compaction: pipeline extract → score_methods → explain is frozen; "
      "contracts only additive; LLM_MOCK=1 by default; never touch .env; branch + PR, no push to main; "
      "the product is not multi-agent.")
try:
    log = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, timeout=10).stdout
    print("Recent commits:\n" + log)
except Exception:
    pass
