# Contributing

Short rules so five people can work in parallel without blocking each other.

## Golden rules

- `main` always works. Nobody pushes to `main` directly; everything goes through a pull request.
- One branch per task. Small pull requests get merged faster.
- Never commit secrets. API keys go into `.env`, which git ignores. Add every new variable to `.env.example` without its value.
- The data contracts in [contracts/](contracts/README.md) are our shared contract (single source: `contracts/models.py`). Announce changes to it in the team chat before merging.
- Code, comments, commits and docs are written in English.

## Daily workflow

```bash
# 1. Get the latest main
git switch main
git pull

# 2. Create a branch for your task
git switch -c feat/engine-scoring

# 3. Work, then commit
git add .
git commit -m "feat(engine): score methods by sample matrix"

# 4. Push and open a pull request
git push -u origin feat/engine-scoring
gh pr create --fill        # or open the pull request on github.com
```

If `main` moved on while you were working:

```bash
git switch main && git pull
git switch feat/engine-scoring
git merge main             # resolve conflicts if any, then commit
git push
```

## Branch names

`<type>/<area>-<short-description>`

| Type | Use for |
|---|---|
| `feat/` | new functionality |
| `fix/` | bug fixes |
| `docs/` | documentation only |
| `chore/` | setup, config, dependencies |
| `data/` | knowledge base, rules, test cases |

Areas: `backend`, `engine`, `prompts`, `frontend`, `knowledge`, `cases`, `eval`, `docs`.

Examples: `feat/frontend-briefing-view`, `data/cases-moisture`, `fix/backend-timeout`.

## Commit messages

`<type>(<area>): <what changed, imperative mood>`

```
feat(prompts): add parameter extraction prompt
fix(engine): handle missing temperature
data(knowledge): add NIR method card
docs(readme): add demo video link
```

## Pull requests

- Fill in the pull request template.
- At least one teammate reviews. Merges into `main`: _owner TBD at kickoff_.
- Use **Squash and merge** so the history of `main` stays readable.
- Delete the branch after merging.

## Definition of done

A task is done when it works on at least 3 test cases from `data/test-cases/` and is merged into `main`.

## Hackathon timeline

| When | What |
|---|---|
| Fri 16.10, 18:00 | Hackathon starts |
| Sun 18.10, 16:00 | Feature freeze: only fixes, docs and the demo video after this point |
| Sun 18.10, 22:00 | Our internal submission deadline |
| Sun 18.10, 23:59 | Official submission deadline |
