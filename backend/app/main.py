"""Application entrypoint.

This module wires the FastAPI app. Routes, the pipeline, and the HTTP
client live in their own modules. Startup here is logging, the shared
HTTP client, and the integration error response.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.ai.client import create_http_client
from app.api.assessments import router as assessments_router
from app.config import get_settings
from app.logging import add_request_logging, configure_logging
from app.pipeline.errors import EditError, IntegrationError
from app.schemas.errors import ErrorBody, ErrorResponse



def create_app() -> FastAPI:
    """Build the app from the current settings.

    A factory keeps construction in one place. Tests and uvicorn both
    import the module-level `app` created below.
    """
    settings = get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # One client for the whole process. Routes borrow it through get_http_client.
        app.state.http_client = create_http_client(settings)
        yield
        await app.state.http_client.aclose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    add_request_logging(app)
    app.add_exception_handler(IntegrationError, integration_error_response)
    app.add_exception_handler(RequestValidationError, validation_error_response)
    app.add_exception_handler(EditError, edit_error_response)

    app.include_router(assessments_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Report that the API process is up. Used by local checks and deploy."""
        return {"status": "ok"}

    return app


def integration_error_response(request: Request, exc: IntegrationError) -> JSONResponse:
    """Return the shared error envelope. The message is the exception text, not a traceback."""
    return JSONResponse(
        status_code=exc.status,
        content=_error_body(exc.code, exc.message, ""),
    )


def validation_error_response(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return the shared error envelope instead of FastAPI's detail list."""
    details = "; ".join(_validation_detail(error) for error in exc.errors())
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", "The request is invalid.", details),
    )


def edit_error_response(request: Request, exc: EditError) -> JSONResponse:
    """An edit or answer with a value the feature does not allow."""
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", "The edit is invalid.", str(exc)),
    )


def _error_body(code: str, message: str, details: str) -> dict[str, dict[str, str]]:
    return ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details)
    ).model_dump()


def _validation_detail(error: dict) -> str:
    field = ".".join(str(part) for part in error.get("loc", ()) if part != "body") or "body"
    ctx = error.get("ctx") or {}
    if "min_length" in ctx:
        return f"{field}: min_length={ctx['min_length']}"
    if "max_length" in ctx:
        return f"{field}: max_length={ctx['max_length']}"
    return f"{field}: {error.get('type', 'invalid')}"


# uvicorn app.main:app
app = create_app()
