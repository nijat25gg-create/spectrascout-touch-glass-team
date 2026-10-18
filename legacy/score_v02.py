"""LEGACY (retired 18.10, see legacy/README.md). Deterministic scoring of the 6 AFS methods from the 12 features.

Same input -> same output. Every point is traceable to a rule id in rules/rules.yaml.
"""
from collections import defaultdict
from pathlib import Path

import yaml

from contracts.models import CriterionScore, RejectedMethod, ScoredMethod, ScoreInput, Scoring

RULES_PATH = Path(__file__).resolve().parent / "rules_v02.yaml"   # legacy copy of rules/rules.yaml
METHODS = ["uv_vis", "nir", "mir", "raman", "fluorescence", "scattering"]
_cache = {}


def load_rules(path: Path = RULES_PATH) -> dict:
    key = (str(path), path.stat().st_mtime)
    if key not in _cache:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        _validate(data)
        _cache.clear()
        _cache[key] = data
    return _cache[key]


def _validate(data: dict) -> None:
    ids = set()
    for r in data["rules"]:
        assert r["id"] not in ids, f"duplicate rule id {r['id']}"
        ids.add(r["id"])
        for m, eff in r["effects"].items():
            assert m in METHODS, f"{r['id']}: unknown method {m}"
            assert eff == "block" or isinstance(eff, (int, float)), f"{r['id']}: bad effect {eff}"
    for m in METHODS:
        assert m in data["methods"], f"method {m} missing in methods:"


def score_methods(inp: ScoreInput, rules: dict | None = None) -> Scoring:
    rules = rules or load_rules()
    feats = inp.features.model_dump()
    points = {m: defaultdict(float) for m in METHODS}          # method -> criterion -> score
    hits = {m: defaultdict(list) for m in METHODS}             # method -> criterion -> [(rule_id, note, eff)]
    blocks = {}                                                # method -> (rule_id, note)
    unknown_relevant = {m: 0 for m in METHODS}

    for r in rules["rules"]:
        f = feats[r["feature"]]
        if f["value"] == "unknown" or f["status"] == "unknown":
            for m in r["effects"]:
                unknown_relevant[m] += 1
            continue
        if f["value"] not in r["values"]:
            continue
        for m, eff in r["effects"].items():
            if eff == "block":
                blocks.setdefault(m, (r["id"], r["note"]))
            else:
                points[m][r["criterion"]] += eff
                hits[m][r["criterion"]].append((r["id"], r["note"], eff))

    totals = {m: round(sum(points[m].values()), 2) for m in METHODS}
    min_score = rules.get("min_score", 3)
    candidates = sorted((m for m in METHODS if m not in blocks and totals[m] >= min_score),
                        key=lambda m: (-totals[m], METHODS.index(m)))
    ranked_methods = candidates[:3]

    phase = feats["phase"]["value"]
    ranked = []
    for i, m in enumerate(ranked_methods, 1):
        cfg = rules["methods"][m]
        scores = []
        for crit, val in sorted(points[m].items(), key=lambda kv: -abs(kv[1])):
            h = hits[m][crit]
            main = max(h, key=lambda x: abs(x[2]))
            scores.append(CriterionScore(criterion=crit, score=round(val, 2), rule_id=main[0],
                                         note="; ".join(n for _, n, _ in h)))
        unk = unknown_relevant[m]
        conf = "high" if unk <= 2 else "medium" if unk <= 5 else "low"
        ranked.append(ScoredMethod(
            rank=i, method=m, mode=cfg["modes"].get(phase, cfg["modes"]["default"]),
            spectral_range=cfg["spectral_range"], fiber=cfg["fiber"], probe=cfg["probe"],
            score_total=totals[m], scores=scores, confidence=conf))

    rejected = []
    for m in METHODS:
        if m in ranked_methods:
            continue
        if m in blocks:
            rid, note = blocks[m]
            rejected.append(RejectedMethod(method=m, reason=note, rule_id=rid, blocker=True))
        else:
            neg = [(rid, n, e) for c in hits[m].values() for (rid, n, e) in c if e < 0]
            if neg:
                rid, note, _ = min(neg, key=lambda x: x[2])
                reason = f"Low total score ({totals[m]}). Main issue: {note}"
            else:
                rid, reason = None, f"Low total score ({totals[m]}), no rule speaks for this method"
            rejected.append(RejectedMethod(method=m, reason=reason, rule_id=rid, blocker=False))

    return Scoring(rules_version=rules["version"], ranked=ranked, rejected=rejected)
