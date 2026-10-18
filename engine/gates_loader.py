"""Load rules/gates.yaml (rules, attribute vocabulary, questions, catalog).

YAML 1.1 turns yes/no/on/off into booleans; our vocabularies use yes/no as strings, so only
true/false are booleans here. Every reader of gates.yaml must use this loader.
"""
import re
from functools import lru_cache
from pathlib import Path

import yaml

GATES_PATH = Path(__file__).resolve().parents[1] / "rules" / "gates.yaml"


class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:bool"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf"))


def load_yaml(path: Path) -> dict:
    return yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_Loader)


@lru_cache(maxsize=4)
def _cached(path: str, mtime: float) -> dict:
    return load_yaml(Path(path))


def load_gates(path: Path = GATES_PATH) -> dict:
    """Cached by file path and modification time."""
    p = Path(path)
    return _cached(str(p), p.stat().st_mtime)
