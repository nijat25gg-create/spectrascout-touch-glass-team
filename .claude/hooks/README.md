# Hooks

Python, so they run on macOS, Linux and Windows. They are NOT registered in the shared
settings.json, because the Python command differs (python3 on Mac, python on Windows).
Each person registers them in `.claude/settings.local.json` (stays out of git).

macOS / Linux:
```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit|Read|Bash",
        "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard.py\"" }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/after_edit.py\"" }] }
    ],
    "SessionStart": [
      { "matcher": "compact",
        "hooks": [{ "type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/reminder.py\"" }] }
    ],
    "Notification": [
      { "matcher": "",
        "hooks": [{ "type": "command", "command": "osascript -e 'display notification \"Claude ждёт ответа\" with title \"SpectraScout\"'" }] }
    ]
  }
}
```

Windows: same file, replace `python3` with `python`, and drop the Notification block.

Check: type `/hooks` in Claude Code, the hooks should be listed.
