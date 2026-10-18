import httpx
from fastapi import Request

from app.config import Settings


def create_http_client(settings: Settings) -> httpx.AsyncClient:
    """Build the process-wide client used for the AI component.

    The caller owns the client and closes it on shutdown. No request is sent here.
    """
    timeout = httpx.Timeout(settings.ai_timeout_seconds)
    if settings.ai_base_url is None:
        return httpx.AsyncClient(timeout=timeout)
    return httpx.AsyncClient(base_url=str(settings.ai_base_url), timeout=timeout)


# On boot, create_app stores that client on app.state.http_client. 
# This function takes the current request, walks up to the app, and returns that same client. 
# This is used to send requests to the AI component.
def get_http_client(request: Request) -> httpx.AsyncClient:
    """Return the client opened during application startup."""
    return request.app.state.http_client


class AIClient:
    """Placeholder for the AI component client. Not called yet."""
