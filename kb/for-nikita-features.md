# Для Никиты: параметры и признаки, что проверить

Как работает система, коротко:
1. Клиент пишет письмо обычным текстом.
2. LLM вытаскивает из него **16 параметров**, как их понял бы эксперт, с цитатой из письма.
3. Из параметров получаются **12 признаков**: упрощённые значения из короткого списка, например фаза «жидкость» или «порошок».
4. Движок по правилам ставит баллы каждому методу по этим 12 признакам. Правила и баллы задаёшь ты (с Яриком).

Пример: «Хотим мерить остаточную влагу в фарм-порошке в сушилке, 1–5 %».
Параметры: что меряем = влага, матрица = фарм-порошок, диапазон = 1–5 %...
Признаки: phase = solid_powder, analyte_type = moisture, concentration_level = low_percent...
Правило: phase = solid_powder → NIR +3, MIR −2 и т.д.

---

## 16 параметров (что LLM ищет в письме)

| id | По-русски | Вопрос к тебе |
|---|---|---|
| measurand | что меряем | |
| measurand_type | тип вещества | |
| matrix | в чём (среда) | |
| phase | агрегатное состояние | |
| water_content | сколько воды в среде | |
| concentration_range | диапазон концентраций | |
| required_accuracy | нужная точность | |
| temperature | температура в точке измерения | |
| pressure | давление | |
| aggressiveness_fouling | агрессивность, налипание | |
| installation_point | где ставим зонд (реактор, труба, сушилка) | |
| distance_to_instrument | расстояние до прибора, длина волокна | |
| measurement_frequency | как часто нужен результат | |
| reference_method | чем меряют сейчас (KF, HPLC...) | |
| samples_available | есть ли образцы для калибровки | |
| regulatory | требования (GMP, ATEX...) | |

**Проверить:** чего не хватает, что лишнее? Что из этого чаще всего забывают клиенты (из интервью)?

---

## 12 признаков (что читает движок)

| Признак | Значения сейчас | Вопрос к тебе |
|---|---|---|
| phase | liquid, solid_powder, slurry, emulsion, gas, solid_surface | хватает? |
| water_level | none, low, medium, high | где границы, в % ? |
| analyte_type | moisture, organic_compound, colored_compound, polymorph, particles_cells, trace_contaminant, other | какие типы важны для выбора метода? |
| concentration_level | trace_ppm, low_percent, high_percent | границы? |
| accuracy_need | screening, quantitative, high_precision | |
| temperature_class | cryogenic, ambient, elevated, high | границы в °C? |
| pressure_class | vacuum, ambient, elevated, high | границы в бар? |
| fouling_risk | low, medium, high | |
| distance_class | short <2 м, medium 2–20 м, long >20 м | верно для ИК-волокон? |
| fluorescence_risk | low, high | как понять по описанию? |
| turbidity | clear, turbid, opaque | |
| hazardous_area | yes, no | |

**Проверить:** каких признаков не хватает, чтобы различить методы? Какие значения неправильные?

Можно отвечать прямо в этом файле или голосовыми, я перенесу.

---

## Что уже есть, что нет

- Есть: черновые карточки 6 методов в `kb/card-*.md` (что метод видит, где не работает). Их тоже глянуть, когда будет время.
- Нет: поиска статей и парсера. Это потом, отдельной кнопкой. Сейчас только сетап для ресерча, его скину отдельно.
