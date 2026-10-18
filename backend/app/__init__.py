"""Backend package.

The shared code lives at the repository root: contracts/ (data contracts), llm/ (steps A and B)
and engine/ (rules engine). Put the root on sys.path so `uvicorn app.main:app` from backend/
can import them.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
