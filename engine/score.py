"""C4 -> C5 on the gates engine (rules/gates.yaml). The old points engine (rules/rules.yaml) is retired
(team decision 18.10) and kept only in legacy/ for reference.

    score_methods(ScoreInput) -> Scoring        same contract as before, filled from engine.gates

How C5 is filled (deterministic, every entry traceable to a gates rule and its AFS source):
- `assessment`: the full gates result (row statuses, premises, questions, lab checks, trace).
- `ranked`: the selected catalog rows, one entry per method in gates order (best row first; a second
  selected row of the same method is named as the alternative probe). Empty unless the case is provisional.
  The ORDER is the gates order (evidence -> high risks -> risks -> S01 Table 1 tie-break), not the points.
- `scores` / `score_total`: display points derived from the gates effects on that row, so the expert sees
  why: support_application +2, support_physics +1, risk_high -1, configuration change -1, risk -0.5.
- `confidence`: high = AFS application and no high risk; medium = application with high risk, or physics
  without high risk; low = otherwise.
- `rejected`: every other method with the reason from the deciding rule (excluded -> blocker).

Input: C4 `attributes` (v0.3). Only without them (a v0.2 caller) the attributes are derived from the
12 features (`features_to_attributes`, a coarse mapping); the two are never mixed. With attributes, an expert's
change goes through the attributes (the UI writes C8.attributes before /assessments/recalculate).
"""
if __package__:
    from .gates import Evaluator, assess
    from .gates_loader import load_gates
else:  # pragma: no cover
    from gates import Evaluator, assess
    from gates_loader import load_gates

from contracts.models import CriterionScore, RejectedMethod, ScoredMethod, ScoreInput, Scoring

METHODS = ["uv_vis", "nir", "mir", "raman", "fluorescence", "scattering"]
ROW_MODE = {"K01": "atr", "K02": "transflection", "K03": "diffuse_reflectance", "K04": "diffuse_reflectance",
            "K05": "raman_backscatter", "K06": "atr", "K07": "diffuse_reflectance", "K08": "transmission",
            "K09": "transmission", "K10": "fluorescence_emission"}
POINTS = {"support_application": (2.0, "evidence: AFS application"),
          "support_physics": (1.0, "evidence: physical principle"),
          "risk_high": (-1.0, "high risk"),
          "exclude_config": (-1.0, "configuration change required"),
          "risk": (-0.5, "risk")}
FACT = ("known", "assumed")


def features_to_attributes(features) -> dict:
    """Coarse v0.2 fallback: the 12 features -> gates attributes (known/assumed features only)."""
    f = {k: v["value"] for k, v in features.model_dump().items() if v["status"] in FACT and v["value"] != "unknown"}
    a = {}
    a["sample_form"] = {"liquid": "liquid", "slurry": "liquid", "emulsion": "liquid", "solid_powder": "powder",
                        "solid_surface": "solid", "gas": "gas"}.get(f.get("phase"))
    a["matrix_aqueous"] = {"high": "yes", "medium": "yes", "low": "no", "none": "no"}.get(f.get("water_level"))
    a["target_kind"] = {"moisture": "water", "trace_contaminant": "contaminant"}.get(f.get("analyte_type"))
    a["target_class"] = {"trace_ppm": "trace", "high_percent": "major_component"}.get(f.get("concentration_level"))
    if f.get("analyte_type") == "trace_contaminant":
        a["target_class"] = "trace"
    a["temperature"] = {"ambient": "ambient", "elevated": "elevated", "high": "high"}.get(f.get("temperature_class"))
    a["fouling"] = {"low": "low", "high": "high"}.get(f.get("fouling_risk"))
    a["distance"] = {"short": "at_process", "long": "outside_area"}.get(f.get("distance_class"))
    a["matrix_fluorescence"] = {"low": "low", "high": "high"}.get(f.get("fluorescence_risk"))
    a["optical_density"] = {"clear": "clear", "turbid": "turbid", "opaque": "opaque"}.get(f.get("turbidity"))
    return {k: v for k, v in a.items() if v}


def _attributes(inp: ScoreInput) -> dict:
    """C4 attributes if present (they passed the quote and vocabulary checks of step A), else the coarse
    feature fallback. Never mixed: feature values are often silent assumptions the attribute check rejected."""
    if getattr(inp, "attributes", None):
        from llm.vocab import engine_attrs   # known/assumed values of the C3 attributes
        return engine_attrs(inp.attributes)
    return features_to_attributes(inp.features)


def _range(g: dict, m: str) -> str:
    meta = g["methods"].get(m)
    if not meta:
        return "not in the catalog"
    lo, hi = meta["range_nm"]
    text = f"{lo / 1000:g}–{hi / 1000:g} µm" if m == "mir" else f"{lo}–{hi} nm"
    return f"{text} (nominal; {meta['source'].split(',')[0]})"


def _fibers(g: dict, ev: Evaluator, m: str, existing: str | None) -> str:
    from .gates import overlap
    if m not in g["methods"]:
        return "—"
    need = ev.full_overlap.get(m, ev.full_overlap.get("default", 1.0))
    fit = [f for f, x in g["fibers"].items() if overlap(g["methods"][m]["range_nm"], x["range_nm"]) >= need]
    text = ", ".join(fit) if fit else "no fiber in the table covers the full range"
    if existing and existing not in ("none", "unknown"):
        text += f" (customer's fiber: {existing}{'' if existing in fit else ', does not cover the range'})"
    return text + "; length and routing to be confirmed by AFS"


def score_methods(inp: ScoreInput, g: dict | None = None, probs: dict | None = None) -> Scoring:
    g = g or load_gates()
    attrs = _attributes(inp)
    # probs only weight question strength. They do not change which row the gates select.
    a = assess(attrs, probs=probs, g=g)
    ev = Evaluator(g)
    because = {r["id"]: r.get("because", "") for r in g["rules"]}
    rows = {r.row: r for r in a.rows}
    effects: dict[str, list] = {}
    for t in a.trace:
        if t.target and (t.rule_id, t.effect) not in [(x[0], x[1]) for x in effects.get(t.target, [])]:
            effects.setdefault(t.target, []).append((t.rule_id, t.effect))

    ranked, seen = [], {}
    for rid in a.selected:
        m = g["catalog"][rid]["method"]
        if m in seen:
            seen[m].append(rid)
            continue
        seen[m] = [rid]
    for i, (m, rids) in enumerate(seen.items(), 1):
        best = rids[0]
        scores = []
        for rule_id, eff in effects.get(best, []):
            if eff in POINTS:
                pts, crit = POINTS[eff]
                scores.append(CriterionScore(criterion=crit, score=pts, rule_id=rule_id, note=because[rule_id]))
        r = rows[best]
        high = sum(1 for x in r.risks if x.endswith((":risk_high", ":exclude_config")))
        conf = ("high" if r.evidence == "application" and not high else
                "medium" if r.evidence == "application" or (r.evidence == "physics_only" and not high) else "low")
        probe = f"{g['catalog'][best]['technique']} ({best})"
        if len(rids) > 1:
            probe += "; alternative: " + ", ".join(f"{g['catalog'][x]['technique']} ({x})" for x in rids[1:])
        ranked.append(ScoredMethod(
            rank=i, method=m, mode=ROW_MODE[best], spectral_range=_range(g, m),
            fiber=_fibers(g, ev, m, attrs.get("existing_fiber")), probe=probe,
            score_total=round(sum(s.score for s in scores), 2), scores=scores, confidence=conf))

    rejected = []
    for m in METHODS:
        if m in seen:
            continue
        mrows = [r for r in a.rows if r.method == m]
        if not mrows:
            rejected.append(RejectedMethod(method=m, rule_id=None, blocker=True,
                                           reason="Not an in-line row of the AFS method catalog (S01 Table 1, p.6)"))
            continue
        if all(r.status == "excluded" for r in mrows):
            rid = next(x for r in mrows for x, e in effects.get(r.row, []) if e == "exclude")
            rejected.append(RejectedMethod(method=m, rule_id=rid, blocker=True, reason=because[rid]))
            continue
        if a.decision_status != "provisional":
            rejected.append(RejectedMethod(
                method=m, rule_id=None, blocker=False,
                reason=f"Case status {a.decision_status}: no method can be recommended yet"))
            continue
        order = {"candidate": 0, "needs_info": 1, "excluded": 2}
        evid = {"application": 0, "analogy": 1, "physics_only": 2, "none": 3}
        r = min(mrows, key=lambda r: (order[r.status], evid[r.evidence], r.row))
        if r.status == "needs_info":
            rid = next((x for x, e in effects.get(r.row, []) if e == "needs_info"), None)
            reason = f"Needs information ({r.row}): {because.get(rid, '')}" if rid else f"Needs information ({r.row})"
        elif r.evidence == "none":
            rid, reason = None, "No AFS application and no physical support for this target in the rules"
        else:
            rid = None
            reason = f"Ranked below the selected rows ({r.row}: evidence {r.evidence}, risks {len(r.risks)})"
        rejected.append(RejectedMethod(method=m, rule_id=rid, blocker=False, reason=reason))

    scoring = Scoring(rules_version=f"rules-{g.get('version')}", ranked=ranked, rejected=rejected, assessment=a)
    return with_engine_b(scoring, inp)


# ------------------------------------------------------------------------------------------------- method B
# ENGINE=a  : gates only (old behaviour)
# ENGINE=ab : gates decide `ranked`, method B result attached as `assessment_b`
# ENGINE=b  : method B decides `ranked`/`rejected`; the gates result stays in `assessment` for comparison (default, team decision 18.10 20:30)
B_METHOD = {"NIR": "nir", "MIR": "mir", "Raman": "raman", "UV_VIS": "uv_vis", "Fluorescence": "fluorescence"}
B_MODE = {"atr": "atr", "transflection": "transflection", "transmission": "transmission",
          "diffuse_reflection": "diffuse_reflectance", "backscatter": "raman_backscatter",
          "scattering_90": "raman_backscatter", "emission": "transmission"}


def engine_mode() -> str:
    import os
    return os.environ.get("ENGINE", "b").lower()


def with_engine_b(scoring: Scoring, inp: ScoreInput) -> Scoring:
    mode = engine_mode()
    if mode == "a" or not (getattr(inp, "attributes", None) or getattr(inp, "facts_b", None)):
        return scoring
    from .b import assess_b
    if getattr(inp, "facts_b", None):          # step A extracted the B fields directly
        from llm.facts_b import to_engine
        b = assess_b(to_engine(inp.facts_b))
        b["facts_origin"] = "facts_b"   # from step A, or edited by the expert on recalculate
    else:                                       # bridge from the 34 step-A attributes
        from .b.from_a import facts_from_attributes
        b = assess_b(facts_from_attributes(inp.attributes))
        b["facts_origin"] = "bridge_from_attributes"
    upd = {"assessment_b": trim_b(b)}
    if mode == "b":
        upd.update(ranked_from_b(b))
        upd["rules_version"] = f"rules-{b['ruleset_version']}"
    return scoring.model_copy(update=upd)


def facts_b_from_assessment(b: dict | None) -> list | None:
    """The B facts the engine used (also when bridged from the attributes), as editable FactB records,
    so the expert can always correct a B fact and recalculate."""
    if not b or not b.get("facts"):
        return None
    from contracts.models import FactB
    ok = ("reported", "inferred", "unknown", "conflicting", "confirmed_experiment", "confirmed_expert")
    out = []
    for k, r in b["facts"].items():
        v = r.get("value")
        out.append(FactB(key=k, value=", ".join(v) if isinstance(v, list) else v, unit=r.get("unit_or_category"),
                         status=r.get("status") if r.get("status") in ok else "unknown",
                         quote=r.get("quote"), source=r.get("source")))
    return out


TRACE_TOP = 5


def trim_b(b: dict, top: int = TRACE_TOP) -> dict:
    """API payload only (team decision 18.10): the engine computes every candidate; the briefing keeps the full
    factor trace for the top 5 candidates per Case and drops NOT_APPLICABLE factors. The rest keep their
    scores, intervals and unknown inputs. Decision, scores and order are unchanged."""
    for case in b["cases"]:
        for i, c in enumerate(case["ranking"]):
            c["factor_contributions"] = ([f for f in c["factor_contributions"] if f["outcome"] != "NOT_APPLICABLE"]
                                         if i < top else [])
            c["trace_trimmed"] = i >= top
    return b


def ranked_from_b(b: dict) -> dict:
    """First Case drives `ranked` (best configuration per method, spec 06 §5); other methods -> rejected."""
    case = b["cases"][0]
    ranked, rejected = [], []
    if case["decision_status"] == "needs_target":
        for m in METHODS:
            rejected.append(RejectedMethod(method=m, rule_id="R_Q1_01", blocker=False,
                                           reason="Target not defined yet: screening directions only (spec 06 §6)"))
        return {"ranked": [], "rejected": rejected}
    by_id = {c["candidate_id"]: c for c in case["ranking"]}
    for i, m in enumerate(case["methods"][:3], 1):
        c = by_id[m["best_candidate_id"]]
        scores = [CriterionScore(criterion=f"{q} {c['question_results'][q]['display_score']}/9",
                                 score=float(c["question_results"][q]["display_score"]), rule_id=None,
                                 note=f"interval {c['question_results'][q]['score_interval']}, "
                                      f"{c['question_results'][q]['status']}")
                  for q in ("Q1", "Q1b", "Q2", "Q3")]
        for f in c["factor_contributions"]:
            if f["outcome"] in ("MATCH", "MISMATCH") and f["selected_in_exclusive_group"] and f["effect"]:
                scores.append(CriterionScore(criterion=f"{f['stage']} {f['group']}: {f['outcome']}",
                                             score=float(f["effect"]), rule_id=f["factor_id"], note=f["note"] or ""))
        ranked.append(ScoredMethod(rank=i, method=B_METHOD[m["method_id"]],
                                   mode=B_MODE.get(c["configuration"]["optical_geometry"], "transmission"),
                                   spectral_range="see method card", fiber=c["configuration"]["fiber_link"],
                                   probe=f"{c['interface_name']} ({c['interface_id']})",
                                   score_total=float(c["suitability"]), scores=scores, confidence=m["confidence"]))
    shown = {r.method for r in ranked}
    excluded = {e["candidate_id"].split("|")[0]: e for e in case["excluded"] if e["level"] == "method"}
    for m in METHODS:
        if m in shown:
            continue
        bm = next((k for k, v in B_METHOD.items() if v == m), None)
        if bm is None:
            rejected.append(RejectedMethod(method=m, rule_id=None, blocker=True,
                                           reason="Not one of the five methods of the method B catalog (S01 Table 1)"))
        elif bm in excluded:
            x = excluded[bm]["excluded_by"][0]
            rejected.append(RejectedMethod(method=m, rule_id=x["rule_id"], blocker=True, reason=x["reason"]))
        else:
            row = next((r for r in case["methods"] if r["method_id"] == bm), None)
            reason = (f"Ranked below the top 3: suitability {row['suitability']}/36, interval "
                      f"{row['suitability_interval']}" if row else "No allowed configuration")
            rejected.append(RejectedMethod(method=m, rule_id=None, blocker=False, reason=reason))
    return {"ranked": ranked, "rejected": rejected}
