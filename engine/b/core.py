"""Method B engine (spec spectroscopy-rules 1.2-draft), deterministic.

    assess_b(facts) -> dict   (the Assessment of spec 02 §5, one entry per Case)

Flow (spec 07 §1): facts -> Cases -> per method Q1, Q1b -> per documented interface Q2 -> per configuration
concept Q3 -> Q4 evidence + confidence -> ranking -> sensitivity of unknowns -> questions -> first experiment.
Every factor is a rule of rules/b/rules_b.yaml with MATCH / MISMATCH / UNKNOWN / NOT_APPLICABLE, its effect,
the facts it read and its source. The LLM never runs here (spec 02 §1).
"""
from __future__ import annotations

import functools
import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATCH, MISMATCH, UNKNOWN, NA = "MATCH", "MISMATCH", "UNKNOWN", "NOT_APPLICABLE"
UNKNOWN_VALUES = (None, "", "unknown", "conflicting", [])
CONF_RANK = {"high": 2, "medium": 1, "low": 0}
LIQUID_FORMS = {"solution", "suspension", "emulsion"}
SOLID_FORMS = {"powder", "bulk_solid", "film", "pill"}


@functools.lru_cache(maxsize=1)
def load_b():
    cat = yaml.safe_load((ROOT / "rules/b/catalog_b.yaml").read_text(encoding="utf-8"))
    reg = yaml.safe_load((ROOT / "rules/b/rules_b.yaml").read_text(encoding="utf-8"))
    return cat, reg


# ----------------------------------------------------------------------------------------- facts
# Fact record: value + unit/category + source + status, so a missing value never
# becomes an invented fact. Status vocabulary and the aliases accepted from older inputs:
STATUSES = ("reported", "inferred", "unknown", "confirmed_experiment", "confirmed_expert", "conflicting")
STATUS_ALIAS = {"explicit": "reported", "known": "reported", "stated": "reported", "assumed": "inferred",
                "derived": "inferred", "not_stated": "unknown"}
COVERED = ("reported", "confirmed_experiment", "confirmed_expert")   # inferred never counts (spec 06 §4)


def normalize_facts(raw: dict) -> tuple[dict, dict, dict]:
    """{key: value | {value, status, unit, source, quote}} -> (values, statuses, meta).
    A plain value is 'reported' (said by the client). Unknown / conflicting stay out of the values (E09)."""
    vals, stat, meta = {}, {}, {}
    for k, v in (raw or {}).items():
        if isinstance(v, dict) and "value" in v:
            value, status = v.get("value"), v.get("status", "reported")
            m = {"unit": v.get("unit"), "source": v.get("source"), "quote": v.get("quote")}
        else:
            value, status, m = v, "reported", {"unit": None, "source": None, "quote": None}
        status = STATUS_ALIAS.get(status, status)
        if status not in STATUSES:
            raise ValueError(f"data_error: unknown fact status {status!r} for {k}")   # spec 02 §7
        meta[k] = m
        if status in ("unknown", "conflicting") or value in UNKNOWN_VALUES:
            stat[k] = "conflicting" if status == "conflicting" else "unknown"
            continue
        vals[k], stat[k] = value, status
    return vals, stat, meta


def fact_records(cat: dict, vals: dict, stat: dict, meta: dict) -> dict:
    """Every catalog fact, filled or not: value, unit_or_category, source, status."""
    out = {}
    for k in sorted(set(cat["facts"]) | set(vals) | set(stat)):
        m = meta.get(k, {})
        status = stat.get(k, "unknown")
        src = m.get("source") or ("client_text" if status == "reported" and m.get("quote") else
                                  "client_text" if status == "reported" else
                                  "product_scope" if k == "ProcessContext.deployment_preference" and status == "inferred"
                                  else "derived" if status == "inferred" else None)
        out[k] = {"value": vals.get(k), "unit_or_category": m.get("unit") or ("category" if k in cat["facts"] else None),
                  "source": src, "quote": m.get("quote"), "status": status}
    return out


def derive(vals: dict) -> dict:
    """Derived execution facts (spec 01 §8, 09: target_definition_status is computed, not read)."""
    v = dict(vals)
    # Product scope is in-line process spectroscopy (AFS brief): without a stated preference the proposed
    # process configuration is in-line; marked 'inferred' (not reported) so it never counts as covered.
    v.setdefault("ProcessContext.deployment_preference", "in_line")
    if "MeasurementTask.target_definition" not in v:
        t = v.get("MeasurementTask.target")
        if t and t != ["contaminant"] and t != "contaminant":
            v["MeasurementTask.target_definition"] = "defined"
    return v


# ----------------------------------------------------------------------------------------- conditions
class Ctx:
    def __init__(self, cat, facts, method, iface=None, config=None, case_target=None):
        self.cat, self.facts, self.method, self.iface, self.config = cat, facts, method, iface, config
        self.case_target = case_target
        self.used, self.missing = set(), set()

    def fact(self, key):
        self.used.add(key)
        if key == "MeasurementTask.target":
            val = self.case_target
        else:
            val = self.facts.get(key)
        if val in UNKNOWN_VALUES:
            self.missing.add(key)
            return None
        return val


def ev(cond, x: Ctx):
    """Three-valued: True / False / None (unknown)."""
    if cond is None:
        return True
    if "all" in cond:
        r = [ev(c, x) for c in cond["all"]]
        return False if False in r else (None if None in r else True)
    if "any" in cond:
        r = [ev(c, x) for c in cond["any"]]
        return True if True in r else (None if None in r else False)
    if "not" in cond:
        r = ev(cond["not"], x)
        return None if r is None else not r
    if "method" in cond:
        return x.method in cond["method"]
    if "i" in cond:
        return (x.iface or {}).get(cond["i"]) in cond["in"]
    if "c" in cond:
        val = (x.config or {}).get(cond["c"])
        if val is None and (x.config or {}).get("level") == "combination":
            return None   # a combination field not documented is unknown, not false
        return val in cond["in"]
    if "f" in cond:
        val = x.fact(cond["f"])
        if val is None:
            return None
        vs = val if isinstance(val, list) else [val]
        return any(v in cond["in"] for v in vs)
    if "op" in cond:
        return PREDICATES[cond["op"]](x)
    raise ValueError(f"unknown condition {cond}")  # data_error, spec 02 §7


# ----------------------------------------------------------------------------------------- predicates
def _ev_match(x, need_matrix=True):
    m = x.facts.get("Sample.matrix")
    best = 0
    for e in x.cat["evidence"]:
        if e["method"] != x.method or x.case_target not in e["targets"]:
            continue
        best = max(best, e["level"] if (not need_matrix or e["matrix"] == m) else 1)
    return best


def p_target_relation(x):
    x.fact("MeasurementTask.target")
    return True if _ev_match(x, need_matrix=False) else None


def p_existing_method(x):
    v = x.fact("ProcessContext.assets.method")
    return None if v is None else v == x.method


def p_absorber(x):
    return True if x.fact("Sample.relevant_components.absorber") == "known" else None


def p_selectivity(x):
    """R_Q1_04: True only if an evidence row for this method, target and matrix cites the page that shows the
    separation (selectivity_source). A documented application alone is the target relation (R_Q1_01 group),
    not a second +2 for the same source. No measured spectra in the materials -> never False."""
    t, m = x.fact("MeasurementTask.target"), x.fact("Sample.matrix")
    if t is None or m is None:
        return None
    hit = any(e["method"] == x.method and t in e["targets"] and e["matrix"] == m and e.get("selectivity_source")
              for e in x.cat["evidence"])
    return True if hit else None


def p_edge(x):
    """R_Q2_01: a documented edge (S01 Table 1) is MATCH. A missing edge is UNKNOWN (research candidate),
    never MISMATCH: only a positive proof of incompatibility may count against the pair (spec 05 §2, T07)."""
    return True if x.iface["method"] == x.method else None


def p_forms(x):
    form, phase = x.fact("Sample.physical_form"), x.fact("Sample.phase")
    forms = set(x.iface.get("forms") or [])
    if form and form in forms:
        return True
    if forms == {"radiating"} and (form or phase):
        return False   # lens for an externally radiating sample: a non-radiating sample gives no signal
    kind = "liquid" if (form in LIQUID_FORMS or (form is None and phase == "liquid")) else \
           "solid" if (form in SOLID_FORMS or (form is None and phase == "solid")) else None
    if forms and kind == "solid" and forms <= LIQUID_FORMS:
        return False   # constructive conflict: solid sample in a liquid-only cell/probe
    if forms and kind == "liquid" and forms <= SOLID_FORMS:
        return False   # liquid sample in a solid-only interface (sphere, surface at a distance)
    return None        # CL10: not listed = unknown, not false


def p_optical_path(x):
    o = x.fact("Sample.optical_properties.opacity")
    return {"clear": True, "opaque": False}.get(o)


def p_dairy_geometry(x):
    o = x.fact("Sample.optical_properties.opacity")
    if o not in ("clear", "opaque"):
        return None
    transmissive = x.iface["geometry"] in ("transmission", "transflection")
    return (o == "clear") == transmissive


def p_spatial(x):
    s = x.fact("MeasurementTask.spatial_scope")
    if s == "local":
        return True
    if s is None:
        return None
    h = x.fact("Sample.heterogeneity")
    return {"homogeneous": True, "heterogeneous": False}.get(h)


def p_hot(x):
    m = x.fact("Sample.matrix")
    for e in x.cat["evidence"]:
        if e["method"] == x.method and e["scope"] == "in_line" and e["matrix"] == m == "polymer":
            return True
    return None


def p_deployment(x):
    pref = x.fact("ProcessContext.deployment_preference")
    if pref is None:
        return None
    return True if pref in ("lab", "at_line") else x.iface["deployment"] == "in_line"


def _fiber_ok(x):
    fam = x.fact("ProcessContext.assets.fiber")
    if fam is None:
        return None
    return fam in x.cat["methods"][x.method]["fiber_families"]


def p_fiber_covers(x):
    if x.config["link"] == "new":
        return True    # a documented family for the method's window is chosen (S02 p6)
    return _fiber_ok(x)


def p_fiber_not_covering(x):
    ok = _fiber_ok(x)
    return None if ok is None else not ok


def p_reuse_plan(x):
    if x.config["link"] == "reuse":
        return True    # the plan is to reuse; the spectral fit is R_Q3C_08 (no double count)
    must = x.fact("ProcessContext.assets.must_reuse")
    return None if must is None else must == "no"


def _temps(x):
    """(required [lo, hi], rating [lo, hi]) for this interface, or None where either is not given."""
    req = x.fact("ProcessContext.temperature_c")
    ratings = x.facts.get("Configuration.operating_envelope.temperature_c") or {}
    rating = ratings.get(x.config["configuration_id"].split("|")[1]) if isinstance(ratings, dict) else None
    if not (isinstance(req, (list, tuple)) and len(req) == 2 and isinstance(rating, (list, tuple)) and len(rating) == 2):
        return None
    return req, rating


def p_temp_rating_given(x):
    """R_Q3P_01 applies only where a data-sheet rating of this interface exists. Without one the concept row
    R_Q3C_01 stays (NOT_APPLICABLE here, so no question per missing data sheet). Unknown process range = unknown."""
    ratings = x.facts.get("Configuration.operating_envelope.temperature_c") or {}
    if not (isinstance(ratings, dict) and x.config["configuration_id"].split("|")[1] in ratings):
        return False
    return True if _temps(x) else None


def p_temp_within(x):
    t = _temps(x)
    if t is None:
        return None
    (lo, hi), (rlo, rhi) = t
    return rlo <= lo and hi <= rhi    # both ends (T08): max above the rating and min below it both conflict


def p_temp_outside(x):
    r = p_temp_within(x)
    return None if r is None else not r


PREDICATES = {
    "always": lambda x: True, "never_known": lambda x: None, "band_overlap_known": lambda x: None,
    "documented_target_relation": p_target_relation, "is_existing_model_method": p_existing_method,
    "absorber_known_or_unknown": p_absorber, "selectivity_documented": p_selectivity, "documented_edge": p_edge, "forms_compatible": p_forms,
    "optical_path_usable": p_optical_path, "dairy_geometry": p_dairy_geometry,
    "spatially_representative": p_spatial, "hot_process_documented": p_hot,
    "deployment_matches": p_deployment, "fiber_family_covers_method": p_fiber_covers,
    "fiber_family_not_covering": p_fiber_not_covering, "reuse_plan_ok": p_reuse_plan,
    "nonradiating_sample_on_emission_interface": lambda x: (
        x.iface.get("forms") == ["radiating"] and (x.fact("Sample.physical_form") or x.fact("Sample.phase")) is not None
        and x.facts.get("Sample.physical_form") != "radiating"),
    "temperature_rating_given": p_temp_rating_given, "temperature_within_rating": p_temp_within,
    "temperature_outside_rating": p_temp_outside,
    "asset_fiber_stated": lambda x: x.facts.get("ProcessContext.assets.fiber") not in UNKNOWN_VALUES + ("none",),
}


# ----------------------------------------------------------------------------------------- factors
def eval_rule(r: dict, x: Ctx) -> dict:
    x.used, x.missing = set(), set()
    w = ev(r.get("when"), x)
    m, mm = r.get("match", 0), r.get("mismatch", 0)
    out = {"factor_id": r["id"], "stage": r["stage"], "group": r["group"], "source": r.get("source"),
           "note": r.get("note"), "exclusive": r.get("exclusive"), "specificity": r.get("specificity", 1),
           "family": r.get("family"), "component": r.get("component", False),
           "diagnostic": r.get("diagnostic", False), "catalog_unknown": r.get("catalog_unknown", False),
           "applicability_known": w is True, "exclusion": None}
    if w is False:
        out.update(outcome=NA, effect=0, possible=[0])
    elif r.get("catalog_unknown") and w is True:
        out.update(outcome=UNKNOWN, effect=0, possible=[0], code="NO_SCOPED_PERFORMANCE_PROFILE")
    elif r.get("diagnostic"):
        out.update(outcome=UNKNOWN if w is not False else NA, effect=0, possible=[0])
    elif w is None:
        poss = sorted({0, m} | ({mm} if r.get("criterion") else set()))
        out.update(outcome=UNKNOWN, effect=0, possible=poss)
    else:
        c = ev(r.get("criterion"), x) if r.get("criterion") else True
        if c is True:
            out.update(outcome=MATCH, effect=m, possible=[m])
        elif c is False:
            out.update(outcome=MISMATCH, effect=mm, possible=[mm])
        else:
            out.update(outcome=UNKNOWN, effect=0, possible=sorted({m, mm}))
    out["input_fact_refs"] = sorted(x.used)
    out["unknown_inputs"] = sorted(x.missing)
    h = r.get("hard")
    if h and w is True:   # a hard predicate only acts where the rule provably applies (spec 02 §3)
        x.used, x.missing = set(), set()
        if ev(h["when"], x) is True:
            out["exclusion"] = {"scope": h["scope"], "reason": h["reason"], "rule_id": r["id"],
                                "fact_refs": sorted(x.used), "proof_ref": r.get("source")}
    return out


def select_exclusive(factors: list) -> list:
    """Spec 02 §4: one most specific applicable row per exclusive group; ties -> conservative, then id."""
    groups = {}
    for f in factors:
        f["selected_in_exclusive_group"] = True
        if f["exclusive"] and f["outcome"] != NA:
            groups.setdefault((f["stage"], f["exclusive"]), []).append(f)
    for fs in groups.values():
        fs.sort(key=lambda f: (not f["applicability_known"], -f["specificity"], min(f["possible"]), f["factor_id"]))
        for f in fs[1:]:
            f["selected_in_exclusive_group"] = False
    return factors


def component_replaces_concept(factors: list) -> list:
    known_fams = {f["family"] for f in factors if f["component"] and f["outcome"] in (MATCH, MISMATCH)}
    for f in factors:
        if not f["component"] and f["family"] in known_fams:
            f["selected_in_exclusive_group"] = False
            f["replaced_by_component"] = True
    return factors


def bucket(raw, thr):
    return sum(1 for t in thr if t <= raw)


def aggregate(stage: str, factors: list, reg: dict) -> dict:
    cap, thr = reg["group_cap"], reg["bucket_thresholds"]
    clamp = lambda v: max(-cap, min(cap, v))
    totals, lo_t, hi_t, crit = {}, {}, {}, set()
    for g in reg["groups"][stage]:
        fs = [f for f in factors if f["group"] == g and f["selected_in_exclusive_group"] and not f["diagnostic"]]
        known = sum(f["effect"] for f in fs if f["outcome"] in (MATCH, MISMATCH))
        lo = known + sum(min(f["possible"]) for f in fs if f["outcome"] == UNKNOWN)
        hi = known + sum(max(f["possible"]) for f in fs if f["outcome"] == UNKNOWN)
        totals[g], lo_t[g], hi_t[g] = clamp(known), clamp(lo), clamp(hi)
        crit |= {k for f in fs if f["outcome"] == UNKNOWN for k in f["unknown_inputs"]}
    raw, rmin, rmax = sum(totals.values()), sum(lo_t.values()), sum(hi_t.values())
    has_unknown = any(f["outcome"] == UNKNOWN and not f["diagnostic"] for f in factors)
    return {"stage": stage, "status": "provisional" if has_unknown else "assessed", "raw_known": raw,
            "raw_min": rmin, "raw_max": rmax, "display_score": bucket(raw, thr),
            "score_interval": [bucket(rmin, thr), bucket(rmax, thr)], "group_totals": totals,
            "unknown_inputs": sorted(crit)}


# ----------------------------------------------------------------------------------------- Q4, confidence
def q4(cat, facts, method, iface, target, primary_match: bool) -> dict:
    m = facts.get("Sample.matrix")
    apps, level = [], 0
    for e in cat["evidence"]:
        if e["method"] != method or target not in e["targets"]:
            continue
        lv = e["level"] if e["matrix"] == m else 1
        if e.get("geometry") and e["geometry"] != iface["geometry"]:
            lv = min(lv, 1)
        apps.append({"evidence_id": e["id"], "claim": e["claim"], "source": e["source"], "level": lv,
                     "scope": e["scope"], "sample_match": "same" if e["matrix"] == m else "different_or_unknown"})
        level = max(level, lv)
    if primary_match:
        level = max(level, 1)
    use = facts.get("MeasurementTask.business_goal")
    scopes = {a["scope"] for a in apps if a["level"] == level}
    if use == "clinical_in_vivo" and (not apps or scopes <= {"in_vitro", "model_tissue", "lab"}):
        dep = "outside_supported_evidence_scope"   # R_Q4_07
    else:
        dep = "not_validated"
    return {"q4_score": level, "evidence_polarity": "positive" if level else "unknown",
            "evidence_applications": apps, "deployment_status": dep}


def coverage(factors: list, stat: dict):
    F = [f for f in factors if f["selected_in_exclusive_group"] and not f["diagnostic"] and f["outcome"] != NA]
    if not F:
        return None
    ok = [f for f in F if f["outcome"] in (MATCH, MISMATCH) and not f["catalog_unknown"]
          and all(stat.get(k, "reported") in COVERED for k in f["input_fact_refs"])]
    return round(len(ok) / len(F), 3)


def confidence(q4s: int, cov, critical: bool) -> str:
    if cov is None or q4s == 0:
        return "low"
    if q4s >= 2 and cov >= 0.8 and not critical:
        return "high"
    if q4s >= 1 and cov >= 0.5:
        return "medium"
    return "low"


# ----------------------------------------------------------------------------------------- one Case
def run_case(cat, reg, facts, stat, target) -> dict:
    rules = reg["rules"]
    cands, excluded = [], []
    for method in cat["methods"]:
        x = Ctx(cat, facts, method, case_target=target)
        mf = [eval_rule(r, x) for r in rules if r["stage"] in ("Q1", "Q1b") and r.get("level", "method") == "method"]
        select_exclusive(mf)
        mex = [f["exclusion"] for f in mf if f["exclusion"] and f["exclusion"]["scope"] == "method"]
        q1 = aggregate("Q1", [f for f in mf if f["stage"] == "Q1"], reg)
        q1b = aggregate("Q1b", [f for f in mf if f["stage"] == "Q1b"], reg)
        primary = any(f["exclusive"] == "primary_target" and f["selected_in_exclusive_group"]
                      and f["outcome"] == MATCH for f in mf)
        if mex:
            excluded.append({"candidate_id": method, "level": "method", "excluded_by": mex, "factors": mf})
            continue
        for iid, iface in cat["interfaces"].items():
            if iface["method"] != method:
                continue
            xi = Ctx(cat, facts, method, iface=iface, case_target=target)
            pf = select_exclusive([eval_rule(r, xi) for r in rules
                                   if r["stage"] == "Q2" and r.get("level") != "combination"])
            pex = [f["exclusion"] for f in pf if f["exclusion"]]
            q2 = aggregate("Q2", pf, reg)
            if pex:
                excluded.append({"candidate_id": f"{method}|{iid}", "level": "method_interface",
                                 "excluded_by": pex, "factors": pf})
                continue
            fiber = facts.get("ProcessContext.assets.fiber")
            links = ["reuse", "new"] if fiber and fiber != "none" else ["new"]
            for link in links:
                cfg = {"configuration_id": f"{method}|{iid}|{link}", "link": link, "configuration_stage": "concept",
                       "deployment_mode": iface["deployment"], "optical_geometry": iface["geometry"],
                       "fiber_link": {"reuse": f"existing {fiber}", "new": "new link, family per S02 p6"}[link]}
                xc = Ctx(cat, facts, method, iface=iface, config=cfg, case_target=target)
                cf = component_replaces_concept(select_exclusive([eval_rule(r, xc) for r in rules if r["stage"] == "Q3"]))
                cex = [f["exclusion"] for f in cf if f["exclusion"]]
                q3 = aggregate("Q3", cf, reg)
                factors = mf + pf + cf
                if cex:
                    excluded.append({"candidate_id": cfg["configuration_id"], "level": "configuration",
                                     "excluded_by": cex, "factors": factors})
                    continue
                ev4 = q4(cat, facts, method, iface, target, primary)
                qs = [q1, q1b, q2, q3]
                suit = sum(q["display_score"] for q in qs)
                cands.append({
                    "candidate_id": cfg["configuration_id"], "method_id": method, "interface_id": iid,
                    "interface_name": iface["name"], "configuration": cfg,
                    "question_results": {q["stage"]: q for q in qs},
                    "suitability": suit, "suitability_raw": suit, "suitability_pct": round(suit / 36 * 100, 1),
                    "suitability_interval": [sum(q["score_interval"][0] for q in qs),
                                             sum(q["score_interval"][1] for q in qs)],
                    "raw_total": sum(q["raw_known"] for q in qs), "factor_contributions": factors,
                    "coverage": coverage(factors, stat), **ev4,
                    "unknown_inputs": sorted({k for q in qs for k in q["unknown_inputs"]}),
                })
    for c in cands:
        c["confidence"] = confidence(c["q4_score"], c["coverage"], False)
    cands.sort(key=lambda c: (-c["suitability"], -c["raw_total"], -CONF_RANK[c["confidence"]], c["candidate_id"]))
    return {"candidates": cands, "excluded": excluded}


def leader(res) -> str | None:
    """Top1 = best method (spec 06 §5: methods are ranked by their best allowed configuration).
    A change of interface inside the same leading method is a top-3 (medium) change, not a new leader."""
    c = res["candidates"]
    return c[0]["method_id"] if c else None


def top_pairs(res, n=3) -> list:
    return [f'{c["method_id"]}|{c["interface_id"]}' for c in res["candidates"][:n]]


def top_methods(res, n=3) -> list:
    out = []
    for c in res["candidates"]:
        if c["method_id"] not in out:
            out.append(c["method_id"])
    return out[:n]


# ----------------------------------------------------------------------------------------- sensitivity
def sensitivity(cat, reg, facts, stat, target, base) -> list:
    """Spec 06 §6 AQ01-AQ05: one unknown at a time over its allowed domain, same bucket, two passes."""
    keys = sorted({k for c in base["candidates"] for k in c["unknown_inputs"]} - {"MeasurementTask.target"})
    base_lead, base_top, base_ex = leader(base), top_pairs(base), {e["candidate_id"] for e in base["excluded"]}
    out = []
    for k in keys:
        dom = (cat["facts"].get(k) or {}).get("domain")
        if not dom:
            continue
        changes, level = [], "low"
        for v in dom:
            f2 = dict(facts)
            f2[k] = v
            r = run_case(cat, reg, f2, stat, target)
            lead, top, ex = leader(r), top_pairs(r), {e["candidate_id"] for e in r["excluded"]}
            if lead != base_lead or ex != base_ex:
                level = "high"
                changes.append({"value": v, "leader": lead, "excluded_change": sorted(ex ^ base_ex)})
            elif top != base_top and level != "high":
                level = "medium"
                changes.append({"value": v, "top_candidates": top})
        rule_ids = sorted({f["factor_id"] for c in base["candidates"] for f in c["factor_contributions"]
                           if k in f["unknown_inputs"]})
        out.append({"fact": k, "impact": level, "rule_ids": rule_ids, "baseline_leader": base_lead,
                    "scenarios": changes, "domain_complete": True})
    order = {"high": 0, "medium": 1, "low": 2}
    out.sort(key=lambda s: (order[s["impact"]], s["fact"]))
    return out


def questions(cat, sens, needs_target: bool) -> list:
    qs = []
    if needs_target:
        qs.append({"fact": "MeasurementTask.target_definition", "priority": "high",
                   "text": cat["facts"]["MeasurementTask.target_definition"]["ask"],
                   "why": "Without a defined target no comparable claims can be formed (spec 06 §6, H05).",
                   "rule_ids": ["R_Q1_01"]})
    for s in sens:
        if s["impact"] == "low":
            continue
        why = "; ".join(f'if {s["fact"].split(".")[-1]}={c["value"]}: leader {c.get("leader") or c.get("top_candidates")}'
                        for c in s["scenarios"][:3])
        qs.append({"fact": s["fact"], "priority": s["impact"], "text": cat["facts"][s["fact"]]["ask"],
                   "why": why, "rule_ids": s["rule_ids"]})
    return qs[:3] if len(qs) > 3 else qs   # AQ06: default up to 3, rest stays in the trace


def experiment(case_out: dict, facts: dict) -> dict:
    """EXP01-EXP04 (spec 06 §7). Nothing numeric is invented (EXP02)."""
    cands = case_out["ranking"]
    target = case_out["target"]
    ref = facts.get("MeasurementTask.reference_method")
    if case_out["extraction_status"] == "needs_target":
        return {"experiment_id": "EXP-SCREEN", "hypothesis": "Normal and off-spec samples differ spectrally; "
                "the difference is linked to an independently identified quality attribute or impurity.",
                "tested_candidate_ids": [c["candidate_id"] for c in cands[:3]],
                "samples_and_variation": "normal and off-spec samples from the client (count to agree)",
                "independent_reference": "independent identification of the quality problem (lab analysis)",
                "go_no_go_logic": "to be agreed after the target is defined", "rule": "EXP04"}
    hi = [q for q in case_out["questions"] if q["priority"] == "high"]
    tested = []
    for c in cands:
        if c["method_id"] not in [t["method_id"] for t in tested]:
            tested.append(c)
        if len(tested) == 2:
            break
    names = " vs ".join(f'{c["method_id"]} ({c["interface_name"]})' for c in tested)
    return {
        "experiment_id": "EXP-1", "case_ids": [case_out["case_id"]],
        "tested_candidate_ids": [c["candidate_id"] for c in tested],
        "hypothesis": f"{target or 'the target'} is measurable with {names} on the client's real samples"
                      + (f"; the open point '{hi[0]['fact']}' is answered by the test" if hi else ""),
        "addressed_factor_ids": sorted({r for q in hi for r in q["rule_ids"]}),
        "samples_and_variation": "client samples across the stated variation (count to agree with the client)",
        "independent_reference": "client reference method" if ref == "available" else "reference to agree (none stated)",
        "single_method_baselines": [c["method_id"] for c in tested],
        "independent_validation_split": "by batch/run, not neighbouring spectra of one sample (EXP03)",
        "client_acceptance_criteria_or_to_be_agreed": "to be agreed with the client",
        "go_no_go_logic": "go if the reference comparison meets the agreed criterion on independent batches",
        "rule": "EXP01",
    }


COMBOS = [  # spec 05 §6: only documented combinations; hypothesis, not a summed score
    {"methods": ["NIR", "Raman"], "matrix": "pharma_blend", "source": "S01 p7-9,14-15; REF D01",
     "hypothesis_of_gain": "Raman adds selectivity for the API band; must beat the best single method on the same samples."},
    {"methods": ["MIR", "Fluorescence"], "matrix": "tissue", "source": "S04 p1,3-5; REF D08", "co_registered": True,
     "hypothesis_of_gain": "Co-registered local MIR ATR + fluorescence; joint model must beat each single channel."},
]


def combination_factors(cat, reg, facts, target, combo) -> list:
    """Rules of level 'combination' (R_Q2_11) on one combination. Shown in the trace, never summed into a
    single candidate's score (spec 05 §6: no bonus for the number of channels)."""
    cfg = {"level": "combination", **{k: v for k, v in combo.items() if k != "hypothesis_of_gain"}}
    x = Ctx(cat, facts, "+".join(combo["methods"]), config=cfg, case_target=target)
    return [eval_rule(r, x) for r in reg["rules"] if r.get("level") == "combination"]


def premises(facts: dict, cases: list) -> list:
    out = []
    if facts.get("CustomerRequest.combination_to_keep_calibration") == "yes":
        out.append({"rule_id": "R_Q1_06", "verdict": "not_supported",
                    "text": "Adding a second method does not restore the validity of the old calibration "
                            "after a formulation change; a new matrix calibration is needed.", "source": "REF D01 risks, §5; H01"})
    if facts.get("CustomerRequest.justification") == "sensitivity_only":
        out.append({"rule_id": "R_Q1_F02", "verdict": "not_supported",
                    "text": "High sensitivity alone does not show a direct signal of the target.", "source": "S01 p16; H03"})
    if facts.get("CustomerRequest.asks") == "approve_concept" and facts.get("ProcessContext.assets.fiber"):
        out.append({"rule_id": "R_Q3C_08", "verdict": "cannot_approve",
                    "text": "Reuse of the existing link cannot be approved without the actual cable data; "
                            "a new-link branch is kept as the alternative.", "source": "S02 p6; H04"})
    if any(c.get("deployment_status") == "outside_supported_evidence_scope" for c in cases):
        out.append({"rule_id": "R_Q4_07", "verdict": "not_supported",
                    "text": "The cited study (in-vitro / model tissue) does not establish immediate in-vivo readiness; "
                            "a research plan is the next step.", "source": "S03 p1-3,6; S04; H06"})
    if facts.get("CustomerRequest.asks") == "exact_config_now" and \
            facts.get("MeasurementTask.target_definition") == "undefined":
        out.append({"rule_id": "R_Q1_01", "verdict": "not_possible_yet",
                    "text": "No exact sensor can be named before the target is defined.", "source": "REF §3; H05"})
    return out


# ----------------------------------------------------------------------------------------- public API
def build_cases(vals: dict, streams: list | None) -> list:
    targets = vals.get("MeasurementTask.target")
    targets = targets if isinstance(targets, list) else ([targets] if targets else [None])
    streams = streams or [{"id": None, "facts": {}}]
    out = []
    for s in streams:
        for t in targets:
            cid = "+".join(p for p in [s.get("id"), t] if p) or "case-1"
            out.append({"case_id": cid, "target": t, "stream": s.get("id"), "overrides": s.get("facts", {})})
    return out


def headline(case_out: dict) -> str:
    """One line for the expert: the leaders and, if any, the open fact that could change them.
    e.g. 'NIR and Raman lead; provisional until fluorescence of the sample is checked.'"""
    if case_out["extraction_status"] == "needs_target":
        return "No method yet: the target must be defined first; methods are screening directions only."
    ms = case_out["methods"]
    if not ms:
        return "No allowed configuration for this case."
    best = ms[0]["suitability"]
    lead = [m["method_id"] for m in ms if m["suitability"] == best]
    text = (" and ".join(lead) + (" lead" if len(lead) > 1 else " leads")) + f" ({best}/36)"
    crit = [q for q in case_out["questions"] if q["priority"] == "high"]
    if crit:
        fact = crit[0]["fact"].split(".", 1)[1].replace("_", " ").replace(".", " ")
        return text + f"; provisional until '{fact}' is checked."
    return text + "."


def rank_mode() -> str:
    return os.environ.get("B_RANK_MODE", "technical")


def assess_b(raw_facts: dict, streams: list | None = None, with_sensitivity: bool = True) -> dict:
    cat, reg = load_b()
    vals, stat, meta = normalize_facts(raw_facts)
    vals = derive(vals)
    for k in vals:
        stat.setdefault(k, "inferred")
    case_outs = []
    for case in build_cases(vals, streams):
        o_vals, o_stat, _ = normalize_facts(case["overrides"])
        facts = {**vals, **o_vals}
        st = {**stat, **o_stat}
        needs_target = facts.get("MeasurementTask.target_definition") == "undefined" or case["target"] is None \
            and facts.get("MeasurementTask.target_definition") != "defined"
        res = run_case(cat, reg, facts, st, case["target"])
        sens = sensitivity(cat, reg, facts, st, case["target"], res) if with_sensitivity else []
        critical = {s["fact"] for s in sens if s["impact"] == "high"}
        for c in res["candidates"]:
            c["critical_unknown"] = bool(critical & set(c["unknown_inputs"]))
            c["confidence"] = confidence(c["q4_score"], c["coverage"], c["critical_unknown"])
        technical = [c["candidate_id"] for c in res["candidates"]]
        # spec 06 §5 sort key: (critical_unknown ASC, suitability DESC, raw_total DESC, confidence DESC, id).
        # Team decision 18.10: critical_unknown stays a marker and the reason for a clarification
        # question, but is not the first sort key (a strong method must not drop only because an important
        # question was found for it). B_RANK_MODE=spec restores the literal spec 06 §5 key.
        crit_first = rank_mode() == "spec"
        res["candidates"].sort(key=lambda c: (c["critical_unknown"] if crit_first else False, -c["suitability"],
                                              -c["raw_total"], -CONF_RANK[c["confidence"]], c["candidate_id"]))
        out = {"case_id": case["case_id"], "target": case["target"], "stream": case["stream"],
               "extraction_status": "needs_target" if needs_target else "valid",
               "ranking": res["candidates"], "technical_rank_without_critical_groups": technical,
               "excluded": [{k: v for k, v in e.items() if k != "factors"} for e in res["excluded"]],
               "sensitivity": sens, "sensitivity_complete": True}
        out["questions"] = questions(cat, sens, needs_target)
        out["first_experiment"] = experiment(out, facts)
        out["combinations"] = [{**cb, "factor_contributions": combination_factors(cat, reg, facts, case["target"], cb)}
                               for cb in COMBOS if facts.get("Sample.matrix") == cb["matrix"]
                               and all(any(c["method_id"] == m for c in res["candidates"]) for m in cb["methods"])]
        best = {}
        for c in res["candidates"]:
            best.setdefault(c["method_id"], c)
        out["methods"] = [{"method_id": m, "best_candidate_id": c["candidate_id"], "interface": c["interface_name"],
                           "suitability": c["suitability"], "suitability_interval": c["suitability_interval"],
                           "scores": {s: c["question_results"][s]["display_score"] for s in ("Q1", "Q1b", "Q2", "Q3")},
                           "q4_score": c["q4_score"], "confidence": c["confidence"],
                           "critical_unknown": c["critical_unknown"], "deployment_status": c["deployment_status"]}
                          for m, c in best.items()]
        out["headline"] = headline(out)
        top = out["ranking"][0] if out["ranking"] else None
        out["decision_status"] = ("needs_target" if needs_target else "insufficient_information" if not top
                                  else "provisional" if any(q["status"] == "provisional"
                                                            for q in top["question_results"].values()) else "assessed")
        case_outs.append(out)
    bundle = None
    if len(case_outs) > 1:   # spec 05 §6: aggregate = min over mandatory Cases per method
        per = {}
        for co in case_outs:
            for m in co["methods"]:
                per.setdefault(m["method_id"], []).append(m["suitability"])
        bundle = sorted(({"method_id": m, "aggregate_bundle_score": min(v), "cases": len(v)}
                         for m, v in per.items() if len(v) == len(case_outs)),
                        key=lambda b: (-b["aggregate_bundle_score"], b["method_id"]))
    flat_cands = [c for co in case_outs for c in co["ranking"]]
    return {"engine": "B", "rank_mode": rank_mode(), "ruleset_version": reg["version"], "catalogue_version": cat["version"],
            "score_contract_version": "levels_10", "bucket_version": reg["bucket"],
            "facts": fact_records(cat, vals, stat, meta),
            "cases": case_outs, "aggregate_bundle": bundle, "premises": premises(vals, flat_cands)}
