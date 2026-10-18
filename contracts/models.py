"""
SpectraScout contracts v0.2 (+ v0.3 draft: optional fields only) — single source of truth.

Every arrow in the pipeline that carries data has exactly one contract here.
JSON Schema files in contracts/schemas/ are GENERATED from this file
(run: python contracts/export_schemas.py). Never edit the .json schemas by hand.

Main pass (/assessments), 8 contracts:
  C1  AnalyzeRequest   Gadzhi  (frontend)  -> Semyon (backend)
  C2  ExtractInput     Semyon  (backend)   -> Nidzhat (LLM module, step A)
  C3  Extraction       Nidzhat (LLM)       -> Semyon
  C4  ScoreInput       Semyon              -> Yarik (rules engine)
  C5  Scoring          Yarik               -> Semyon
  C6  ExplainInput     Semyon              -> Nidzhat (LLM module, step B)
  C7  Explanation      Nidzhat             -> Semyon
  C8  Briefing         Semyon              -> Gadzhi

Extra (not new arrows of the main pass):
  C1b RecomputeRequest Gadzhi -> Semyon   (/assessments/recalculate, then C4..C8 are reused, step A is skipped)
  E   ErrorResponse    Semyon -> Gadzhi   (any 4xx/5xx)

Content (from the chemist Nikita) lives in enums below: FEATURE values, METHOD, MODE.
Any change to an enum = change of contracts C3, C4, C5, C8 -> agree with Nikita, Yarik, Semyon.
"""
from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "0.2"


class Strict(BaseModel):
    """additionalProperties: false everywhere (required by Claude structured outputs)."""
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- shared enums
Language = Literal["de", "en"]
Status = Literal["known", "assumed", "unknown"]
Level = Literal["high", "medium", "low"]
Method = Literal["uv_vis", "nir", "mir", "raman", "fluorescence", "scattering"]
Mode = Literal["transmission", "transflection", "atr", "diffuse_reflectance",
               "raman_backscatter", "fluorescence_emission", "combi_probe"]

ParameterId = Literal[
    "measurand", "measurand_type", "matrix", "phase", "water_content",
    "concentration_range", "required_accuracy", "temperature", "pressure",
    "aggressiveness_fouling", "installation_point", "distance_to_instrument",
    "measurement_frequency", "reference_method", "samples_available", "regulatory",
]
ParameterSource = Literal["customer_text", "llm_assumption", "expert_edit"]

# Normalized features: what the rules engine (Yarik) actually reads.
# Draft values, to be confirmed by Nikita.
FeatureKey = Literal[
    "phase", "water_level", "analyte_type", "concentration_level", "accuracy_need",
    "temperature_class", "pressure_class", "fouling_risk", "distance_class",
    "fluorescence_risk", "turbidity", "hazardous_area",
]
Phase = Literal["liquid", "solid_powder", "slurry", "emulsion", "gas", "solid_surface", "unknown"]
WaterLevel = Literal["none", "low", "medium", "high", "unknown"]
AnalyteType = Literal["moisture", "organic_compound", "colored_compound", "polymorph",
                      "particles_cells", "trace_contaminant", "other", "unknown"]
ConcentrationLevel = Literal["trace_ppm", "low_percent", "high_percent", "unknown"]
AccuracyNeed = Literal["screening", "quantitative", "high_precision", "unknown"]
TemperatureClass = Literal["cryogenic", "ambient", "elevated", "high", "unknown"]
PressureClass = Literal["vacuum", "ambient", "elevated", "high", "unknown"]
FoulingRisk = Literal["low", "medium", "high", "unknown"]
DistanceClass = Literal["short", "medium", "long", "unknown"]   # short <2 m, medium 2-20 m, long >20 m
FluorescenceRisk = Literal["low", "high", "unknown"]
Turbidity = Literal["clear", "turbid", "opaque", "unknown"]
HazardousArea = Literal["yes", "no", "unknown"]


# ---------------------------------------------------------------- building blocks
class Parameter(Strict):
    """Human-readable fact about the customer case (shown in the UI)."""
    id: ParameterId
    value: Optional[str] = Field(description="Free text value, null if unknown")
    status: Status
    evidence_quote: Optional[str] = Field(description="Exact words from the customer text, null if assumed or unknown")
    source: ParameterSource


class F_Phase(Strict):
    value: Phase
    status: Status
class F_Water(Strict):
    value: WaterLevel
    status: Status
class F_Analyte(Strict):
    value: AnalyteType
    status: Status
class F_Conc(Strict):
    value: ConcentrationLevel
    status: Status
class F_Accuracy(Strict):
    value: AccuracyNeed
    status: Status
class F_Temp(Strict):
    value: TemperatureClass
    status: Status
class F_Pressure(Strict):
    value: PressureClass
    status: Status
class F_Fouling(Strict):
    value: FoulingRisk
    status: Status
class F_Distance(Strict):
    value: DistanceClass
    status: Status
class F_Fluor(Strict):
    value: FluorescenceRisk
    status: Status
class F_Turbidity(Strict):
    value: Turbidity
    status: Status
class F_Hazard(Strict):
    value: HazardousArea
    status: Status


class Features(Strict):
    """Normalized, machine-readable view of the case. Input of the rules engine."""
    phase: F_Phase
    water_level: F_Water
    analyte_type: F_Analyte
    concentration_level: F_Conc
    accuracy_need: F_Accuracy
    temperature_class: F_Temp
    pressure_class: F_Pressure
    fouling_risk: F_Fouling
    distance_class: F_Distance
    fluorescence_risk: F_Fluor
    turbidity: F_Turbidity
    hazardous_area: F_Hazard


class CriterionScore(Strict):
    criterion: str
    score: float
    rule_id: Optional[str]
    note: str


class ScoredMethod(Strict):
    rank: int
    method: Method
    mode: Mode
    spectral_range: str
    fiber: str
    probe: str
    score_total: float
    scores: list[CriterionScore]
    confidence: Level


class RejectedMethod(Strict):
    method: Method
    reason: str
    rule_id: Optional[str]
    blocker: bool = Field(description="true = excluded by a hard rule, false = scored too low")


class Claim(Strict):
    claim: str
    kb_card: str = Field(description="Id of the knowledge card that supports the claim, e.g. card-nir")
    source: Optional[str] = Field(
        default=None, description="v0.3: AFS source of the claim as given in the engine trace (e.g. 'S01 p.4'), null if none")


class MethodRationale(Strict):
    method: Method
    claims: list[Claim]


class Question(Strict):
    id: str
    text: str = Field(description="Question to the customer, in the case language")
    priority: Level
    why: str = Field(description="How the answer can change the recommendation")
    parameter_id: ParameterId
    feature: Optional[FeatureKey] = Field(description="Feature the answer sets, null if it only adds context")
    attribute: Optional[str] = Field(
        default=None, description="v0.3: gates attribute the answer sets (from assessment.questions), null if none")


class Experiment(Strict):
    goal: str
    sample_count: str
    sample_design: str
    interferents: list[str]
    reference_method: str
    methods_compared: list[Method]
    steps: list[str]
    success_criterion: str
    duration_estimate: str


class Risk(Strict):
    text: str
    severity: Level


# ---------------------------------------------------------------- v0.3 draft (additive, optional)
# Attribute vocabulary of the gates engine (rules/gates.yaml -> attributes). The allowed VALUES per
# attribute live in rules/gates.yaml and are checked by llm.vocab.normalize_attributes, so the
# Claude output schema stays small. llm/vocab.py tests that this list equals rules/gates.yaml.
AttributeName = Literal[
    "target_defined", "target_kind", "target_class", "targets_count", "quantitative",
    "reference_method", "reference_uncertainty", "acceptance_criteria", "concentration_range",
    "intended_use", "domain", "sample_form", "optical_density", "matrix_aqueous", "heterogeneous",
    "fluorophore", "chromophore", "matrix_fluorescence", "formulation_changed", "streams",
    "physical_variation", "temperature", "fouling", "distance", "link_confirmed", "existing_fiber",
    "gmp", "client_method", "reuse_calibration", "add_method_to_keep_calibration", "justification",
    "asks", "cited_evidence", "own_validation",
]
AttributeStatus = Literal["known", "assumed", "unknown", "conflicting"]


class AttributeFact(Strict):
    """One attribute of the analysis request (v0.3). known = the customer says it (quote verbatim);
    assumed = a safe inference (no quote); unknown = not said; conflicting = the text says two things."""
    name: AttributeName
    value: Optional[str] = Field(description="One value from the vocabulary of this attribute, null if unknown")
    status: AttributeStatus
    quote: Optional[str] = Field(description="Exact words from the customer text, null if assumed or unknown")


FactBStatus = Literal["reported", "inferred", "unknown", "conflicting", "confirmed_experiment", "confirmed_expert"]


class FactB(Strict):
    """One property for method B (v0.4): value + unit/category + source + status.
    key = ER entity.field from rules/b/catalog_b.yaml. reported = the customer says it (quote verbatim);
    inferred = a safe inference (no quote); unknown = not said. Missing data is never filled."""
    key: str = Field(description="Fact key from the method B catalog, e.g. 'Sample.physical_form'")
    value: Optional[str] = Field(description="One allowed category (several targets: comma-separated), null if unknown")
    unit: Optional[str] = Field(default=None, description="Unit as the customer wrote it, or 'category'")
    status: FactBStatus
    quote: Optional[str] = Field(default=None, description="Exact words from the customer text, null unless reported")
    source: Optional[str] = Field(default=None, description="client_text | step A inference | expert | experiment")


class JevVote(Strict):
    """Jev classification of one attribute (v0.3). Filled by the backend after step A, never by Claude."""
    name: AttributeName
    value: Optional[str] = Field(description="Jev's most probable value, null if 'not_stated' won")
    p: float = Field(description="Probability of that value")
    agrees: bool = Field(description="True if Jev's value equals the attribute value from step A")


class RowResult(Strict):
    """One catalog row (method x probe) after the gates (v0.3)."""
    row: str = Field(description="Catalog id, e.g. K03")
    method: Method
    technique: str
    status: Literal["candidate", "needs_info", "excluded"]
    evidence: Literal["application", "analogy", "physics_only", "none"]
    risks: list[str] = Field(description="rule_id: effect for each risk")
    reasons: list[str] = Field(description="All fired rules on this row, rule_id: effect")


class PremiseFlag(Strict):
    rule_id: str
    verdict: Literal["contradicted", "not_supported"]
    text: str
    source: list[str]


class GateQuestion(Strict):
    attribute: AttributeName
    kind: Literal["method", "plan", "lab_check"]
    strength: Optional[float] = Field(description="Share of answers that change the decision; null if forced or plan")
    forced: bool
    text: str


class TraceStep(Strict):
    step: Literal["Q1", "Q2", "Q3", "Q4", "OUT"]
    rule_id: str
    target: Optional[str] = Field(description="Row id, or null for case-level rules")
    effect: str
    source: list[str]


class GatesAssessment(Strict):
    """Output of engine.gates (v0.3), carried inside C5 as `assessment`."""
    rules_version: str
    decision_status: Literal["provisional", "insufficient_information", "outside_scope"]
    selected: list[str] = Field(description="Top rows (at most 3), best first")
    combinations: list[list[Method]]
    rows: list[RowResult] = Field(description="Every catalog row exactly once")
    premise_flags: list[PremiseFlag]
    questions: list[GateQuestion] = Field(description="Method questions (strongest first), then plan questions")
    lab_checks: list[GateQuestion] = Field(description="Checked on samples in step 0 of the plan, not asked")
    trace: list[TraceStep]
    ignored_inputs: Optional[list[str]] = Field(
        default=None, description="v0.3: attribute names or values the engine ignored (outside the vocabulary)")


# ================================================================ C1
class AnalyzeRequest(Strict):
    """C1 · Gadzhi (frontend) -> Semyon (backend) · POST /assessments"""
    text: str = Field(min_length=20, max_length=3000)
    language: Language


# ================================================================ C2
class ExtractInput(Strict):
    """C2 · Semyon -> Nidzhat · call llm.extract(...)"""
    case_id: str
    text: str
    language: Language


# ================================================================ C3  (sent to Claude as output schema)
class Extraction(Strict):
    """C3 · Nidzhat (Claude step A) -> Semyon"""
    summary: str = Field(description="Customer task in one sentence, in the case language")
    parameters: list[Parameter] = Field(description="All 16 parameter ids exactly once")
    features: Features
    attributes: Optional[list[AttributeFact]] = Field(
        default=None, description="v0.3: attributes of the analysis request, each name at most once")
    jev: Optional[list[JevVote]] = Field(
        default=None, description="v0.3: leave null. Filled by the backend after step A (Jev cross-check)")
    facts_b: Optional[list[FactB]] = Field(
        default=None, description="v0.4 optional: method B facts (value, unit, source, status) for engine B")


# ================================================================ C4
class ScoreInput(Strict):
    """C4 · Semyon -> engine · call engine.score_methods(...) (gates engine since 18.10)"""
    case_id: str
    features: Features
    attributes: Optional[list[AttributeFact]] = Field(
        default=None, description="v0.3: C3.attributes (or the edited C8.attributes on recalculate); the gates "
                                  "engine reads these. Without them the attributes are derived from features")
    facts_b: Optional[list[FactB]] = Field(
        default=None, description="v0.4 optional: C3.facts_b (or edited C8.facts_b); engine B reads these, "
                                  "else it bridges from the attributes")


# ================================================================ C5
class Scoring(Strict):
    """C5 · engine -> Semyon. Filled from the gates engine (rules/gates.yaml); `assessment` carries its full result"""
    rules_version: str
    ranked: list[ScoredMethod] = Field(description="1-3 methods, rank 1 = best")
    rejected: list[RejectedMethod]
    assessment: Optional[GatesAssessment] = Field(
        default=None, description="v0.3: gates engine result (statuses, premises, questions, trace)")
    assessment_b: Optional[dict[str, Any]] = Field(
        default=None, description="v0.4 optional: method B engine result (spec spectroscopy-rules 1.2): Cases, "
                                  "Q1/Q1b/Q2/Q3 scores 0-9, suitability 0-36, Q4, confidence, sensitivity, questions")


# ================================================================ C6
class ExplainInput(Strict):
    """C6 · Semyon -> Nidzhat · call llm.explain(...)"""
    case_id: str
    language: Language
    summary: str
    parameters: list[Parameter]
    features: Features
    scoring: Scoring


# ================================================================ C7  (sent to Claude as output schema)
class Explanation(Strict):
    """C7 · Nidzhat (Claude step B) -> Semyon"""
    questions: list[Question]
    rationale: list[MethodRationale] = Field(description="One entry per ranked method")
    experiment: Experiment
    risks: list[Risk]


# ================================================================ C8
class RankedMethodWithRationale(ScoredMethod):
    claims: list[Claim]


class Methods(Strict):
    ranked: list[RankedMethodWithRationale]
    rejected: list[RejectedMethod]


class QuestionWithAnswer(Question):
    answer: Optional[str] = Field(description="Filled from the UI, null until answered")


class ExpertFlag(Strict):
    target: str
    reason: str


class Change(Strict):
    field: str
    before: Optional[str]
    after: Optional[str]


class Meta(Strict):
    model: str
    generated_at: str
    rules_version: str
    kb_version: str
    recomputed: bool


class Briefing(Strict):
    """C8 · Semyon -> Gadzhi · response of /assessments and /assessments/recalculate"""
    schema_version: Literal["0.2"]
    case_id: str
    language: Language
    summary: str
    parameters: list[Parameter]
    features: Features
    questions: list[QuestionWithAnswer]
    methods: Methods
    experiment: Experiment
    risks: list[Risk]
    expert_flags: list[ExpertFlag]
    changes: list[Change] = Field(description="Empty on /assessments, filled on /assessments/recalculate")
    meta: Meta
    attributes: Optional[list[AttributeFact]] = Field(
        default=None, description="v0.3: C3.attributes after normalisation (and Jev), for the expert to check and edit")
    assessment: Optional[GatesAssessment] = Field(
        default=None, description="v0.3: C5.assessment (gates engine: statuses, premises, questions, lab checks, trace)")
    assessment_b: Optional[dict[str, Any]] = Field(
        default=None, description="v0.4 optional: C5.assessment_b (method B engine result)")
    facts_b: Optional[list[FactB]] = Field(
        default=None, description="v0.4 optional: method B facts used for this briefing (editable, sent back on recalculate)")


# ================================================================ C1b
class FeatureEdit(Strict):
    feature: FeatureKey
    value: str = Field(description="Must be one of the allowed values of that feature")
    note: Optional[str]


class Answer(Strict):
    question_id: str
    answer: str
    feature_value: Optional[str] = Field(description="Value for question.feature, null if the question has no feature")


class RecomputeRequest(Strict):
    """C1b · Gadzhi -> Semyon · POST /assessments/recalculate (step A is skipped, C4..C8 reused)"""
    briefing: Briefing
    edits: list[FeatureEdit]
    answers: list[Answer]


# ================================================================ E
class ErrorBody(Strict):
    code: Literal["validation_error", "llm_error", "engine_error", "internal_error"]
    message: str
    details: Optional[str]


class ErrorResponse(Strict):
    """E · Semyon -> Gadzhi · any 4xx/5xx"""
    error: ErrorBody


CONTRACTS = {
    "C1": AnalyzeRequest, "C2": ExtractInput, "C3": Extraction, "C4": ScoreInput,
    "C5": Scoring, "C6": ExplainInput, "C7": Explanation, "C8": Briefing,
    "C1b": RecomputeRequest, "E": ErrorResponse,
}
