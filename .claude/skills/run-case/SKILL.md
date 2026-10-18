---
description: Run one customer text through the pipeline and show parameters, scores, questions and experiment. Use when the user pastes a customer use case or says "прогони кейс".
---
Run `LLM_MOCK=1 python run_case.py "$ARGUMENTS" de` (use `en` for English text; drop LLM_MOCK only if the user asks for the real API).
Show in Russian: unknown parameters, ranked methods with score and the rule ids behind them, rejected methods with reason, top 3 questions, the experiment goal, and the gates block (status, selected rows, premises, method questions, lab checks). Point out where the old ranking and the gates assessment disagree.
Then ask whether to run @agent-afs-expert-critic on the result.
