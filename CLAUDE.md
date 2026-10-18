@AGENTS.md

## Claude Code notes
- Use plan mode (Shift+Tab) for anything touching more than 2 files.
- Delegate narrow checks to the subagents in .claude/agents (see .claude/agents/README.md).
  Run independent checks in parallel.
- Big fan-out jobs (label all test cases, audit the repo, research all 6 method cards)
  can run as a dynamic workflow. Start small, Pro limits are shared with claude.ai.
- When a contract changes, tell the user which teammates must update what.
- Before a PR run /pre-pr.
