---
description: Write a short team status message in Russian from recent git activity. Use when the user asks "что написать ребятам", "статус" or before a team call.
disable-model-invocation: true
---
## Recent activity
!`git log --all --since="18 hours ago" --oneline --decorate`

## Current branch state
!`git status --short`

Write a chat message in Russian, short, warm, no em-dashes, at most one emoji, in this shape:
Статус [время]
Готово: ...
Сейчас: ...
Блокирует: ... (кто может помочь)
Следующий созвон: ...
Name people by first name. Do not invent progress that is not in the activity above; ask the user for anything else.
