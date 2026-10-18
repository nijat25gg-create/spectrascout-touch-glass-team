# Контракты SpectraScout v0.2

Контракт это правило «рукопожатия» между двумя частями продукта: какие поля передаются, какого типа и какие значения допустимы. Данные в каждом запросе разные, а форма всегда одна и та же.

- **Источник правды:** `models.py` (Pydantic). JSON Schema в `schemas/` генерируются из него командой `python contracts/export_schemas.py`. Руками `.json` не правим.
- **Примеры:** `examples/` — один и тот же кейс (влажность порошка) проходит через все контракты, данные согласованы между собой.
- **Проверка:** `python contracts/check_contracts.py`. Должно быть `OK, all checks passed`. Запускаем после каждого изменения.
- **Менять контракт** может только Ниджат (CS 1), после согласования с теми, кого он касается. Каждое изменение: новая версия и сообщение в чат.

## Сколько контрактов

**8 на основной проход `/assessments`** (Семён прав) плюс **2 служебных**:

| № | Имя | От → Кому | Стрелка на схеме | Как передаётся |
| --- | --- | --- | --- | --- |
| C1 | `AnalyzeRequest` | Гаджи (фронт) → Семён (бэкенд) | 2 | HTTP `POST /assessments` |
| C2 | `ExtractInput` | Семён → Ниджат (LLM, шаг А) | 4 | вызов функции `llm.extract()` |
| C3 | `Extraction` | Ниджат → Семён | 5 | ответ `llm.extract()` |
| C4 | `ScoreInput` | Семён → движок gates | 6 | вызов функции `engine.score_methods()` (v0.3: + `attributes`) |
| C5 | `Scoring` | движок gates → Семён | 7 | ответ `engine.score_methods()`: ranked/rejected из gates + `assessment` |
| C6 | `ExplainInput` | Семён → Ниджат (LLM, шаг Б) | 8 | вызов функции `llm.explain()` |
| C7 | `Explanation` | Ниджат → Семён | 9 | ответ `llm.explain()` |
| C8 | `Briefing` | Семён → Гаджи | 10 и 16 | HTTP-ответ `/assessments` и `/assessments/recalculate` |
| C1b | `RecomputeRequest` | Гаджи → Семён | 13 | HTTP `POST /assessments/recalculate` |
| E | `ErrorResponse` | Семён → Гаджи | любая ошибка | HTTP 4xx или 5xx |

Не контракты: стрелка 3 (проверка внутри бэкенда), стрелки 1, 11, 12 (действия эксперта в интерфейсе).

**Пересчёт** (`/assessments/recalculate`): вход другой (C1b, потому что фронт присылает брифинг и правки, а не текст), шаг А пропускается, дальше те же C4 → C5 → C6 → C7 → C8. Новых контрактов для пересчёта не нужно, кроме C1b.

## Ответы на вопросы с созвона

- **Старый `briefing.schema.json` (v0.1)** был контрактом **C8**, стрелка 10: полный ответ фронту. Это не 16 параметров.
- **Старый `briefing.example.json`** был **примером данных** для той же стрелки 10, а не отдельной стрелкой.
- **16 параметров** это контракт **C3**, стрелка 5: Ниджат → Семён.
- **Поле `methods` в брифинге** приходит от Ярика (C5), Семён только добавляет к нему объяснения из C7.
- В v0.2 старая папка `docs/contract/` удалена, всё лежит здесь, у каждого файла номер.

## Что изменилось после проверки пайплайна

1. **Все вызовы идут только через бэкенд.** На карте команды LLM передавала параметры прямо в движок, это была ошибка. LLM и движок друг о друге не знают.
2. **Добавлены `features`** — 12 нормализованных признаков с фиксированными значениями (например `phase = solid_powder`, `water_level = low`). Движок правил не может читать свободный текст вроде «1–5 %», поэтому Ярик работает только с `features`. 16 параметров остаются для эксперта на экране.
3. **Вопрос связан с признаком.** У вопроса есть поле `feature`, ответ эксперта приходит как `feature_value` из выпадающего списка. Так пересчёт меняет баллы без нового вызова LLM.
4. **Разделение авторства:** баллы и причины отказов считает движок (C5), объяснения пишет LLM (C7), Семён склеивает их в C8.
5. **Карточки знаний** Никиты Ниджат загружает внутри своего модуля, в контракт они не входят. В ответе C7 у каждого утверждения есть ссылка `kb_card`.
6. **Движок вызывается как обычная Python-функция внутри бэкенда**, без отдельного HTTP-сервера. Так проще и быстрее.

## Контракты по одному

### C1 · `AnalyzeRequest` · Гаджи → Семён
| Поле | Тип | Правило |
| --- | --- | --- |
| `text` | строка | 20–3000 символов |
| `language` | `de` или `en` | выбирает эксперт |
Если правило нарушено, Семён отвечает **E** с кодом `validation_error`. Лишние поля запрещены.

### C2 · `ExtractInput` · Семён → Ниджат
`case_id` (создаёт Семён), `text` и `language` без изменений из C1.

### C3 · `Extraction` · Ниджат → Семён
- `summary`: задача клиента одним предложением.
- `parameters`: ровно 16, каждый `id` один раз. У каждого `value`, `status` (`known` / `assumed` / `unknown`), `evidence_quote` (цитата клиента, только если `known`), `source`.
- `features`: 12 признаков, у каждого `value` из списка и `status`.
Эту схему Ниджат передаёт Claude как формат ответа. Проверено, что она укладывается в лимиты structured outputs.

### C4 · `ScoreInput` · Семён → Ярик
`case_id` и `features` без изменений из C3 (или с правками эксперта при пересчёте).

### C5 · `Scoring` · Ярик → Семён
- `rules_version`: версия правил.
- `ranked`: 1–3 метода, `rank` от 1. У каждого `mode`, `spectral_range`, `fiber`, `probe`, `scores` по критериям, `score_total` = сумма `scores`, `confidence`.
- `rejected`: остальные методы, у каждого `reason`, `rule_id`, `blocker` (исключён жёстким правилом или просто мало баллов).
Каждый из 6 методов стоит ровно в одном списке.

### C6 · `ExplainInput` · Семён → Ниджат
`case_id`, `language`, `summary`, `parameters`, `features` из C3 и весь `scoring` из C5 без изменений.

### C7 · `Explanation` · Ниджат → Семён
- `questions`: вопросы клиенту только про то, что `unknown` или `assumed`. У каждого `priority`, `why`, `parameter_id`, `feature`.
- `rationale`: для каждого метода из `ranked` список утверждений со ссылкой `kb_card`.
- `experiment`: план первого теста, сравниваются только методы из `ranked`.
- `risks`: риски с `severity`.

### C8 · `Briefing` · Семён → Гаджи
Склейка: `summary`, `parameters`, `features` из C3, `methods.ranked` = C5 + `claims` из C7, `methods.rejected` = C5, `questions` (+ `answer`), `experiment`, `risks` из C7. Плюс от Семёна: `expert_flags`, `changes` (пусто при `/assessments`, что поменялось при `/assessments/recalculate`), `meta`.

### C1b · `RecomputeRequest` · Гаджи → Семён
`briefing` (последний C8), `edits` (правки признаков: `feature`, `value` из списка, `note`), `answers` (`question_id`, `answer`, `feature_value`).

### E · `ErrorResponse` · Семён → Гаджи
`error.code`: `validation_error`, `llm_error`, `engine_error`, `internal_error`; `message` для человека; `details` для разработчика.

## Функции, которые обещают друг другу

```python
# Ниджат, модуль llm/
def extract(inp: ExtractInput) -> Extraction: ...          # C2 -> C3
def explain(inp: ExplainInput) -> Explanation: ...         # C6 -> C7

# Ярик, модуль engine/
def score_methods(inp: ScoreInput) -> Scoring: ...         # C4 -> C5

# Семён, backend/
POST /assessments   body: AnalyzeRequest   -> Briefing | ErrorResponse
POST /assessments/recalculate body: RecomputeRequest -> Briefing | ErrorResponse
```

Пути на бэкенде Семёна (FastAPI). Браузер ходит на `/api/assessments` и `/api/assessments/recalculate`, префикс `/api` снимают прокси Vite (разработка) и `deploy/nginx.conf` (деплой). Пересчёт принимает либо C1b `{briefing, edits, answers}`, либо сам брифинг, который присылает страница: тогда правки параметров переводятся в признаки через `engine/numeric.py` (°C, бар, м, %), а ответ на вопрос ставит признак, только если это одно из допустимых значений.

```
GET  /health
```

Пока чужая функция не готова, Семён подставляет заглушку, которая возвращает пример из `examples/`.

## Что ещё должен подтвердить Никита

- Список 16 параметров (`ParameterId`).
- 12 признаков и их значения (`Phase`, `WaterLevel` и так далее) — это «словарь» для правил Ярика.
- Химию в примерах C5 и C7.
