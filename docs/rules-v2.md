# Правила прохода v2 (gates)

Статус: черновик 17.10. Химию проверяет Никита, перебор вопросов делает Гаджи.
Файлы: `rules/gates.yaml` (правила), `eval/golden_cases.yaml` (ожидания), `rules/check_gates.py` (проверка).
Заменяет: «правила прохода, версия 1» (Codex) и старый движок баллов `rules/rules.yaml`. **С 18.10 gates — единственный движок** (решение команды): `engine.score_methods` заполняет C5 из gates, старые правила лежат в `legacy/`.

## 1. Зачем v2

v1 была хорошей общей рамкой, но для нас не работала:

| Проблема v1 | Что в v2 |
|---|---|
| Ни одного конкретного условия, «заполнить по materials позже» | 61 правило с источником и страницей (S01, S02, S03, S04, AFS ref, Q&A 17.10) |
| Не проверяет, что именно просит клиент («утвердите», «докажите», «сразу точную конфигурацию») | Шаг Q4: предпосылки клиента получают вердикт `ok / not_supported / contradicted`. На этом построены H01, H03, H04, H05 и H06 |
| Пять наборов статусов; нет статуса AFS | Один набор (раздел 2), статус кейса как в AFS: provisional / insufficient_information / outside_scope |
| Порядок вопросов не определён | Перебор Гаджи встроен в формат: у каждого входа правила конечный словарь значений, на `unknown` правило ведёт себя явно |
| Не связана с каталогом, баллами и достаточностью | Кандидат = строка каталога K01–K10 (plan v4). Порядок: доказательство → риски → `cost` из Table 1 → баллы |
| Нельзя проверить | 14 golden-кейсов (H01–H06, D01–D08) и проверка `check_gates.py`, она падает при ослаблении любого ключевого правила |

## 2. Статусы

| Уровень | Значения | Кто ставит |
|---|---|---|
| Атрибут | `explicit / inferred / unknown / conflicting / expert`, у каждого цитата из текста клиента | экстракция (шаг A) |
| Кандидат (строка каталога) | `excluded` · `needs_info` · `candidate` + список рисков | движок |
| Доказательство кандидата | `application` (у AFS то же семейство применений) · `physics_only` · `none`. Уровня «validated» нет: измеренных данных нет | движок |
| Предпосылка клиента | `ok / not_supported / contradicted` | движок, правила Q4 |
| Кейс | `provisional / insufficient_information / outside_scope`. «final» не бывает | движок, O-STATUS |

Старшинство на строке: `exclude` > `exclude_config` > `needs_info` > `candidate`.
- `exclude_config` убирает только конфигурацию (например, кварцевую линию для MIR). Строка остаётся в `needs_info`: с другим волокном она возможна.
- `support_application` снимает `needs_info`, пришедший от правил сигнала Q2: материалы AFS покрывают вопрос о сигнале, но проверять всё равно нужно.
- `fit` (геометрия подходит, Q3) не повышает уровень доказательства.
- Строка с доказательством `none` не рекомендуется. Это замена старого `min_score`.

## 3. Порядок прохода

```
текст клиента
 → G0 извлечение: атрибуты из словаря (раздел 5), статус и цитата у каждого; просьбы клиента → client_claims
 → Q1 задача:   цель определена? несколько потоков или целей → отдельные кейсы; есть ли референс
 → Q2 сигнал:   метод × цель (флуорофор, хромофор, вода, водная матрица, флуоресцентный фон, OD ≠ viable)
 → Q3 интерфейс и конфигурация: строка × проба (Table 1 p.6, оптическая плотность, ATR-поверхность, обрастание)
                 + волокно × диапазон (S02 p.6), линия, рейтинги компонентов
 → Q4 предпосылки и доказательства: калибровка, комбинация, чувствительность, «утвердите», «сразу точную»,
                 научная статья ≠ готовность, клиника → outside_scope; таблица применений AFS
 → OUT: статус кейса → порядок и достаточность → комбинации → вопросы (перебор) → план эксперимента → ссылки
```

### Как правило читается движком

```yaml
- id: L-LINK-LENGTH-MIR
  step: Q3
  applies_to: row
  targets: [K01]
  guard: {distance: [outside_area, other_building]}   # рассматриваем, только если это ИЗВЕСТНО
  when: {link_confirmed: ["no"]}                       # все условия И
  effect: needs_info
  on_unknown: needs_info                               # что делать, если вход в `when` неизвестен
  because: "No link length for IR fibers is given in the materials; length and routing need AFS confirmation"
  source: ["AFS ref §3 'Do not invent' (fiber lengths)", "S01 p.10"]
  ask: {kind: method, attribute: link_confirmed, text: "..."}
  tests: [H04, D06]
```

- `guard` нужен, чтобы `needs_info` не загорался во всех кейсах. Пример: вопрос о длине линии задаём, только если анализатор далеко.
- Без `guard` правило с `on_unknown: needs_info` при неизвестном входе ставит `needs_info` всегда.
- **YAML:** `yes/no` в PyYAML по умолчанию превращаются в булевы значения. В `check_gates.py` есть `Loader`, который так не делает. `engine/gates.py` должен грузить файл тем же загрузчиком.

## 4. Решения, которые v2 фиксирует

1. **Исключение только по физике или обязательному условию с источником.** Это P-FIBER-RANGE, P-NO-FLUOROPHORE, S-UV-NO-CHROMOPHORE. Всё остальное (мутность, обрастание, температура, тип пробы не из Table 1) даёт риск или `needs_info`. Так решили 17.10 вечером: уходим от жёстких критериев.
2. **Никаких выдуманных чисел.**
   - `R-MIR-FIBER-LENGTH: block` в `rules.yaml` опирается на «MIR fibers are only a few meters». В материалах этого нет, а S01 p.10 говорит о «significant distance». Предлагаю удалить блок: в v2 это `L-LINK-LENGTH-MIR` с вопросом.
   - Рейтинги температуры, давления и материалов в источниках не даны. Поэтому `L-COMPONENT-RATINGS` — только риск и вопрос, без запрета.
3. **Достаточность (Слава, Q&A 17.10: «не нужен Bentley»).** Порядок внутри `candidate`:
   1. доказательство;
   2. меньше `risk_high`, потом меньше рисков;
   3. **колонки S01 Table 1** (блок `tie_break:`): следы (`target_class = trace`) → выше sensitivity (S01 p.16); сложная природная среда (молоко, нефть, ферментация, ткань, процессная среда; S01 p.7) → выше selectivity;
   4. ниже cost;
   5. ID.

   Баллы `rules.yaml` больше не участвуют: каждый ключ порядка — колонка таблицы AFS. Показываем не больше 3 строк.
4. **Комбинация — пост-шаг.** Только пары из `combinations:` (6 пар из материалов), только если оба метода в топ-3 и кейс `provisional`. Выигрыш — гипотеза, которую сравнивают с лучшим одиночным методом.
5. **Вопросы (идея Гаджи):**
   - Для каждого неизвестного входа любого правила перебираем все значения и прогоняем правила заново. Сила вопроса = доля значений, при которых меняется **выбранная строка (топ-1) или статус кейса**. Это совпадает с модулем Гаджи (`selected` + `decision_status`) и с AFS ref §3 («change the method or the setup»: строка = метод × зонд). Сверено на всех 14 кейсах.
   - Обязательные вопросы метода, даже если перебор их не выбрал: (а) кейс нельзя решить (`case_insufficient`); (б) неизвестен вход правила предпосылки уровня кейса; (в) что-то блокирует или ослабляет строку с доказательством `application`.
   - Вопросы плана (референс, критерии, диапазон, обрастание, температура, GMP) задаём всегда, отдельным блоком.
   - **Тексты вопросов** — блок `questions:` в `gates.yaml`: один параметр = один вопрос. Тип `kind`:
     - `method` — спросить клиента, ответ может поменять метод;
     - `plan` — спросить клиента для плана эксперимента;
     - `lab_check` — **не спрашивать клиента**: ответ даёт измерение образцов, это шаг 0 плана. Сейчас это `matrix_fluorescence` (AFS ref D01 «Check fluorescence background») и `chromophore`. Перебор их учитывает; в ответе это выглядит так: «выбор между NIR и Raman решит проверка флуоресценции на образцах»;
     - `never` — предпосылки клиента, их проверяем, а не спрашиваем.

     `check_gates.py` падает, если у параметра нет текста или если `ask.kind` правила не совпадает с `questions` (один источник правды).
   - **Отсечка шума** (`question_policy`):
     - вопрос из перебора слабее 0.3 не задаём;
     - не больше 5 вопросов о методе;
     - ответ, который только переводит кейс во «вне области» (например «клиника»), изменением решения не считается;
     - `existing_fiber` в переборе не участвует (`probe: false`): волокно выбирают потом вместе с AFS.
   - **Уже известное не спрашиваем повторно.** Исключение — правило с `ask_even_if_known`: например, при «мутность меняется» спрашиваем, в каком диапазоне. У обязательного вопроса текст берётся из сработавшего правила, он точнее.
   - **Вопросы плана как в эталонах AFS.** В D01/D02 AFS спрашивает: диапазон и критерии, референс **и его погрешность**, **физические и рецептурные вариации**, доступ и мойку. Отсюда T-REFERENCE-QUALITY (`reference_uncertainty`) и I-PHYSICAL-VARIATION (`physical_variation`; S01 p.17, AFS ref D01/D02). Golden D01/D02 проверяет, что все темы AFS заданы.
   - Каждая отсечка проверена поломкой, golden падает: топ-3 вместо топ-1 (H02), выключенный тай-брейк selectivity (D07), флуоресценция как вопрос клиенту (проверка источника правды), сломанное правило вариаций (D02).
6. **План эксперимента (O-EXPERIMENT)** — по эталонам D01/D02 и Q&A:
   - шаг 0: лабораторный скрининг нескольких образцов в AFS;
   - шаг 1: репрезентативные образцы или in-line пилот с независимым референсом;
   - сначала одиночные методы, потом комбинация из списка;
   - шаг 2: проверка на отложенных партиях против критериев клиента;
   - строка «после подтверждения сенсор можно сократить до нескольких длин волн» (S01 p.9, S02 p.15).

## 5. Словарь атрибутов (для экстракции и контракта v0.3)

Все поля необязательны. По умолчанию `unknown`. Привязка к сущностям модели 17.10:

| Сущность | Атрибуты |
|---|---|
| MeasurementTask | `target_defined`, `target_kind`, `target_class` (уровень концентрации, обычно unknown), `targets_count`, `quantitative`, `reference_method`, `reference_uncertainty`, `acceptance_criteria`, `concentration_range`, `intended_use` |
| Sample | `domain`, `sample_form`, `optical_density`, `matrix_aqueous`, `heterogeneous`, `fluorophore`, `chromophore`, `matrix_fluorescence`, `formulation_changed`, `streams`, `physical_variation` |
| ProcessContext | `temperature`, `fouling`, `distance`, `link_confirmed`, `existing_fiber`, `gmp` |
| CustomerRequest (client_claims) | `client_method`, `reuse_calibration`, `add_method_to_keep_calibration`, `justification`, `asks`, `cited_evidence`, `own_validation` |

Значения перечислены в `rules/gates.yaml → attributes`. Для C3 v0.3 это только добавления. Существующие 12 features v0.2 остаются, большинство отображается один к одному: `phase` → `sample_form`, `turbidity` → `optical_density`, `distance_class` → `distance`, `fouling_risk` → `fouling`, `fluorescence_risk` → `matrix_fluorescence`.

## 6. Ожидаемые результаты (golden)

Проверены эталонным вычислителем в `check_gates.py`: DEV 0 ошибок, TEST 0 ошибок. Ожидания по H — черновик Claude, заморожен (раздел 6a).

| Кейс | Статус | Топ (строки каталога) | Ключевые правила и вердикты |
|---|---|---|---|
| H01 | provisional | K03 NIR DR, K05 Raman, K04 | P-CALIBRATION и P-COMBO-NOT-FIX = not_supported (AFS говорит «can invalidate», а не «invalid»); вопросы плана: референс, критерии, GMP |
| H02 | provisional (2 кейса) | whey: K02 NIR transmission; concentrate: K03 NIR DR | T-SPLIT-STREAMS; прозрачный и непрозрачный поток дают разные геометрии |
| H03 | provisional (2 цели) | glucose: K05 Raman; biomass: K06 UV-ATR | P-NO-FLUOROPHORE исключает K10; P-SENSITIVITY-NOT-SELECTIVITY = contradicted; OD ≠ viable |
| H04 | provisional | K03, K04 (NIR) | P-FIBER-RANGE: K01 по кварцу исключён (contradicted); L-REMOTE-SILICA (S02 p.7: кварц 100–300 м) — плюс NIR/Raman издалека; P-APPROVE-WITHOUT-DATA = not_supported; вопрос о линии IR |
| H05 | insufficient_information | — | P-TARGET-UNDEFINED; P-EXACT-CONFIG-NOW = not_supported; первый вопрос — что считается браком |
| H06 | outside_scope | — | P-EVIDENCE-SCOPE = contradicted (S03: 14 in vitro, proof of concept); P-CLINICAL-SCOPE |
| D01 | provisional | K03, K05, K04; комбинация NIR + Raman | APP-PHARMA-BLEND, S-RAMAN-FLUOR-BG, L-GMP |
| D02 | provisional | K03 для fat и protein | I-OPAQUE-*, APP-DAIRY, I-PHYSICAL-VARIATION (S01 p.17), T-REFERENCE-QUALITY |
| D03 | provisional | K02, K03 | I-OD-VARIES: сравнить геометрии, вопрос о диапазоне мутности |
| D04 | provisional | K05 для glucose и lactate; K02 для glucose ждёт ответа об оптической плотности | S-AQUEOUS-RAMAN, S-AQUEOUS-IR/NIR, APP-BIO-METABOLITES, APP-BIO-NIR-GLUCOSE |
| D05 | provisional | biomass: K08, K06 | цели разделены; OD ≠ viable |
| D06 | provisional | K03, K04; K01 ждёт подтверждения линии | APP-PETRO-WATER, L-LINK-LENGTH-MIR |
| D07 | provisional | **K01 MIR ATR**, K03 | APP-EXTRUSION (S02 p.14); K01 первый по selectivity Table 1, как лид AFS (AFS ref §5); рейтинги и обрастание → вопросы плана |
| D08 | provisional | K10, K01; комбинация MIR + fluorescence | APP-TISSUE-LAB (S04), I-ATR-SURFACE, одна точка |

Проверка ловит ошибки. Шесть искусственных поломок дали FAIL:
- ослабили P-FIBER-RANGE;
- ослабили P-NO-FLUOROPHORE;
- в P-CLINICAL-SCOPE подставили неверное условие;
- из APP-PHARMA убрали Raman;
- в правило вписали значение не из словаря;
- испортили диапазон волокна.

**Сверка источников.** Отдельный агент сверил каждую ссылку с PDF и docx. Исправлено: P-CALIBRATION и P-COMBO-NOT-FIX смягчены до not_supported; у L-LINK-LENGTH-MIR теперь источник S02 p.7 (кварц 100–300 м) и S02 p.9 (IR-кабели 2 м); NIR в биопроцессе поддерживается только для глюкозы (S01 p.16); диапазон флуоресценции помечен как допущение; расширения Table 1 в каталоге (melt, soft_solid) помечены как наше сопоставление; из P-CLINICAL-SCOPE убрано «regulatory». Открытый вопрос: PIR 3–17 мкм (AFS ref §5) или 3–16 мкм (S02 p.8)? Сверить с рисунком S02 p.6. Ответы Q&A 17.10 по файлам не проверить: источник — заметки команды.

Без тестов остались четыре правила: S-FLUOR-INDICATOR, S-UV-NO-CHROMOPHORE, S-TRACE-NIR, P-BUSINESS-SOURCE. Ни один D/H-кейс их не затрагивает. Никите: добавить по кейсу или подтвердить, что они нужны.

## 6a. Разработка и тест: D и H (честность по H)

По `AGENTS.md`: D01–D08 — набор для разработки, H01–H06 — тестовый, **под H не подгоняем**.

**Как это устроено в проверке (`rules/check_gates.py`):**
- отчёт отдельно: `DEV D01–D08` и `TEST H01–H06`;
- **ожидания по H заморожены** 18.10 (`eval/h_frozen.sha256`). Если кто-то меняет H в `golden_cases.yaml`, проверка падает. Менять H можно только решением команды и никогда ради того, чтобы прошло правило;
- предупреждение «правило проверено только на H»: такое правило ни один кейс разработки не затрагивает, значит, оно могло быть подогнано.

**Что честно надо знать:**
1. **Ожидания по H — черновик Claude**, а не ответы AFS: официальных ответов на H нет. Они написаны по тексту H и материалам AFS.
2. **Часть механики движка появилась после того, как я смотрел на вывод по H.** Правила общие, номеров кейсов в них нет, но мотивация была такой:
   - обязательные вопросы — в H05 не задавался «что считается браком», в H04 — вопрос о линии IR;
   - `guard` и `link_confirmed` в L-LINK-LENGTH-MIR — H04;
   - фильтр «без доказательства не рекомендуем» — в H04 в топ попадал UV-ATR для воды в нефти;
   - эффект `fit` для геометрии — в H02 (сыворотка) первым был UV-transmission;
   - L-REMOTE-SILICA проверен только на H04.
3. **16 правил проверены только на H.** Это ловушки: калибровка, волокно, флуорофор, «утвердите», «сразу точную», статья как доказательство, клиника, два потока. В D01–D08 таких ловушек нет.

**Что делаем дальше:**
- Никита заполняет `eval/h_independent_nikita.yaml` **независимо**, не глядя на наш вывод. Потом сравниваем. Расхождения — честные ошибки, под H их не правим.
- Добавить свои кейсы разработки с ловушками (`X01…`), собранные из материалов AFS, но не из текста H. Так советует сам AFS docx §4: «Test the hard cases on purpose: missing information, an enquiry outside the sources, a premise that the sources contradict». Тогда правила-ловушки будут проверены не только на H.
- ~~Прогнать экстракцию и сравнить атрибуты с golden~~ — сделано 18.10 (симуляция, см. `eval/extract_report.md`).

**18.10, честность по H на шаге A:**
- В промпте экстракции ночной версии были примеры, почти дословно взятые из текстов H (H03, H04, H05, H06): «our only justification is sensitivity», «a silica fiber cable from a visible or NIR setup», «we suspect contamination but cannot name it», «during live surgery». Я заменил их определениями и примерами из D. Теперь H — более чистый тест для шага A.
- Определения значений `asks` уточнены после того, как в H06 видели ошибку на базовом прогоне. Поэтому совпадение `asks` по H06 — не чистое доказательство.
- Синтетические кейсы S01–S04 (`eval/synthetic_cases.yaml`) я написал сам, без материалов AFS: новые домены, немецкий текст, другие предпосылки. По S01 и S04 после первого прогона поправлены две строки промпта (гранулы → `powder`; йогурт → `opaque`). После этого S тоже не полностью независимый набор.

## 7. Что дальше

| Что | Кто | Когда |
|---|---|---|
| Проверить химию и страницы в `gates.yaml` (особенно S-AQUEOUS-*, S-RAMAN-COMPOSITION, I-SAMPLE-TYPE, диапазоны `methods:`, `fiber_full_overlap`) | Никита | вс |
| Подключить оверлей gates в бэкенд: the backend gates overlay (applied) (C8 `attributes` и `assessment`, пересчёт на recalculate) | Семён | вс |
| `engine/completeness.py`: перебор поверх `Evaluator.run` (`completeness_score_fn`) | Гаджи | до фриза |
| ~~Старый движок `rules.yaml`~~ — выведен 18.10, лежит в `legacy/`; удалить папку одним коммитом после демо | команда | после демо |
| `must_not_claim` из golden проверять в `/eval` на тексте шага B | Ниджат | вс |

Запуск проверки: `python rules/check_gates.py`. Трасса одного кейса: `python rules/check_gates.py --case H04`.
После изменения `gates.yaml`: `python rules/rules_table.py` (раздел 8), `python contracts/regen_assessment_example.py`,
`python -m engine.paths` (пути решения), `python rules/mutate_gates.py`.

## 7a. Изменения 18.10 (после ревью кода и критики эксперта)

| Изменение | Почему |
|---|---|
| `I-OPAQUE-TRANSMISSION`: известная «opaque» → `needs_info`, неизвестная → `risk` (было: risk_high / needs_info) | Неизвестное значение было строже известного плохого: при «opaque» трансмиссионный зонд попадал в топ-3. Теперь монотонно: clear → K02 первый, unknown → K02 с вопросом, opaque → K02 не выбирается |
| `APP-PHARMA-BLEND` только для `target_kind = api` | S01 p.14–15 — это содержание API в смеси, не влажность. Иначе Raman получал «application» для воды в порошке |
| `fiber_full_overlap: {default: 0.9, mir: 0.6}` | Ни одно MIR-волокно не покрывает 90 % от 2,5–25 µm; поликристаллическое (62 %) и полый волновод (69 %) — обычные MIR-линии, они не должны давать риск «частичное покрытие». Инженерный выбор, подтвердить с AFS |
| Предпосылка «утвердить концепт» не проходит и для кандидата без поддержки (evidence none) | Иначе Raman без единого правила «за» считался утверждаемым |
| `selected` пустой, если статус не provisional | P-TARGET-UNDEFINED говорит «метод пока нельзя обосновать», а строки показывались |
| Нерешаемый кейс всегда получает до 3 вопросов (базовые факты + `target_class`, `quantitative`) | Был тупик: insufficient без вопросов |
| `ignored_inputs` в C5.assessment (optional) | Эксперт видит, какие значения движок отбросил |
| Устойчивость: не-dict на входе, плохие вероятности Jev, плоский формат для `completeness_score_fn` | Падения на неверном вводе |
| `completeness_score_fn` принимает оба словаря статусов: known/assumed (C3) и stated/inferred (спека §6); незнакомый статус возвращается в `ignored`, а не отбрасывается молча | Со статусом `stated` все атрибуты отбрасывались, и любой кейс становился «недостаточно данных» |
| Проверки: 31 тест движка, 19/19 мутаций, `check_gates` проверяет `sample_types` каталога и `fiber_full_overlap` | Пять поломок движка раньше не ловились |

## 8. Все правила

#### Q1 · Задача

| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |
|---|---|---|---|---|---|---|
| `P-TARGET-UNDEFINED` | case | target_defined ∈ [no] | case_insufficient | needs_info | AFS ref §3 'Insufficient information can be the right answer'; S01 p.3 (samples of incompletely known composition: test several approaches to select the method) | H05 |
| `T-TARGET-PARTIAL` | case | target_defined ∈ [partial] | clarify | ignore | AFS ref D05 ('target variables still need definition'); AFS ref §3 (clarification questions first) | D05 |
| `T-SPLIT-TARGETS` | case | targets_count ∈ [2plus] | split_case | ignore | AFS ref D05 'target variables still need definition'; S01 p.16 | H03, D02, D04, D05 |
| `T-SPLIT-STREAMS` | case | streams ∈ [2plus] | split_case | ignore | S01 p.17–18 | H02 |
| `T-NO-REFERENCE` | case | quantitative ∈ [yes]; reference_method ∈ [none] | cap_provisional | plan_question | AFS ref §3 (feasibility plan: independent reference measurements) | H03, H05, D05, D08 |
| `T-REFERENCE-QUALITY` | case | [guard] reference_method ∈ [available]; reference_uncertainty ∈ [given] | plan_question | plan_question | AFS ref D01 (clarification: 'Which assay, uncertainty and sampling time provide the reference concentrations?'); AFS ref D02 | D01, D02, D03, D04, D06 |
| `T-PLAN-MINIMUM` | case | acceptance_criteria ∈ [unknown] | plan_question | plan_question | AFS ref D01 'Decision basis'; AFS Q&A 17.10 (lab screening: range, resolution, concentration level) | D01, D02, D03, D04, D06, D07 |

#### Q2 · Сигнал

| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |
|---|---|---|---|---|---|---|
| `P-NO-FLUOROPHORE` | fluorescence | fluorophore ∈ [not_identified] | exclude | needs_info | S01 p.5; AFS ref §5 (fluorescence row) | H03 |
| `S-FLUOR-INDICATOR` | fluorescence | fluorophore ∈ [indicator_justified] | risk | ignore | AFS ref §5 ('a justified indicator'); S01 p.16 (NADH, tryptophan, riboflavin as fluorescence targets) | нет (no case names an indicator; D05 needs target definition first) |
| `S-UV-NO-CHROMOPHORE` | uv_vis | chromophore ∈ [no]; target_kind ∈ [api, fat, protein, glucose, lactate, metabolite_other, water, contaminant, tissue_type, other] | exclude | ignore | S01 p.5; AFS ref §5 (UV-Vis row) | нет (no D/H case states a non-absorbing target; Nikita: add a case or confirm) |
| `S-UV-OVERLAP` | uv_vis | target_kind ∈ [api, fat, protein, glucose, lactate, metabolite_other] | risk | ignore | S01 p.5 | D04 |
| `S-WATER` | nir, mir | target_kind ∈ [water] | support_physics | ignore | S01 p.10; S01 p.16 (strong water absorption in IR); S02 p.13 | D06, H04 |
| `S-VIBRATIONAL-MAJOR` | nir, mir | target_kind ∈ [api, fat, protein, glucose, lactate, water] | support_physics | ignore | S01 p.4–5; S01 p.9–10 | D01, D02, D04, D06, H01, H04 |
| `S-RAMAN-COMPOSITION` | raman | target_kind ∈ [api, fat, protein, glucose, lactate] | support_physics | ignore | S01 p.11–12; S01 p.14–15; S01 p.16 | D01, D02, D04, H01 |
| `S-TRACE-NIR` | nir | target_class ∈ [trace] | risk_high | ignore | S01 p.16 | нет (no case states a trace level; enumeration still asks the concentration level when it flips NIR) |
| `S-AQUEOUS-IR` | mir | matrix_aqueous ∈ [yes]; target_kind ∈ [glucose, lactate, metabolite_other, protein] | risk | ignore | S01 p.16 | D04, H03 |
| `S-AQUEOUS-NIR` | nir | matrix_aqueous ∈ [yes]; target_kind ∈ [lactate, metabolite_other] | risk | ignore | S01 p.16 | D04 |
| `S-AQUEOUS-RAMAN` | raman | matrix_aqueous ∈ [yes]; target_kind ∈ [glucose, lactate, metabolite_other] | support_physics | ignore | S01 p.16 | D04, H03 |
| `S-RAMAN-FLUOR-BG` | raman | matrix_fluorescence ∈ [high] | risk_high | risk | S01 p.11; AFS ref D01 ('Check fluorescence background and signal quality') | D01, H01 |
| `S-OD-NOT-VIABLE` | uv_vis | target_kind ∈ [biomass] | risk | ignore | S01 p.16; AFS ref §5 (UV-Vis row) | H03, D05 |

#### Q3 · Интерфейс и конфигурация

| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |
|---|---|---|---|---|---|---|
| `I-SAMPLE-TYPE` | K01, K02, K03, K04, K05, K06, K07, K08, K09, K10 | sample_form_not_in_row ∈ [True] | needs_info | needs_info | S01 Table 1 (p.6) | D01, D07, D08 |
| `I-GAS-OUT-OF-SCOPE` | case | sample_form ∈ [gas] | case_outside_scope | ignore | S01 Table 1 (p.6); AFS ref §3 (decision status: outside the supported scope) | нет (no D/H case is a gas; covered by engine/test_gates.py) |
| `I-OPAQUE-TRANSMISSION` | K02, K08 | optical_density ∈ [opaque] | needs_info | risk | S01 p.16; S01 p.18 | D02, H02 |
| `I-OPAQUE-REFLECTION` | K03 | optical_density ∈ [opaque, turbid] | fit | ignore | S01 p.17 | D02, H02 |
| `I-CLEAR-TRANSMISSION` | K02, K08 | optical_density ∈ [clear] | fit | ignore | S01 p.16; S01 p.18 | H02 |
| `I-CLEAR-REFLECTION` | K03 | optical_density ∈ [clear]; sample_form ∈ [liquid] | risk | ignore | S01 p.18 | H02 |
| `I-OD-VARIES` | K02, K03, K06, K08 | optical_density ∈ [varies] | risk | ignore | S01 p.18 (transflection can cover low- and high-fat products); S01 p.16 | D03, D05 |
| `I-UV-HIGH-OD` | K06 | optical_density ∈ [opaque, turbid, varies] | fit | ignore | S01 p.16 | D05 |
| `I-ATR-SURFACE` | K01, K06 | heterogeneous ∈ [yes] | risk | ignore | S01 p.13; S01 Table 1 (p.6) | D08 |
| `I-FOULING-CONTACT` | K01, K02, K03, K05, K06, K08, K10 | fouling ∈ [high] | risk | plan_question | AFS ref §5 (MIR: contact, fouling); AFS ref D07, D02 | D07, D02 |
| `I-PHYSICAL-VARIATION` | K02, K03, K04 | physical_variation ∈ [yes] | risk | plan_question | S01 p.17; AFS ref D02 (risks); AFS ref D01 (risks: physical variation of the powder) | D02, D01 |
| `P-FIBER-RANGE` | K01, K02, K03, K04, K05, K06, K07, K08, K09, K10 | fiber_overlap_none ∈ [True] | exclude_config | ignore | S02 p.6; S01 p.9 | H04 |
| `L-FIBER-PARTIAL` | K01, K02, K03, K04, K05, K06, K07, K08, K09, K10 | fiber_overlap_partial ∈ [True] | risk | ignore | S02 p.6; AFS ref §3 'Spectral range' | H04 |
| `L-LINK-LENGTH-MIR` | K01 | [guard] distance ∈ [outside_area, other_building]; link_confirmed ∈ [no] | needs_info | needs_info | S02 p.7 (100–300 m silica cables); S02 p.9 (PIR, HWG 2 m); AFS ref §3 'Do not invent' (fiber lengths) | H04, D06 |
| `L-REMOTE-SILICA` | K02, K03, K05 | [guard] distance ∈ [outside_area, other_building]; existing_fiber ∈ [silica_vis_nir, silica_uv_vis, none] | fit | ignore | S02 p.7; S01 p.5; S01 p.15 | H04 |
| `L-COMPONENT-RATINGS` | K01, K02, K03, K04, K05, K06, K07, K08, K09, K10 | temperature ∈ [elevated, high] | risk | plan_question | AFS ref §3 'Do not invent' (component ratings); AFS Q&A 17.10 (temperature is critical) | D07 |
| `L-GMP` | case | domain ∈ [pharma_solid] | plan_question | ignore | AFS Q&A 17.10 | D01, H01 |

#### Q4 · Предпосылки и доказательства

| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |
|---|---|---|---|---|---|---|
| `P-CALIBRATION` | case | [guard] reuse_calibration ∈ [yes]; formulation_changed ∈ [yes] | premise_not_supported | needs_info | AFS ref D01 (recommendation and risks) | H01 |
| `P-COMBO-NOT-FIX` | case | add_method_to_keep_calibration ∈ [yes] | premise_not_supported | ignore | AFS ref D01 (NIR + Raman); AFS ref §5 (combinations); S01 p.14–15 | H01 |
| `P-SENSITIVITY-NOT-SELECTIVITY` | case | justification ∈ [sensitivity_only] | premise_contradicted | ignore | S01 Table 1 (p.6); S01 p.5 | H03 |
| `P-APPROVE-WITHOUT-DATA` | case | [guard] asks ∈ [approve_concept]; any_needs_info_on_requested ∈ [True] | premise_not_supported | ignore | AFS ref §3 'An honest provisional plan is more useful than a final configuration built on missing facts' | H04 |
| `P-EXACT-CONFIG-NOW` | case | [guard] asks ∈ [exact_config_now]; target_defined ∈ [no, partial] | premise_not_supported | ignore | AFS ref §3 'Insufficient information can be the right answer' | H05 |
| `P-EVIDENCE-SCOPE` | case | [guard] cited_evidence ∈ [research_paper]; intended_use ∈ [clinical_in_vivo, production]; own_validation ∈ [no] | premise_contradicted | needs_info | S03 p.1; S03 p.3; S03 p.14; AFS ref §3 'Common mistakes' | H06 |
| `P-CLINICAL-SCOPE` | case | intended_use ∈ [clinical_in_vivo] | case_outside_scope | ignore | S03 p.3; S03 p.14; AFS ref §3 (decision status: outside the supported scope) | H06 |
| `P-ASSET-NOT-EVIDENCE` | case | client_method ∈ [mir, nir, raman, uv_vis, fluorescence] | risk | ignore | AFS ref §3 'Common mistakes' (missing facts filled in as if given) | H01, H03, H04 |
| `P-BUSINESS-SOURCE` | case | cited_evidence ∈ [business_material] | risk | ignore | AFS ref §4 (S05, S06) | нет (no D/H case cites S05/S06; checked by the citation validator) |
| `APP-PHARMA-BLEND` | K03, K05 | domain ∈ [pharma_solid]; sample_form ∈ [powder]; target_kind ∈ [api] | support_application | ignore | S01 p.14–15 | D01, H01 |
| `APP-DAIRY` | K02, K03 | domain ∈ [dairy] | support_application | ignore | S01 p.17–18 | D02, D03, H02 |
| `APP-BIO-METABOLITES` | K05 | domain ∈ [bioprocess]; target_kind ∈ [glucose, lactate, metabolite_other] | support_application | ignore | S01 p.16 | D04, H03 |
| `APP-BIO-NIR-GLUCOSE` | K02 | domain ∈ [bioprocess]; target_kind ∈ [glucose] | support_application | ignore | S01 p.16 | D04, H03 |
| `APP-BIO-BIOMASS` | K08, K06 | domain ∈ [bioprocess]; target_kind ∈ [biomass] | support_application | ignore | S01 p.16 | D05, H03 |
| `APP-PETRO-WATER` | K01 | domain ∈ [petroleum]; target_kind ∈ [water] | support_application | ignore | S02 p.13 | D06, H04 |
| `APP-EXTRUSION` | K01, K03 | domain ∈ [polymer_melt] | support_application | ignore | S02 p.14 | D07 |
| `APP-TISSUE-LAB` | K01, K10 | domain ∈ [tissue]; intended_use ∈ [lab_research] | support_application | ignore | S04 p.1; S04 p.3–4 | D08 |

#### OUT · Выход

| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |
|---|---|---|---|---|---|---|
| `O-STATUS` | case | outside_scope if any case_outside_scope fired; insufficient_information if case_insufficient fired or every non-excluded candidate is needs_info; otherwise provisional. Never 'final'. | — | — | AFS ref §3 (decision status) | H01, H02, H03, H04, H05, H06 |
| `O-ORDER` | row | Tie-break by S01 Table 1 columns as in `tie_break:` (trace → sensitivity, complex natural media → selectivity, then cost). Only candidates with evidence (application or physics_only) are recommended; rows no rule supports are not shown. Order: evidence application > analogy > physics_only; fewer risk_high, then fewer risks; lower Table 1 cost (simplest sufficient); catalog row id last. Show at most 3 (team choice). | — | — | AFS Q&A 17.10 ('you don't need a Bentley'); AFS ref D01 'Choose the simplest configuration that meets them'; S01 Table 1 (p.6) cost | D01, D02, H02 |
| `O-COMBINATION` | combination | Propose a combination only if listed in the materials and both single methods are in the top-3 of the case; its gain is a hypothesis tested against the best single method; sampling location and acquisition timing of both methods must be aligned (same spot for heterogeneous samples) | — | — | S01 p.7–9; S01 p.8 (synchronisation, same spot); AFS Q&A 17.10; AFS ref §5 (combinations) | D01, D08 |
| `O-QUESTIONS` | case | Method questions: for each unknown input of a fired or skipped rule, try every value; strength = share of values that change top row, an exclusion or the case status. Strongest first, 5–10 questions in total (Q&A 17.10); plan questions (reference, criteria, range) always, as a separate block. | — | — | AFS ref §3 'Clarification questions: first the questions whose answers could change the method or the setup'; AFS Q&A 17.10 (5–10 questions) | H02, H04, H05 |
| `O-EXPERIMENT` | case | Step 0 lab screening of a few samples (range, resolution, concentration level); step 1 representative samples or in-line pilot with independent reference (sampling + lab assay; Q&A examples: chromatography, MS); single methods first, then a listed combination; step 2 held-out validation against client criteria; note: after confirmation the sensor may be reduced to a few wavelengths. | — | — | AFS ref D01, D02 (feasibility experiment); AFS Q&A 17.10; S01 p.9; S02 p.15 | D01, D02, H01, H05, H06 |
| `O-SPECTRAL-RANGE` | row | A nominal method range is not the range of an instrument, fiber or probe; for Raman state excitation (nm) and shift (cm-1) separately; µm = 10000 / cm-1 | — | — | AFS ref §3 'Spectral range'; AFS ref §5; S01 p.11 | D01, D02 |
| `O-CITE` | case | Every reason carries its source; an AFS page is enough if it directly supports the claim at the same scope (lab/process/clinic); external sources need link and quote | — | — | AFS ref §4 'How to cite'; AFS Q&A 17.10 | H06, D08 |

Всего правил: 61. Таблица сгенерирована `python rules/rules_table.py`.
