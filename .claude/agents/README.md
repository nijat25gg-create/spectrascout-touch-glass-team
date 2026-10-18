# Subagents (developer tools, not part of the product)

| Agent | Model | Can edit? | Who uses it | When |
|---|---|---|---|---|
| contracts-guard | haiku | no | Nidzhat, Semyon | after contract or schema edits |
| rules-reviewer | opus | no | Nikita | after gates.yaml edits, odd rankings |
| case-evaluator | sonnet | no | team | every evening, numbers for the video |
| literature-scout | sonnet | only kb/evidence/ | Nikita | evidence for cards and rules |
| integration-checker | sonnet | no | Semyon, Gadzhi | after backend/frontend edits, 17:00 run |
| afs-expert-critic | opus | no | everyone | on a real briefing, before demos |
| pr-reviewer | sonnet | no | everyone | before every PR |
| secret-scanner | haiku | no | everyone | before push, before the link goes public |
| ux-reviewer | sonnet | no | Gadzhi | after UI changes |
| demo-coach | opus | no | Nidzhat | video script, README, submission |

Call one explicitly: type `@` and pick it, or write `@agent-rules-reviewer ...`.
Run several at once: "run pr-reviewer, secret-scanner and contracts-guard in parallel".
Ctrl+B moves a running subagent to the background.
Read-only is enforced by `tools` / `disallowedTools`, not by trust.
