"""A small HTTP client for the meraGPT API (https://meragpt.com/docs), standard library only.

Every call sends the user's own API key as a bearer token. The key comes from Hermes's secret scope
(declared as MERAGPT_API_KEY in plugin.yaml) and is never logged, returned or written anywhere.
Errors come back in an OpenAI-style envelope, {"error": {"type", "code", "message"}}, and are turned
into a short dict the tool returns to the agent. Nothing here retries: a 429 is surfaced with its
Retry-After so the agent (or the person) decides whether to wait.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

API_BASE = "https://meragpt.com/v1"
TIMEOUT_S = 60
USER_AGENT = "meragpt-hermes-plugin/0.1.0"


def _default_key() -> Optional[str]:
    from agent.secret_scope import get_secret

    return get_secret("MERAGPT_API_KEY")


def post(path: str, body: dict, *, key_fn: Callable[[], Optional[str]] = _default_key,
         opener: Callable[..., Any] = urllib.request.urlopen, timeout: float = TIMEOUT_S) -> dict:
    """POST JSON to the meraGPT API. Returns the parsed body, or {"error": {...}} on any failure."""
    key = key_fn()
    if not key:
        return {"error": {"code": "missing_api_key",
                          "message": "MERAGPT_API_KEY is not set. Create a key at https://meragpt.com/dashboard/keys "
                                     "and add it as the MERAGPT_API_KEY secret in Hermes."}}
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "Accept": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with opener(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": _http_error(e)}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        return {"error": {"code": "network_error", "message": f"Could not reach meragpt.com: {reason}"}}
    except ValueError:
        return {"error": {"code": "bad_response", "message": "meragpt.com returned a response that is not JSON."}}


def _http_error(e: "urllib.error.HTTPError") -> dict:
    try:
        payload = json.loads(e.read().decode("utf-8"))
        err = payload.get("error", payload) if isinstance(payload, dict) else {}
    except Exception:
        err = {}
    out = {
        "status": e.code,
        "code": err.get("code") or err.get("type") or f"http_{e.code}",
        "message": err.get("message") or f"meragpt.com answered HTTP {e.code}.",
    }
    retry_after = e.headers.get("Retry-After") if e.headers else None
    if retry_after:
        out["retry_after_seconds"] = retry_after
    if e.code == 401:
        out["hint"] = "The API key was refused. Check MERAGPT_API_KEY."
    elif e.code == 402:
        out["hint"] = "The meraGPT account is out of credit. Top up at https://meragpt.com/dashboard/credits."
    elif e.code == 429:
        out["hint"] = "meraGPT is busy or starting capacity. Wait for retry_after_seconds before trying again; do not retry in a loop."
    return out
