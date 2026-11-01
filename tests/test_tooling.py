"""Guard important judge-tool boundaries without external providers or credentials."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from commerce.settings import Settings

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


smoke = load_script("smoke_demo")
submission = load_script("check_submission")


class RecordingClient:
    def __init__(self, mode="rehearsal", ai_mode="local"):
        self.config = {"mode": mode, "ai_mode": ai_mode, "csrf_token": "test-session-token"}
        self.calls = []

    def request(self, method, path, data=None):
        self.calls.append((method, path))
        if path == "/api/config":
            return self.config
        if path == "/api/catalog":
            return {"items": [{"id": "desk", "price_cents": 1000}]}
        if path in {"/api/plans", "/api/plans/plan/revise"}:
            return {"id": "plan", "ai_source": self.config["ai_mode"], "budget_cents": 30000,
                    "total_cents": 1000, "remaining_cents": 29000,
                    "items": [{"product_id": "desk", "quantity": 1,
                               "unit_price_cents": 1000, "line_total_cents": 1000}]}
        if method == "POST" and path == "/api/orders":
            return {"id": "order", "mode": "rehearsal", "status": "CREATED", "total_cents": 1000}
        if path == "/api/orders/order/capture":
            return {"id": "order", "mode": "rehearsal", "status": "SIMULATED", "total_cents": 1000}
        if method == "GET" and path == "/api/orders":
            return {"orders": [{"id": "order", "status": "SIMULATED"}]}
        raise AssertionError("Unexpected tool request")


class JudgeToolTests(unittest.TestCase):
    def test_smoke_refuses_sandbox_before_any_mutation_even_with_provider_opt_in(self):
        client = RecordingClient(mode="sandbox", ai_mode="provider")
        with self.assertRaises(smoke.SmokeFailure):
            smoke.run_smoke("http://127.0.0.1:8000", allow_provider=True, client=client)
        self.assertEqual(client.calls, [("GET", "/api/config")])

    def test_smoke_refuses_paid_ai_without_explicit_opt_in(self):
        client = RecordingClient(ai_mode="provider")
        with self.assertRaises(smoke.SmokeFailure):
            smoke.run_smoke("http://127.0.0.1:8000", client=client)
        self.assertEqual(client.calls, [("GET", "/api/config")])

    def test_smoke_checks_rehearsal_receipt_and_authoritative_prices(self):
        client = RecordingClient()
        self.assertEqual(smoke.run_smoke("http://127.0.0.1:8000", client=client)["payment_status"], "SIMULATED")
        altered = {"items": [{"product_id": "desk", "quantity": 1, "unit_price_cents": 1, "line_total_cents": 1}],
                   "budget_cents": 30000, "total_cents": 1, "remaining_cents": 29999}
        with self.assertRaises(smoke.SmokeFailure):
            smoke.validate_plan(altered, {"desk": {"price_cents": 1000}})

    def test_smoke_rejects_untrusted_origin_before_network(self):
        for origin in ("http://public.example", "https://user:secret@example.com", "https://example.com/path", "https://example.com?token=private", "http://[::1"):
            with self.assertRaises(smoke.SmokeFailure):
                smoke.validate_origin(origin)

    def test_submission_check_does_not_call_local_rehearsal_eligible(self):
        issues = submission.configuration_issues(Settings())
        self.assertTrue(any("PAYMENT_MODE=sandbox" in issue for issue in issues))
        self.assertTrue(any("AI_MODE=provider" in issue for issue in issues))
        configured = Settings(payment_mode="sandbox", ai_mode="provider", paypal_client_id="fake-id",
                              paypal_client_secret="fake-secret", ai_api_key="fake-key", ai_model="model")
        self.assertEqual(submission.configuration_issues(configured), [])

    def test_configuration_errors_never_echo_secret_values(self):
        secret = "private-key-never-print"
        settings = Settings(payment_mode=secret, ai_api_key=secret, paypal_client_secret=secret)
        rendered = " ".join(submission.configuration_issues(settings))
        self.assertNotIn(secret, rendered)

    @unittest.skipUnless(shutil.which("node"), "Node is needed only to execute the supplied Postman guards")
    def test_postman_guards_block_default_sandbox_and_consume_manual_capture_opt_in(self):
        collection = json.loads((ROOT / "postman/trace-commerce.postman_collection.json").read_text())
        rehearsal = next(folder for folder in collection["item"] if folder["name"] == "Rehearsal smoke")
        manual = next(folder for folder in collection["item"] if folder["name"].startswith("03 Manual"))
        mutations = [item for folder in (rehearsal, manual) for item in folder["item"] if item["request"]["method"] == "POST"]
        cases = []
        for item in mutations:
            guard = next(event["script"]["exec"] for event in item["event"] if event["listen"] == "prerequest")
            cases.append({"code": "\n".join(guard), "variables": {"payment_mode": "sandbox", "ai_mode": "provider", "csrf_token": "csrf", "plan_id": "plan", "order_id": "order", "order_mode": "sandbox"}, "skip": True})
        capture = next(item for item in manual["item"] if "/capture" in item["request"]["url"]["raw"])
        code = "\n".join(next(event["script"]["exec"] for event in capture["event"] if event["listen"] == "prerequest"))
        for approved_id, should_skip in (("wrong-order", True), ("order", False)):
            cases.append({"code": code, "variables": {"payment_mode": "sandbox", "ai_mode": "provider", "csrf_token": "csrf", "order_id": "order", "order_mode": "sandbox", "manual_action": "capture_approved_sandbox_order", "buyer_approved_order_id": approved_id}, "skip": should_skip, "consumed": True})
        javascript = r"""
const fs = require('node:fs'); const vm = require('node:vm');
const cases = JSON.parse(fs.readFileSync(0,'utf8'));
for (const test of cases) {
  let skipped = false; const vars = {...test.variables};
  const pm = {collectionVariables:{get:k=>vars[k],unset:k=>{delete vars[k];}},execution:{skipRequest:()=>{skipped=true;throw new Error('SKIPPED');}}};
  try { vm.runInNewContext(test.code,{pm,console:{warn:()=>{}}}); } catch(e) { if(e.message!=='SKIPPED') throw e; }
  if (skipped !== test.skip) throw new Error('Unexpected guard result');
  if (test.consumed && ('manual_action' in vars || 'buyer_approved_order_id' in vars)) throw new Error('Confirmation was not consumed');
}
"""
        result = subprocess.run(["node", "-e", javascript], input=json.dumps(cases), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        # Newman can reuse lexical scope between scripts; catch duplicate const
        # declarations across the collection's scripts, not just within one event.
        scripts = []
        def collect(node):
            scripts.extend("\n".join(event["script"]["exec"]) for event in node.get("event", []))
            for child in node.get("item", []):
                collect(child)
        collect(collection)
        compiled = subprocess.run(["node", "--check"], input="\n".join(scripts), text=True, capture_output=True)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)


if __name__ == "__main__":
    unittest.main()
