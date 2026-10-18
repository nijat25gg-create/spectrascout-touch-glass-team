"""Mutation test: each mutation of rules/gates.yaml must make rules/check_gates.py fail.

    python rules/mutate_gates.py      # from the repo root; runs on temporary copies, changes nothing
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
MUTS = [
 ("P-FIBER-RANGE weakened", "    when: {fiber_overlap_none: [true]}\n    effect: exclude_config", "    when: {fiber_overlap_none: [true]}\n    effect: risk"),
 ("P-NO-FLUOROPHORE weakened", "    when: {fluorophore: [not_identified]}\n    effect: exclude", "    when: {fluorophore: [not_identified]}\n    effect: risk"),
 ("P-CLINICAL-SCOPE wrong", "when: {intended_use: [clinical_in_vivo]}", "when: {intended_use: [production]}"),
 ("APP-PHARMA drops Raman", "targets: [K03, K05]\n    when: {domain: [pharma_solid], sample_form: [powder], target_kind: [api]}", "targets: [K03]\n    when: {domain: [pharma_solid], sample_form: [powder], target_kind: [api]}"),
 ("bad vocabulary", "when: {target_defined: [no]}", "when: {target_defined: [nope]}"),
 ("fiber data wrong", "  silica_vis_nir:   {range_nm: [350, 2400]}", "  silica_vis_nir:   {range_nm: [350, 26000]}"),
 ("top-3 decision", "decision: top1", "decision: top3"),
 ("no selectivity tie-break", "  - {when: {domain: [dairy, bioprocess, petroleum, tissue, polymer_melt]}, column: selectivity", "  - {when: {domain: [nothing]}, column: selectivity"),
 ("fluorescence asked to client", "matrix_fluorescence: {kind: lab_check", "matrix_fluorescence: {kind: method"),
 ("physical variation broken", "    when: {physical_variation: [yes]}", "    when: {physical_variation: [no]}"),
 ("existing_fiber probed", "existing_fiber:      {kind: method, probe: false,", "existing_fiber:      {kind: method,"),
 ("Raman support for any aqueous target", "when: {matrix_aqueous: [yes], target_kind: [glucose, lactate, metabolite_other]}", "when: {matrix_aqueous: [yes]}"),
 ("sample type mismatch only a risk", "    when: {sample_form_not_in_row: [true]}\n    effect: needs_info", "    when: {sample_form_not_in_row: [true]}\n    effect: risk_high"),
 ("no fiber overlap tolerance", "fiber_full_overlap: {default: 0.9, mir: 0.6}", "fiber_full_overlap: {default: 1.0, mir: 1.0}"),
 ("opaque transmission only a risk", "    effect: needs_info        # 18.10: known opaque", "    effect: risk_high        # 18.10: known opaque"),
 ("opaque unknown stricter than opaque known", "    on_unknown: risk          # 18.10: unknown must not", "    on_unknown: needs_info    # 18.10: unknown must not"),
 ("pharma blend application for any target", "when: {domain: [pharma_solid], sample_form: [powder], target_kind: [api]}", "when: {domain: [pharma_solid], sample_form: [powder]}"),
 ("gas in scope", "    when: {sample_form: [gas]}\n    effect: case_outside_scope", "    when: {sample_form: [gas]}\n    effect: risk"),
 ("chromophore check for biomass", "when: {chromophore: [no], target_kind: [api, fat, protein, glucose, lactate, metabolite_other, water, contaminant, tissue_type, other]}", "when: {chromophore: [no]}"),
]
fails = 0
for name, a, b in MUTS:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for sub in ("rules", "eval", "engine", "contracts", "llm"):
            shutil.copytree(REPO / sub, d / sub, ignore=shutil.ignore_patterns("__pycache__", "materials"))
        p = d / "rules" / "gates.yaml"; s = p.read_text(encoding="utf-8")
        assert a in s, name
        p.write_text(s.replace(a, b, 1), encoding="utf-8")
        r = subprocess.run([sys.executable, str(d / "rules" / "check_gates.py")], capture_output=True, text=True)
        first = next((l for l in r.stdout.splitlines() if l.startswith("FAIL")), "")
        caught = r.returncode != 0
        if not caught:   # the golden set did not notice: the engine regression tests must
            t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "engine/test_gates.py"],
                               capture_output=True, text=True, cwd=d)
            caught = t.returncode != 0
            first = next((l for l in t.stdout.splitlines() if l.startswith("FAILED")), "")
        print(f"{'CAUGHT' if caught else 'MISSED'}  {name:30} {first[:110]}")
        fails += not caught
print(f"\n{len(MUTS) - fails}/{len(MUTS)} mutations caught")
sys.exit(1 if fails else 0)
