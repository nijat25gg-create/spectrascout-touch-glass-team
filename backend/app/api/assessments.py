import json
import logging

from fastapi import APIRouter, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.pipeline.assess import run_assessment, run_recalculate
from app.pipeline.recompute import request_from_briefing
from app.schemas.assessment import AssessmentResponse, AssessRequest, RecomputeRequest
from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assessments", tags=["assessments"])

_ERROR_RESPONSES = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "The request body is invalid",
    },
    status.HTTP_502_BAD_GATEWAY: {
        "model": ErrorResponse,
        "description": "A pipeline step returned an unusable result",
    },
    status.HTTP_504_GATEWAY_TIMEOUT: {
        "model": ErrorResponse,
        "description": "A pipeline step timed out",
    },
}


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Create an assessment",
    response_model=AssessmentResponse,
    responses=_ERROR_RESPONSES,
)
async def create_assessment(assessment: AssessRequest) -> AssessmentResponse:
    """Validate a use case and return one briefing."""
    logger.debug(
        "Accepted assessment text_length=%s language=%s",
        len(assessment.text),
        assessment.language,
    )
    return run_assessment(assessment)


@router.post(
    "/recalculate",
    status_code=status.HTTP_200_OK,
    summary="Recalculate an assessment",
    response_model=AssessmentResponse,
    responses=_ERROR_RESPONSES,
)
async def recalculate_assessment(request: Request) -> AssessmentResponse:
    """Score and explain an edited briefing. Extraction is not called.

    Accepts C1b `{briefing, edits, answers}` or the briefing object the page posts.
    """
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise RequestValidationError(_body_error("body must be JSON")) from exc
    body = _recompute_body(payload)
    logger.debug("Accepted recalculation case_id=%s", body.briefing.case_id)
    return run_recalculate(body)


def _recompute_body(payload: object) -> RecomputeRequest:
    if not isinstance(payload, dict):
        raise RequestValidationError(_body_error("body must be an object"))
    if "briefing" in payload:
        try:
            return RecomputeRequest.model_validate(payload)
        except ValidationError as exc:
            raise RequestValidationError(exc.errors()) from exc
    try:
        briefing = AssessmentResponse.model_validate(payload)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc
    return request_from_briefing(briefing)


def _body_error(message: str) -> list[dict[str, object]]:
    return [{"type": "model_attributes_type", "loc": ("body",), "msg": message}]
