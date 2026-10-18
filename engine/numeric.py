"""Turn a number the expert typed ("80 °C", "3 bar", "15 m", "2 %") into a feature class.

The boundaries are the same as in llm/prompts/extract_system.md (draft, to be checked
by Nikita and against the AFS materials). Change them here and in the prompt together.
For a range like "1-5 %" the largest number decides, because the probe and fiber must
survive the worst case.
"""
import re

TEMPERATURE_C = [(0, "cryogenic"), (40, "ambient"), (150, "elevated")]   # above the last → "high"
PRESSURE_BAR = [(0.9, "vacuum"), (1.1, "ambient"), (20, "elevated")]    # above → "high"
DISTANCE_M = [(2, "short"), (20, "medium")]                              # above → "long"
CONCENTRATION_PCT = [(0.1, "trace_ppm"), (10, "low_percent")]            # above → "high_percent"
WATER_PCT = [(10, "low"), (50, "medium")]                                # above → "high"

_NUM = re.compile(r"[-−]?\d+(?:[.,]\d+)?")


def _numbers(text: str) -> list[float]:
    # "1-5 %" must give 1 and 5, not 1 and -5: a minus only counts at the start or after a space
    out = []
    for m in _NUM.finditer(text):
        raw = m.group().replace("−", "-").replace(",", ".")
        if raw.startswith("-") and m.start() > 0 and not text[m.start() - 1].isspace():
            raw = raw[1:]
        out.append(float(raw))
    return out


def _bucket(value: float, bounds: list[tuple[float, str]], top: str) -> str:
    for limit, name in bounds:
        if value < limit:
            return name
    return top


def temperature_class(text: str) -> str | None:
    nums = _numbers(text)
    if not nums:
        return None
    t = text.lower()
    vals = nums
    if "°f" in t or re.search(r"\d\s*f\b", t):
        vals = [(v - 32) * 5 / 9 for v in nums]
    elif re.search(r"\d\s*k\b", t) and "°c" not in t:
        vals = [v - 273.15 for v in nums]
    if min(vals) < 0 and max(vals) <= 0:
        return "cryogenic"
    return _bucket(max(vals), TEMPERATURE_C, "high")


def pressure_class(text: str) -> str | None:
    nums = _numbers(text)
    if not nums:
        return None
    t = text.lower()
    factor = 1.0
    if "mbar" in t:
        factor = 0.001
    elif "kpa" in t:
        factor = 0.01
    elif "mpa" in t:
        factor = 10.0
    elif "psi" in t:
        factor = 0.0689476
    elif "vakuum" in t or "vacuum" in t:
        return "vacuum"
    return _bucket(max(nums) * factor, PRESSURE_BAR, "high")


def distance_class(text: str) -> str | None:
    nums = _numbers(text)
    if not nums:
        return None
    t = text.lower()
    factor = 1.0
    if "km" in t:
        factor = 1000.0
    elif "cm" in t:
        factor = 0.01
    elif "mm" in t:
        factor = 0.001
    elif "ft" in t or "feet" in t:
        factor = 0.3048
    return _bucket(max(nums) * factor, DISTANCE_M, "long")


def concentration_level(text: str) -> str | None:
    nums = _numbers(text)
    if not nums:
        return None
    t = text.lower()
    if "ppb" in t:
        return "trace_ppm"
    if "ppm" in t:
        pct = max(nums) / 10_000
    elif "%" in t:
        pct = max(nums)
    else:
        return None  # g/L, mol/L etc. cannot be turned into % without the matrix
    return _bucket(pct, CONCENTRATION_PCT, "high_percent")


def water_level(text: str) -> str | None:
    nums = _numbers(text)
    if not nums or "%" not in text:
        return None
    v = max(nums)
    if v == 0:
        return "none"
    return _bucket(v, WATER_PCT, "high")


# parameter id → (feature key, converter)
PARAM_TO_FEATURE = {
    "temperature": ("temperature_class", temperature_class),
    "pressure": ("pressure_class", pressure_class),
    "distance_to_instrument": ("distance_class", distance_class),
    "concentration_range": ("concentration_level", concentration_level),
    "water_content": ("water_level", water_level),
}


def classify(parameter_id: str, text: str | None) -> tuple[str, str] | None:
    """("temperature", "80 °C") → ("temperature_class", "elevated"); None if it cannot be decided."""
    if not text or parameter_id not in PARAM_TO_FEATURE:
        return None
    feature, fn = PARAM_TO_FEATURE[parameter_id]
    value = fn(text)
    return (feature, value) if value else None
