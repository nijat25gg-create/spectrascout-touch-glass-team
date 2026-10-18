"""Bridge: today's step-A attributes (C3, 34 classes) -> method B typed facts (spec 01 §3, ER names of spec 09).

Temporary until step A extracts the B fields directly. Every mapping is a class conversion of a value the
customer text supports (quote checked in step A); nothing is added. known -> reported, assumed -> inferred
(inferred never counts as covered, spec 06 §4). What has no B field (gmp, streams count, targets_count
without names) is not mapped; it stays visible in the A attributes.
"""
from __future__ import annotations

MATRIX = {"pharma_solid": "pharma_blend", "dairy": "dairy", "bioprocess": "aqueous_bioprocess",
          "petroleum": "petroleum", "polymer_melt": "polymer", "tissue": "tissue", "other": "other"}
TARGET = {"api": "api", "fat": "fat", "protein": "protein", "glucose": "glucose", "lactate": "lactate",
          "water": "water", "contaminant": "contaminant", "tissue_type": "tissue_type", "biomass": "biomass",
          "metabolite_other": "other", "other": "other"}
OPACITY = {"clear": "clear", "turbid": "translucent", "opaque": "opaque", "varies": "variable"}
METHOD = {"nir": "NIR", "mir": "MIR", "raman": "Raman", "uv_vis": "UV_VIS", "fluorescence": "Fluorescence"}
YES = (True, "yes", "true", "True")


def facts_from_attributes(attrs: list | None) -> dict:
    """C3/C8 `attributes` (list of AttributeFact) -> {B key: {value, status, quote}}."""
    a, st, q = {}, {}, {}
    for f in attrs or []:
        if f.status in ("known", "assumed") and f.value is not None:
            a[f.name], st[f.name], q[f.name] = f.value, ("reported" if f.status == "known" else "inferred"), f.quote
    out = {}

    def put(key, value, src):
        if value is not None:
            out[key] = {"value": value, "status": st.get(src, "inferred"), "quote": q.get(src),
                        "source": f"client_text via step A attribute '{src}'", "unit": "category"}

    put("Sample.matrix", MATRIX.get(a.get("domain")), "domain")
    form = a.get("sample_form")
    if form:
        phase = {"powder": "solid", "liquid": "liquid", "paste_melt": "liquid", "soft_solid": "solid",
                 "solid": "solid", "gas": "gas"}.get(form)
        put("Sample.phase", phase, "sample_form")
        pf = {"powder": "powder", "solid": "bulk_solid",
              "paste_melt": "melt" if a.get("domain") == "polymer_melt" else "paste",
              "soft_solid": "tissue" if a.get("domain") == "tissue" else None}.get(form)
        put("Sample.physical_form", pf, "sample_form")
    if a.get("target_kind") in TARGET:
        put("MeasurementTask.target", [TARGET[a["target_kind"]]], "target_kind")
    td = a.get("target_defined")
    put("MeasurementTask.target_definition",
        {True: "defined", "yes": "defined", "partial": "partial", False: "undefined", "no": "undefined"}.get(td), "target_defined")
    if a.get("quantitative") in YES:
        put("MeasurementTask.measurement_goal", "quantify", "quantitative")
    put("MeasurementTask.reference_method", {"available": "available", "none": "none"}.get(a.get("reference_method")), "reference_method")
    put("MeasurementTask.business_goal", {"lab_research": "lab_research", "pilot": "pilot", "production": "in_line_production",
                                          "clinical_in_vivo": "clinical_in_vivo"}.get(a.get("intended_use")), "intended_use")
    put("Sample.optical_properties.opacity", OPACITY.get(a.get("optical_density")), "optical_density")
    if a.get("matrix_fluorescence") == "high":
        put("Sample.optical_properties.fluorescence", "present", "matrix_fluorescence")
    if "heterogeneous" in a:
        put("Sample.heterogeneity", "heterogeneous" if a["heterogeneous"] in YES else "homogeneous", "heterogeneous")
    put("Sample.relevant_components.fluorophore", {"named": "known", "indicator_justified": "marker_allowed",
                                                  "not_identified": "none_known"}.get(a.get("fluorophore")), "fluorophore")
    if a.get("chromophore") in YES:
        put("Sample.relevant_components.absorber", "known", "chromophore")
    if a.get("physical_variation") in YES:
        put("Sample.variability.physical", "varies_uncontrolled", "physical_variation")
    if a.get("formulation_changed") in YES:
        put("Sample.variability.formulation", "changed", "formulation_changed")
        if a.get("reuse_calibration") in YES and a.get("client_method") in METHOD:
            put("ProcessContext.assets.method", METHOD[a["client_method"]], "client_method")
            put("ProcessContext.assets.calibration_scope", "outside", "formulation_changed")
    put("ProcessContext.temperature_range", {"high": "described_hot", "elevated": "described_hot",
                                             "ambient": "ambient"}.get(a.get("temperature")), "temperature")
    put("ProcessContext.operation_constraints.fouling", {"high": "stated", "low": "none"}.get(a.get("fouling")), "fouling")
    put("ProcessContext.instrument_distance", {"at_process": "local", "outside_area": "remote",
                                               "other_building": "remote"}.get(a.get("distance")), "distance")
    put("ProcessContext.assets.fiber", a.get("existing_fiber"), "existing_fiber")
    if a.get("link_confirmed") in YES:
        put("ProcessContext.assets.fiber_profile", "confirmed", "link_confirmed")
    if a.get("add_method_to_keep_calibration") in YES:
        put("CustomerRequest.combination_to_keep_calibration", "yes", "add_method_to_keep_calibration")
    put("CustomerRequest.justification", {"sensitivity_only": "sensitivity_only",
                                          "physical_basis": "physical_basis"}.get(a.get("justification")), "justification")
    put("CustomerRequest.asks", a.get("asks") if a.get("asks") != "unknown" else None, "asks")
    return out
