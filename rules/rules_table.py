"""Regenerate section 8 ("Все правила") of docs/rules-v2.md from rules/gates.yaml.

    python rules/rules_table.py        # after any change to rules/gates.yaml
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from gates_loader import load_yaml  # noqa: E402

STEPS = [("Q1", "Задача"), ("Q2", "Сигнал"), ("Q3", "Интерфейс и конфигурация"),
         ("Q4", "Предпосылки и доказательства"), ("OUT", "Выход")]
HEADER = "## 8. Все правила"


def _cond(r: dict) -> str:
    parts = [f"[guard] {k} ∈ [{', '.join(map(str, v))}]" for k, v in (r.get("guard") or {}).items()]
    parts += [f"{k} ∈ [{', '.join(map(str, v))}]" for k, v in (r.get("when") or {}).items()]
    return "; ".join(parts) or "—"


def _for(r: dict) -> str:
    if r["applies_to"] in ("case", "combination"):
        return r["applies_to"]
    return ", ".join(r.get("targets") or []) or r["applies_to"]


def table(g: dict) -> str:
    out = [HEADER, ""]
    for step, title in STEPS:
        rules = [r for r in g["rules"] if r["step"] == step]
        if not rules:
            continue
        out += [f"#### {step} · {title}", "",
                "| ID | Для | Условие | Эффект | Если неизвестно | Источник | Тесты |", "|---|---|---|---|---|---|---|"]
        for r in rules:
            if step == "OUT":
                cond, eff, unk = r.get("because", ""), "—", "—"
            else:
                cond, eff, unk = _cond(r), r["effect"], r["on_unknown"]
            src = "; ".join(r.get("source") or [])
            tests = ", ".join(r.get("tests") or []) or f"нет ({r.get('untested', 'untested')})"
            out.append(f"| `{r['id']}` | {_for(r)} | {cond} | {eff} | {unk} | {src} | {tests} |".replace("\n", " "))
        out.append("")
    out.append(f"Всего правил: {len(g['rules'])}. Таблица сгенерирована `python rules/rules_table.py`.")
    return "\n".join(out) + "\n"


def main() -> None:
    g = load_yaml(ROOT / "rules" / "gates.yaml")
    doc = ROOT / "docs" / "rules-v2.md"
    text = doc.read_text(encoding="utf-8")
    head = text.split(HEADER)[0]
    doc.write_text(head + table(g), encoding="utf-8")
    print(f"docs/rules-v2.md section 8: {len(g['rules'])} rules")


if __name__ == "__main__":
    main()
