"""Rules engine (owner: Nidzhat after 15.10). Gates engine on rules/gates.yaml since 18.10.

    score_methods(ScoreInput) -> Scoring       C4 -> C5 (ranked/rejected filled from the gates)
    gates.assess(attrs) -> GatesAssessment     the gates result itself
The old points engine on rules/rules.yaml is retired and kept in legacy/ for reference only.
"""
from .score import features_to_attributes, score_methods
from .gates_loader import load_gates

__all__ = ["score_methods", "features_to_attributes", "load_gates"]
