"""Contracts for the assessment pipeline.

Single source of truth: contracts/models.py at the repository root. This module only gives
the backend names to the shared models, so the backend cannot drift from the contracts.
C1 and C1b are the public requests, C2-C7 the step boundaries, C8 the briefing.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

import app  # noqa: F401  (puts the repository root on sys.path)
from contracts.models import (  # noqa: F401  (re-exported)
    Answer as QuestionAnswer,
    Briefing as AssessmentResponse,
    Change,
    Claim,
    CriterionScore,
    Experiment,
    ExpertFlag,
    ExplainInput,
    Explanation,
    ExtractInput,
    Extraction,
    FeatureEdit,
    Features,
    Language,
    Meta,
    MethodRationale,
    Methods,
    Parameter,
    Question as ExplanationQuestion,
    QuestionWithAnswer as Question,
    RankedMethodWithRationale as RankedMethod,
    RecomputeRequest,
    RejectedMethod,
    Risk,
    ScoredMethod as RankedMethodScore,
    ScoreInput,
    Scoring,
)

UseCaseText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=20, max_length=5000),
]


class AssessRequest(BaseModel):
    """C1. Body of POST /assessments.

    Slightly more tolerant than contracts.models.AnalyzeRequest: text is stripped and may be
    up to 5000 characters, and `language` may be omitted (the orchestrator then uses English).
    """

    model_config = ConfigDict(extra="forbid")

    text: UseCaseText
    language: Literal["en", "de"] | None = None
