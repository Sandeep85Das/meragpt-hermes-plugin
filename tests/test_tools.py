"""Offline tests: request shapes, response trimming and error handling, with HTTP mocked. No network."""
import importlib.util
import io
import json
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_package():
    spec = importlib.util.spec_from_file_location("meragpt", ROOT / "__init__.py", submodule_search_locations=[str(ROOT)])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["meragpt"] = mod
    spec.loader.exec_module(mod)
    return mod


pkg = _load_package()
from meragpt import tools  # noqa: E402


class FakeResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class Recorder:
    """A urlopen stand-in that records the request and answers with a body or an HTTPError."""

    def __init__(self, body=None, status=None, headers=None):
        self.body, self.status, self.headers, self.request = body, status, headers or {}, None

    def __call__(self, req, timeout=None):
        self.request = req
        if self.status:
            msg = Message()
            for k, v in self.headers.items():
                msg[k] = v
            raise urllib.error.HTTPError(req.full_url, self.status, "err", msg, io.BytesIO(json.dumps(self.body or {}).encode()))
        return FakeResponse(self.body)

    def sent(self):
        return json.loads(self.request.data.decode())


def kw(opener, key="test-key"):
    return {"_client": {"key_fn": lambda: key, "opener": opener}}


class DecideTests(unittest.TestCase):
    QUESTIONS = {
        "team": {"type": "choice", "instructions": "Which team?", "criteria": {"billing": "Money", "technical": "Bugs"}},
        "refund": {"type": "noul", "instructions": "Refund asked?"},
    }

    def test_request_shape_and_answer(self):
        r = Recorder({"model": "decider-1", "answers": {"team": {"type": "choice", "choice": "technical", "confidence": 0.9}},
                      "usage": {"input_tokens": 50}, "balance_usd": "$0.99", "id": "req_x"})
        out = json.loads(tools.decide({"state": "export is broken", "questions": self.QUESTIONS}, **kw(r)))
        self.assertEqual(r.request.full_url, "https://meragpt.com/v1/systemone")
        self.assertEqual(r.request.get_header("Authorization"), "Bearer test-key")
        self.assertEqual(r.sent(), {"model": "decider-1", "state": "export is broken", "questions": self.QUESTIONS})
        self.assertEqual(out["answers"]["team"]["choice"], "technical")
        self.assertNotIn("id", out)

    def test_validation(self):
        r = Recorder({})
        self.assertIn("error", json.loads(tools.decide({"questions": self.QUESTIONS}, **kw(r))))
        bad = {"x": {"type": "choice", "instructions": "Which?"}}
        self.assertIn("needs criteria", tools.decide({"state": "s", "questions": bad}, **kw(r)))
        self.assertIsNone(r.request, "invalid input must not call the API")

    def test_missing_key(self):
        r = Recorder({})
        out = json.loads(tools.decide({"state": "s", "questions": self.QUESTIONS}, **kw(r, key=None)))
        self.assertEqual(out["error"]["code"], "missing_api_key")
        self.assertIsNone(r.request)

    def test_out_of_credit(self):
        r = Recorder({"error": {"type": "billing_error", "code": "insufficient_credit", "message": "No credit."}}, status=402)
        out = json.loads(tools.decide({"state": "s", "questions": self.QUESTIONS}, **kw(r)))
        self.assertEqual(out["error"]["status"], 402)
        self.assertEqual(out["error"]["code"], "insufficient_credit")
        self.assertIn("credit", out["error"]["hint"])

    def test_capacity_429_surfaces_retry_after(self):
        r = Recorder({"error": {"code": "capacity_saturated", "message": "Starting capacity."}}, status=429, headers={"Retry-After": "10"})
        out = json.loads(tools.decide({"state": "s", "questions": self.QUESTIONS}, **kw(r)))
        self.assertEqual(out["error"]["retry_after_seconds"], "10")
        self.assertEqual(out["error"]["code"], "capacity_saturated")

    def test_key_never_returned(self):
        r = Recorder({"error": {"message": "bad key"}}, status=401)
        out = tools.decide({"state": "s", "questions": self.QUESTIONS}, **kw(r, key="sk-secret-123"))
        self.assertNotIn("sk-secret-123", out)


class RestyleTests(unittest.TestCase):
    def test_default_and_strict(self):
        r = Recorder({"model": "restyler-1", "text": "Rewritten.", "blocks": [{"index": 0, "status": "rewritten"}], "rewritten": 1, "total": 1})
        out = json.loads(tools.restyle({"text": "Draft."}, **kw(r)))
        self.assertEqual(r.sent(), {"model": "restyler-1", "text": "Draft."})
        self.assertEqual(r.request.full_url, "https://meragpt.com/v1/restyle")
        self.assertEqual(out["text"], "Rewritten.")
        tools.restyle({"text": "Draft.", "mode": "strict"}, **kw(r))
        self.assertEqual(r.sent()["mode"], "strict")

    def test_empty_text(self):
        r = Recorder({})
        self.assertIn("error", json.loads(tools.restyle({"text": "  "}, **kw(r))))
        self.assertIsNone(r.request)


class FanoutTests(unittest.TestCase):
    def test_request_with_hints(self):
        r = Recorder({"model": "fanout-1", "question": "q", "queries": ["a", "b"]})
        out = json.loads(tools.fanout({"question": "Best PM tools?", "category": " project management tools ",
                                       "brands": ["Asana", "", 3, "Linear"]}, **kw(r)))
        self.assertEqual(r.sent(), {"model": "fanout-1", "question": "Best PM tools?", "category": "project management tools",
                                    "brands": ["Asana", "Linear"]})
        self.assertEqual(out["queries"], ["a", "b"])

    def test_network_error(self):
        def boom(req, timeout=None):
            raise urllib.error.URLError("timed out")
        out = json.loads(tools.fanout({"question": "q"}, **kw(boom)))
        self.assertEqual(out["error"]["code"], "network_error")


class RegisterTests(unittest.TestCase):
    def test_registers_declared_tools_and_skill(self):
        calls, skills = [], []

        class Ctx:
            def register_tool(self, **k):
                calls.append(k["name"])

            def register_skill(self, name, path):
                skills.append(name)

        pkg.register(Ctx())
        manifest = (ROOT / "plugin.yaml").read_text()
        for name in calls:
            self.assertIn(f"- {name}", manifest)
        self.assertEqual(sorted(calls), ["meragpt_decide", "meragpt_fanout", "meragpt_restyle"])
        self.assertEqual(skills, ["meragpt-decisions"])


if __name__ == "__main__":
    unittest.main()
