"""Shared Claude client, model choice and mock switch."""
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "contracts" / "examples"


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-5-5")
# Step A (extraction) and step B (reasoning) can use different models; both fall back to MODEL.
MODEL_EXTRACT = os.getenv("MODEL_EXTRACT", MODEL)
MODEL_REASON = os.getenv("MODEL_REASON", MODEL)
TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))
RETRIES = int(os.getenv("LLM_RETRIES", "2"))


def is_mock() -> bool:
    return os.getenv("LLM_MOCK", "0").lower() in ("1", "true", "yes")


def example(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def prompt(name: str) -> str:
    return (Path(__file__).parent / "prompts" / name).read_text(encoding="utf-8")


_client = None


def client():
    global _client
    if _client is None:
        import anthropic  # imported lazily so mock mode needs no SDK
        _client = anthropic.Anthropic(timeout=TIMEOUT_S, max_retries=0)
    return _client


def _retryable(e: Exception) -> bool:
    """Missing key, auth, permission and bad-request errors will not fix themselves."""
    status = getattr(e, "status_code", None)
    if isinstance(status, int) and 400 <= status < 500 and status not in (408, 409, 429):
        return False
    msg = str(e).lower()
    return not ("authentication" in msg or "api_key" in msg or "api key" in msg)


def parse(system: str, user: str, schema, max_tokens: int = 4000, step: str = "", model: str | None = None):
    """One structured call: returns an instance of `schema` (a Pydantic model).

    Retries transient errors (timeouts, 429, 5xx, empty output); a client error such as a missing key
    or a bad request (4xx except 408/409/429) fails at once. Logs time and tokens.
    """
    last = None
    for attempt in range(RETRIES + 1):
        t0 = time.time()
        try:
            resp = client().messages.parse(
                model=model or MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
            )
            u = getattr(resp, "usage", None)
            print(f"[llm] {step} ok in {time.time() - t0:.1f}s ({model or MODEL})"
                  + (f", tokens in/out {u.input_tokens}/{u.output_tokens}" if u else ""))
            if resp.parsed_output is None:
                stop = getattr(resp, "stop_reason", "?")
                if stop == "max_tokens":
                    max_tokens = int(max_tokens * 1.5)   # the answer was cut off: retry with more room
                raise ValueError(f"empty parsed_output (stop_reason={stop})")
            return resp.parsed_output
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"[llm] {step} attempt {attempt + 1} failed after {time.time() - t0:.1f}s: {e}")
            low = str(e).lower()
            if "json_invalid" in low or "eof while parsing" in low:
                # structured output cut off mid-JSON (18.10: a 502 after 145 s): retry with more room
                max_tokens = int(max_tokens * 1.5)
            if not _retryable(e):
                break
            if attempt < RETRIES:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"LLM step {step} failed: {last}")
