"""Tool handlers. Each returns a JSON string: the useful part of meraGPT's answer, or {"error": {...}}."""
from __future__ import annotations

import json
from typing import Any

from . import client

VALID_TYPES = {"noul", "choice", "score", "boolean"}


def _out(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def _error(code: str, message: str) -> str:
    return _out({"error": {"code": code, "message": message}})


def _summary(res: dict, keep: list[str]) -> dict:
    out = {k: res[k] for k in keep if k in res}
    if "usage" in res:
        out["usage"] = res["usage"]
    if "balance_usd" in res:
        out["balance_usd"] = res["balance_usd"]
    return out


def decide(args: dict, **kwargs) -> str:
    questions = args.get("questions")
    if "state" not in args or args.get("state") in (None, ""):
        return _error("invalid_request", "state is required: the message, conversation or object the questions are about.")
    if not isinstance(questions, dict) or not questions:
        return _error("invalid_request", "questions must be an object mapping a name to each question.")
    for name, q in questions.items():
        if not isinstance(q, dict) or q.get("type") not in VALID_TYPES or not q.get("instructions"):
            return _error("invalid_request", f"question '{name}' needs a type (noul, choice or score) and instructions.")
        if q["type"] in ("choice", "score") and not q.get("criteria"):
            return _error("invalid_request", f"question '{name}' is a {q['type']} and needs criteria.")
    res = client.post("/systemone", {"model": "decider-1", "state": args["state"], "questions": questions},
                      **kwargs.get("_client", {}))
    if "error" in res:
        return _out(res)
    return _out(_summary(res, ["model", "answers"]))


def restyle(args: dict, **kwargs) -> str:
    text = args.get("text")
    if not isinstance(text, str) or not text.strip():
        return _error("invalid_request", "text is required.")
    body = {"model": "restyler-1", "text": text}
    if args.get("mode") == "strict":
        body["mode"] = "strict"
    res = client.post("/restyle", body, **kwargs.get("_client", {}))
    if "error" in res:
        return _out(res)
    return _out(_summary(res, ["model", "text", "blocks", "rewritten", "total"]))


def fanout(args: dict, **kwargs) -> str:
    question = args.get("question")
    if not isinstance(question, str) or not question.strip():
        return _error("invalid_request", "question is required.")
    body: dict = {"model": "fanout-1", "question": question}
    if isinstance(args.get("category"), str) and args["category"].strip():
        body["category"] = args["category"].strip()
    if isinstance(args.get("brands"), list):
        brands = [b for b in args["brands"] if isinstance(b, str) and b.strip()]
        if brands:
            body["brands"] = brands
    res = client.post("/fanout", body, **kwargs.get("_client", {}))
    if "error" in res:
        return _out(res)
    return _out(_summary(res, ["model", "question", "queries"]))
