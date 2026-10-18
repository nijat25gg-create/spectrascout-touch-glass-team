"""Briefing fields that C3, C5 and C7 do not supply."""
import os

from app.schemas.assessment import ExpertFlag


def expert_flags() -> list[ExpertFlag]:
    # No step produces flags yet. An empty list is honest; a demo flag would show up on screen.
    return []


def model_name() -> str:
    if os.getenv("LLM_MOCK", "1") == "1":
        return "mock"
    return os.getenv("MODEL", "claude-sonnet-5-5")


def kb_version() -> str:
    return "kb-draft-0"
