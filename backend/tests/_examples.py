"""Shared contract examples (contracts/examples) as plain dicts for the tests."""
import json
from pathlib import Path

_DIR = Path(__file__).resolve().parents[2] / "contracts" / "examples"


def example(name: str) -> dict:
    return json.loads((_DIR / f"{name}.example.json").read_text(encoding="utf-8"))


TEXT = "Wir wollen die Restfeuchte eines Pulvers im Wirbelschichttrockner inline messen."
