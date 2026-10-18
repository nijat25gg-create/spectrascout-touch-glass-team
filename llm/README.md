# llm/ — шаги A и B (Ниджат)

```python
from llm import extract, explain
extraction = extract(ExtractInput(...))     # C2 -> C3
explanation = explain(ExplainInput(...))    # C6 -> C7
```

- `LLM_MOCK=1` в `.env`: возвращает примеры из `contracts/examples`, ключ не нужен, денег не тратит. Для бэкенда и фронта по умолчанию.
- `LLM_MOCK=0` и `ANTHROPIC_API_KEY` в `.env`: настоящий вызов Claude (`MODEL`, по умолчанию `claude-sonnet-5-5`).
- Проверка: `LLM_MOCK=1 python3 -m llm.selftest`
- Промпты: `llm/prompts/*.md`. Шаг A готов, шаг B черновик до чт 15.10.
- Повтор при ошибке (`LLM_RETRIES`, по умолчанию 2), таймаут `LLM_TIMEOUT_S` (60 с), в лог пишется время и токены.
- После шага A код гарантирует все 16 параметров по порядку и убирает цитаты, которых нет в тексте клиента.
