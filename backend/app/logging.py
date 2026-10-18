# HTTP request logging middleware: records method, path, status code, duration,
# and exceptions for every incoming request without logging request bodies.
import logging
import time

from fastapi import FastAPI, Request

REQUEST_LOGGER_NAME = "app.request"


def configure_logging(level: str) -> None:
    """Send application logs to stderr. Safe to call more than once."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("app").setLevel(level)


def add_request_logging(app: FastAPI) -> None:
    """Log method, path, status, and duration for every request.

    Bodies stay out of the log. Customer use-case text can be logged later
    at debug level if a demo needs it.
    """
    logger = logging.getLogger(REQUEST_LOGGER_NAME)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "%s %s failed after %.0fms",
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "%s %s %s %.0fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
