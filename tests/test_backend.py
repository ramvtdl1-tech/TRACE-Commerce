"""Offline integration tests: no provider key or live network is required."""
import asyncio
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from commerce.app import create_app, verify_paypal_order, verified_capture
from commerce.providers import AIClient, ProviderError
from commerce.settings import Settings


class Browser:
    """A tiny real-ASGI browser, including cookie/CSRF session behavior."""
    def __init__(self, app):
        self.app, self.cookie, self.csrf = app, "", ""

    def request(self, method, path, data=None, headers=None):
        body = json.dumps(data).encode() if data is not None else b""
        request_headers = {"host": "localhost:8000", "content-type": "application/json"}
        if self.cookie:
            request_headers["cookie"] = self.cookie
        if method == "POST" and self.csrf:
            request_headers["x-csrf-token"] = self.csrf
        request_headers.update(headers or {})
        scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
                 "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
                 "root_path": "", "headers": [(k.encode(), v.encode()) for k, v in request_headers.items()],
                 "server": ("localhost", 8000), "client": ("127.0.0.1", 12345)}
        messages = []
        async def run():
            delivered = False
            wait = asyncio.Event()
            async def receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                await wait.wait()
                return {"type": "http.disconnect"}
            async def send(message):
                messages.append(message)
            await self.app(scope, receive, send)
        asyncio.run(run())
        start = next(m for m in messages if m["type"] == "http.response.start")
        result_headers = {k.decode(): v.decode() for k, v in start["headers"]}
        if "set-cookie" in result_headers:
            self.cookie = result_headers["set-cookie"].split(";", 1)[0]
        response_body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
        result = json.loads(response_body) if response_body and "application/json" in result_headers.get("content-type", "") else response_body
        if path == "/api/config" and start["status"] == 200:
            self.csrf = result["csrf_token"]
        return start["status"], result


class FakePayPal:
    def __init__(self):
        self.creates = self.captures = 0
        self.document = None
        self.capture_status = "COMPLETED"
        self.bad_capture_amount = False
        self.fail_capture_once = False
        self.approved = True
    def create(self, order):
        self.creates += 1
        self.document = {"id": "SANDBOX123", "status": "CREATED", "purchase_units": [{
            "custom_id": order["id"], "amount": {"currency_code": "USD", "value": "%.2f" % (order["total_cents"] / 100)}
        }], "links": [{"rel": "payer-action", "href": "https://www.sandbox.paypal.com/checkoutnow?token=SANDBOX123"}]}
        return copy.deepcopy(self.document)
    def details(self, provider_id):
        result = copy.deepcopy(self.document)
        if result["status"] != "COMPLETED":
            result["status"] = "APPROVED" if self.approved else "CREATED"
        return result
    def capture(self, order):
        self.captures += 1
        self.document["status"] = "COMPLETED"
        amount = copy.deepcopy(self.document["purchase_units"][0]["amount"])
        if self.bad_capture_amount:
            amount["value"] = "0.01"
        self.document["purchase_units"][0]["payments"] = {"captures": [{
            "id": "CAPTURE123", "status": self.capture_status, "amount": amount
        }]}
        if self.fail_capture_once:
            self.fail_capture_once = False
            raise ProviderError("The provider could not complete this request. Check the server configuration or retry shortly.")
        return copy.deepcopy(self.document)


class FakeAI:
    def __init__(self, response):
        self.response = response
    def recommend(self, prompt, budget, catalog):
        return self.response


class CommerceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Settings(database_path=str(Path(self.temp.name) / "test.db"))
        self.paypal = FakePayPal()
        self.app = create_app(self.settings, paypal_client=self.paypal)
        self.browser = Browser(self.app)
        self.browser.request("GET", "/api/config")
    def tearDown(self):
        self.temp.cleanup()
    def plan(self, browser=None):
        browser = browser or self.browser
        code, result = browser.request("POST", "/api/plans", {"prompt": "A quiet coding setup", "budget_cents": 25000})
        self.assertEqual(code, 200, result)
        return result
    def checkout(self):
        plan = self.plan()
        code, order = self.browser.request("POST", "/api/orders", {"plan_id": plan["id"]})
        self.assertEqual(code, 200, order)
        return order
    def sandbox(self):
        self.settings.payment_mode = "sandbox"
        self.settings.paypal_client_id = "fake-id"
        self.settings.paypal_client_secret = "fake-secret"
    def test_local_plan_has_valid_prices_and_budget(self):
        result = self.plan()
        _, catalog = self.browser.request("GET", "/api/catalog")
        prices = {p["id"]: p["price_cents"] for p in catalog["items"]}
        self.assertLessEqual(result["total_cents"], 25000)
        self.assertEqual(result["total_cents"], sum(prices[x["product_id"]] * x["quantity"] for x in result["items"]))
        self.assertEqual(result["ai_source"], "local")
    def test_csrf_and_cross_origin_protection(self):
        for headers in ({"x-csrf-token": "wrong"}, {"origin": "https://evil.example"}):
            code, _ = self.browser.request("POST", "/api/plans", {"prompt": "desk setup", "budget_cents": 20000}, headers)
            self.assertEqual(code, 403)
    def test_browser_sessions_cannot_read_or_capture_other_orders(self):
        order = self.checkout()
        other = Browser(self.app)
        other.request("GET", "/api/config")
        self.assertEqual(other.request("GET", "/api/orders")[1]["orders"], [])
        self.assertEqual(other.request("POST", "/api/orders/" + order["id"] + "/capture", {})[0], 404)
        self.assertEqual(other.request("POST", "/api/orders", {"plan_id": order["plan_id"]})[0], 404)
    def test_price_injection_and_overbudget_revisions_fail(self):
        plan = self.plan()
        response = self.browser.request("POST", "/api/plans/" + plan["id"] + "/revise", {
            "items": [{"product_id": "focus-monitor", "quantity": 1, "price_cents": 1}]})
        self.assertEqual(response[0], 422)
        response = self.browser.request("POST", "/api/plans/" + plan["id"] + "/revise", {
            "items": [{"product_id": "flow-chair", "quantity": 5}]})
        self.assertEqual(response[0], 422)
    def test_rehearsal_is_explicit_and_idempotent(self):
        order = self.checkout()
        again = self.browser.request("POST", "/api/orders", {"plan_id": order["plan_id"]})[1]
        self.assertEqual(order["id"], again["id"])
        first = self.browser.request("POST", "/api/orders/" + order["id"] + "/capture", {})[1]
        second = self.browser.request("POST", "/api/orders/" + order["id"] + "/capture", {})[1]
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "SIMULATED")
        self.assertEqual(self.paypal.creates, 0)
    def test_sandbox_requires_approval_and_captures_once(self):
        self.sandbox()
        order = self.checkout()
        self.paypal.approved = False
        path = "/api/orders/" + order["id"] + "/capture"
        self.assertEqual(self.browser.request("POST", path, {})[0], 409)
        self.paypal.approved = True
        code, receipt = self.browser.request("POST", path, {})
        self.assertEqual(code, 200, receipt)
        self.assertEqual(receipt["status"], "COMPLETED")
        self.browser.request("POST", path, {})
        self.assertEqual(self.paypal.captures, 1)
        self.assertEqual(self.paypal.creates, 1)
    def test_capture_amount_mismatch_never_fulfills(self):
        self.sandbox()
        order = self.checkout()
        self.paypal.bad_capture_amount = True
        self.assertEqual(self.browser.request("POST", "/api/orders/" + order["id"] + "/capture", {})[0], 502)
        self.assertNotEqual(self.browser.request("GET", "/api/orders")[1]["orders"][0]["status"], "COMPLETED")
    def test_pending_capture_is_not_completed(self):
        self.sandbox()
        order = self.checkout()
        self.paypal.capture_status = "PENDING"
        result = self.browser.request("POST", "/api/orders/" + order["id"] + "/capture", {})[1]
        self.assertEqual(result["status"], "PENDING")
        self.assertNotIn("captured_at", result)
    def test_uncertain_capture_recovers_without_second_capture(self):
        self.sandbox()
        order = self.checkout()
        self.paypal.fail_capture_once = True
        path = "/api/orders/" + order["id"] + "/capture"
        self.assertEqual(self.browser.request("POST", path, {})[0], 502)
        code, result = self.browser.request("POST", path, {})
        self.assertEqual(code, 200, result)
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(self.paypal.captures, 1)
    def test_ai_cannot_invent_catalog_products_or_exceed_budget(self):
        for response in (
            {"summary": "Try this", "items": [{"product_id": "invented", "quantity": 1}]},
            {"summary": "Try this", "items": [{"product_id": "flow-chair", "quantity": 5}]},
        ):
            app = create_app(Settings(database_path=str(Path(self.temp.name) / "provider.db"), ai_mode="provider", ai_api_key="fake", ai_model="fake"),
                             ai_client=FakeAI(response))
            browser = Browser(app)
            browser.request("GET", "/api/config")
            code, result = browser.request("POST", "/api/plans", {"prompt": "a coding desk", "budget_cents": 20000})
            self.assertEqual(code, 502, result)
    def test_persistent_rate_limit_and_health(self):
        self.settings.ai_session_limit = 1
        self.plan()
        code, _ = self.browser.request("POST", "/api/plans", {"prompt": "another setup", "budget_cents": 20000})
        self.assertEqual(code, 429)
        self.assertEqual(self.browser.request("GET", "/healthz")[0], 200)
    def test_money_schema_rejects_float_and_bool(self):
        for amount in (True, 25000.0, "25000"):
            code, _ = self.browser.request("POST", "/api/plans", {"prompt": "a coding desk", "budget_cents": amount})
            self.assertEqual(code, 422)
    def test_cancelled_checkout_can_restart_but_completed_cannot_cancel(self):
        order = self.checkout()
        path = "/api/orders/" + order["id"]
        self.assertEqual(self.browser.request("POST", path + "/cancel", {})[1]["status"], "CANCELLED")
        self.assertEqual(self.browser.request("POST", "/api/orders", {"plan_id": order["plan_id"]})[1]["id"], order["id"])
        self.browser.request("POST", path + "/capture", {})
        self.assertEqual(self.browser.request("POST", path + "/cancel", {})[1]["status"], "SIMULATED")
    def test_nonfinite_or_malformed_paypal_data_fails_safely(self):
        order = {"id": "local-id", "provider_order_id": "SANDBOX123", "total_cents": 10000}
        samples = [None, [], {"id": "SANDBOX123", "purchase_units": [None]},
                   {"id": "SANDBOX123", "purchase_units": [{"amount": None}]},
                   {"id": "SANDBOX123", "purchase_units": [{"custom_id": "local-id", "amount": {"currency_code": "USD", "value": "NaN"}}]},
                   {"id": "SANDBOX123", "purchase_units": [{"custom_id": "local-id", "amount": {"currency_code": "USD", "value": "Infinity"}}]}]
        for sample in samples:
            with self.assertRaises(ProviderError):
                verify_paypal_order(sample, order)
        for payments in (None, {"captures": [None]}, {"captures": [{"id": {}, "amount": {"value": "100.00", "currency_code": "USD"}}]}):
            provider = {"id": "SANDBOX123", "status": "COMPLETED", "purchase_units": [{
                "custom_id": "local-id", "amount": {"value": "100.00", "currency_code": "USD"}, "payments": payments}]}
            with self.assertRaises(ProviderError):
                verified_capture(provider, order)

    def test_stale_cancel_and_create_cannot_overwrite_capture(self):
        order = self.checkout()
        session = self.app.state.store.session(self.browser.cookie.split("=", 1)[1], 7)[0]["id"]
        stale_cancel = dict(order, status="CANCELLED")
        stale_create = dict(order, status="CREATED")
        capturing = self.app.state.store.update_order(session, dict(order, status="CAPTURING"))
        self.assertEqual(self.app.state.store.update_order(session, stale_cancel)["status"], "CAPTURING")
        completed = self.app.state.store.update_order(session, dict(capturing, status="COMPLETED", capture_id="CAPTURE123"))
        self.assertEqual(self.app.state.store.update_order(session, stale_cancel), completed)
        self.assertEqual(self.app.state.store.update_order(session, stale_create, allow_restart=True), completed)

    def test_revisions_share_persisted_plan_quota(self):
        self.settings.ai_session_limit = 1
        plan = self.plan()
        code, _ = self.browser.request("POST", "/api/plans/" + plan["id"] + "/revise", {
            "items": [{"product_id": "quiet-keyboard", "quantity": 1}]})
        self.assertEqual(code, 429)

    def test_malformed_ai_provider_response_is_a_safe_error(self):
        client = AIClient(Settings(ai_api_key="fake", ai_model="fake"))
        for response in ({"choices": [None]}, {"choices": []}, {"choices": [{"message": None}]}, {"choices": [{"message": {"content": "not json"}}]}):
            with patch("commerce.providers.request_json", return_value=response):
                with self.assertRaises(ProviderError):
                    client.recommend("a coding desk", 20000, [])

    def test_ai_token_limit_is_configurable_and_truncation_explained(self):
        settings = Settings(ai_max_tokens=6000, ai_api_key="fake", ai_model="fake")
        response = {"choices": [{"finish_reason": "length", "message": {"content": ""}}]}
        with patch("commerce.providers.request_json", return_value=response) as transport:
            with self.assertRaisesRegex(ProviderError, "AI_MAX_TOKENS"):
                AIClient(settings).recommend("a coding desk", 20000, [])
            self.assertEqual(transport.call_args.args[2]["max_tokens"], 6000)
        with self.assertRaises(ValueError):
            Settings(ai_max_tokens=100000).validate()

    def test_minimal_create_response_uses_authoritative_details(self):
        self.sandbox()
        self.paypal.approved = False
        original = self.paypal.create
        def minimal(order):
            result = original(order)
            return {"id": result["id"], "links": result["links"]}
        with patch.object(self.paypal, "create", side_effect=minimal):
            order = self.checkout()
        self.assertEqual(order["status"], "CREATED")
        self.assertEqual(order["provider_order_id"], "SANDBOX123")
        self.assertTrue(order["approval_url"].startswith("https://www.sandbox.paypal.com/"))

    def test_create_details_timeout_retains_reference_and_retry_does_not_recreate(self):
        self.sandbox()
        self.paypal.approved = False
        plan = self.plan()
        with patch.object(self.paypal, "details", side_effect=ProviderError("Temporary provider failure.")):
            code, _ = self.browser.request("POST", "/api/orders", {"plan_id": plan["id"]})
        self.assertEqual(code, 502)
        stored = self.browser.request("GET", "/api/orders")[1]["orders"][0]
        self.assertEqual(stored["provider_order_id"], "SANDBOX123")
        self.assertIsNone(stored["approval_url"])
        code, recovered = self.browser.request("POST", "/api/orders", {"plan_id": plan["id"]})
        self.assertEqual(code, 200, recovered)
        self.assertEqual(recovered["id"], stored["id"])
        self.assertEqual(recovered["status"], "CREATED")
        self.assertEqual(self.paypal.creates, 1)

    def test_create_can_recover_approval_link_from_get_details(self):
        self.sandbox()
        self.paypal.approved = False
        original = self.paypal.create
        def minimal(order):
            result = original(order)
            return {"id": result["id"], "links": None}
        with patch.object(self.paypal, "create", side_effect=minimal):
            order = self.checkout()
        self.assertEqual(order["status"], "CREATED")
        self.assertTrue(order["approval_url"])

    def test_create_can_recover_retained_candidate_when_get_omits_links(self):
        self.sandbox()
        self.paypal.approved = False
        plan = self.plan()
        with patch.object(self.paypal, "details", side_effect=ProviderError("Temporary provider failure.")):
            self.browser.request("POST", "/api/orders", {"plan_id": plan["id"]})
        self.paypal.document["links"] = []
        code, recovered = self.browser.request("POST", "/api/orders", {"plan_id": plan["id"]})
        self.assertEqual(code, 200, recovered)
        self.assertTrue(recovered["approval_url"])
        self.assertEqual(self.paypal.creates, 1)

    def test_revision_removes_stale_original_explanations(self):
        plan = self.plan()
        code, revised = self.browser.request("POST", "/api/plans/" + plan["id"] + "/revise", {
            "items": [{"product_id": "quiet-keyboard", "quantity": 1}]})
        self.assertEqual(code, 200, revised)
        self.assertEqual(revised["total_cents"], 4900)
        self.assertNotEqual(plan["tradeoffs"], revised["tradeoffs"])
        self.assertIn("You changed this setup", revised["tradeoffs"][0])

    def test_public_config_names_integrations_without_revealing_credentials(self):
        self.settings.ai_mode = "provider"
        self.settings.ai_api_key = "private-ai-credential"
        self.settings.ai_model = "catalog-model-v1"
        self.settings.ai_base_url = "https://api.tokenfactory.nebius.com/v1"
        self.sandbox()
        self.settings.paypal_client_secret = "private-paypal-credential"
        code, config = self.browser.request("GET", "/api/config")
        self.assertEqual(code, 200)
        self.assertEqual(config["project_version"], "2.0.0")
        self.assertEqual(config["ai_provider"], "Nebius Token Factory")
        self.assertEqual(config["ai_model"], "catalog-model-v1")
        self.assertTrue(config["integration_modes_enabled"])
        public_json = json.dumps(config)
        for private_value in (self.settings.ai_api_key, self.settings.paypal_client_id,
                              self.settings.paypal_client_secret, self.settings.ai_base_url):
            self.assertNotIn(private_value, public_json)
        self.settings.payment_mode = "rehearsal"
        config = self.browser.request("GET", "/api/config")[1]
        self.assertFalse(config["integration_modes_enabled"])

    def test_local_planner_never_claims_configured_model_ran(self):
        self.settings.ai_api_key = "private-unused-ai-key"
        self.settings.ai_model = "unused-model"
        config = self.browser.request("GET", "/api/config")[1]
        self.assertEqual(config["ai_provider"], "Local rehearsal planner")
        self.assertIsNone(config["ai_model"])
        self.assertFalse(config["integration_modes_enabled"])
        plan = self.plan()
        self.assertEqual(plan["ai_provider"], "Local rehearsal planner")
        self.assertIsNone(plan["ai_model"])

    def test_provider_provenance_survives_revision_configuration_change_and_receipt(self):
        settings = Settings(database_path=str(Path(self.temp.name) / "provenance.db"),
                            ai_mode="provider", ai_api_key="private-key", ai_model="original-model")
        ai = FakeAI({"summary": "A quiet keyboard", "items": [{"product_id": "quiet-keyboard", "quantity": 1}]})
        browser = Browser(create_app(settings, ai_client=ai))
        browser.request("GET", "/api/config")
        code, plan = browser.request("POST", "/api/plans", {"prompt": "a quiet desk setup", "budget_cents": 30000})
        self.assertEqual(code, 200, plan)
        self.assertEqual(plan["ai_provider"], "Nebius Token Factory")
        self.assertEqual(plan["ai_model"], "original-model")
        settings.ai_model = "different-current-model"
        settings.ai_base_url = "https://new-provider.example/v1"
        code, revised = browser.request("POST", "/api/plans/" + plan["id"] + "/revise", {
            "items": [{"product_id": "quiet-keyboard", "quantity": 2}]})
        self.assertEqual(code, 200, revised)
        self.assertEqual(revised["ai_model"], "original-model")
        self.assertEqual(revised["ai_provider"], "Nebius Token Factory")
        code, order = browser.request("POST", "/api/orders", {"plan_id": revised["id"]})
        self.assertEqual(code, 200, order)
        code, receipt = browser.request("POST", "/api/orders/" + order["id"] + "/capture", {})
        self.assertEqual(code, 200, receipt)
        self.assertEqual(receipt["ai_source"], "provider")
        self.assertEqual(receipt["ai_provider"], "Nebius Token Factory")
        self.assertEqual(receipt["ai_model"], "original-model")
        self.assertEqual(receipt["budget_cents"], 30000)
        self.assertEqual(receipt["status"], "SIMULATED")

    def test_custom_provider_and_legacy_plan_identity_are_not_invented(self):
        custom = Settings(ai_mode="provider", ai_api_key="private", ai_model="custom-model",
                          ai_base_url="https://private-service.example/v1")
        self.assertEqual(custom.planner_identity(), {"ai_provider": "Configured AI provider", "ai_model": "custom-model"})
        plan = self.plan()
        session = self.app.state.store.session(self.browser.cookie.split("=", 1)[1], 7)[0]["id"]
        legacy = dict(plan, id="legacy-provider-plan", ai_source="provider")
        legacy.pop("ai_provider")
        legacy.pop("ai_model")
        self.app.state.store.put_plan(session, legacy)
        code, revised = self.browser.request("POST", "/api/plans/" + legacy["id"] + "/revise", {
            "items": [{"product_id": "quiet-keyboard", "quantity": 1}]})
        self.assertEqual(code, 200, revised)
        self.assertEqual(revised["ai_provider"], "AI provider (not recorded)")
        self.assertIsNone(revised["ai_model"])

    def test_live_payments_and_insecure_deployments_rejected(self):
        with self.assertRaises(ValueError):
            Settings(payment_mode="live").validate()
        with self.assertRaises(ValueError):
            Settings(public_base_url="http://demo.example").validate()
        with self.assertRaises(ValueError):
            Settings(payment_mode="sandbox").validate()


if __name__ == "__main__":
    unittest.main()
