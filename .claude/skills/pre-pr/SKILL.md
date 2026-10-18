---
description: Full pre-PR gate. Use before opening a pull request or when the user says "готов к PR".
---
1. Run /check.
2. In parallel run the subagents pr-reviewer, secret-scanner and, if contracts/ or backend/app/schemas changed, contracts-guard.
3. Merge their findings into one list ordered by severity.
4. If all clean: propose the PR title and body following .github/pull_request_template.md and CONTRIBUTING.md. Do not push without the user's OK.
