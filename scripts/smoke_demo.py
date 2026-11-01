"""Exercise a running rehearsal build without using a browser or shared cookies."""
import argparse
from http.cookiejar import CookieJar
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, quote
from urllib.request import HTTPRedirectHandler, HTTPCookieProcessor, Request, build_opener


class SmokeFailure(Exception):
    pass


def validate_origin(value):
    try:
        parsed = urlparse(value)
    except ValueError:
        raise SmokeFailure("Use a valid application origin without credentials.") from None
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if (not parsed.hostname or parsed.username or parsed.password or parsed.query
            or parsed.fragment or parsed.path not in {"", "/"}
            or (parsed.scheme != "https" and not (local and parsed.scheme == "http"))):
        raise SmokeFailure("Use an HTTPS origin, or HTTP on localhost, without a path or credentials.")
    return value.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self, base_url):
        self.base_url = validate_origin(base_url)
        self.opener = build_opener(NoRedirect, HTTPCookieProcessor(CookieJar()))
        self.csrf = ""

    def request(self, method, path, data=None):
        headers = {"Accept": "application/json"}
        encoded = None
        if method == "POST":
            headers.update({"Content-Type": "application/json", "X-CSRF-Token": self.csrf,
                            "Origin": self.base_url})
            encoded = json.dumps(data or {}).encode("utf-8")
        request = Request(self.base_url + path, data=encoded, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=55) as response:
                raw = response.read(1048577)
                if len(raw) > 1048576:
                    raise SmokeFailure("The application response exceeded the smoke-check size limit.")
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError()
        except HTTPError as error:
            raise SmokeFailure("Application returned HTTP %s for %s. Check its configuration and session origin." % (error.code, path)) from None
        except (URLError, OSError, ValueError):
            raise SmokeFailure("Could not obtain a valid application response. Check the URL and running service.") from None
        if path == "/api/config":
            self.csrf = result.get("csrf_token", "")
        return result


def validate_plan(plan, products):
    try:
        items = plan["items"]
        if not isinstance(items, list) or not items:
            raise ValueError()
        calculated = 0
        seen = set()
        for item in items:
            product_id, quantity = item["product_id"], item["quantity"]
            if product_id in seen or type(quantity) is not int or not 1 <= quantity <= 5:
                raise ValueError()
            seen.add(product_id)
            price = products[product_id]["price_cents"]
            if type(price) is not int or price <= 0:
                raise ValueError()
            if item["unit_price_cents"] != price or item["line_total_cents"] != price * quantity:
                raise ValueError()
            calculated += price * quantity
        if (plan["total_cents"] != calculated or calculated > plan["budget_cents"]
                or plan["remaining_cents"] != plan["budget_cents"] - calculated):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise SmokeFailure("The returned plan did not match catalog prices or its budget.") from None


def run_smoke(base_url, allow_provider=False, client=None):
    base_url = validate_origin(base_url)
    client = client or Client(base_url)
    config = client.request("GET", "/api/config")
    # Refuse before any POST: a smoke test is never approval to capture PayPal.
    if config.get("mode") != "rehearsal":
        raise SmokeFailure("Refused: smoke_demo only runs PAYMENT_MODE=rehearsal; it never captures PayPal sandbox orders.")
    if config.get("ai_mode") not in {"local", "provider"}:
        raise SmokeFailure("Refused: the application returned an unknown planner mode.")
    if config.get("ai_mode") == "provider" and not allow_provider:
        raise SmokeFailure("Refused: provider mode uses AI credits. Pass --allow-provider only to request one real AI plan.")
    if not isinstance(config.get("csrf_token"), str) or not config["csrf_token"]:
        raise SmokeFailure("The application did not establish a usable CSRF session.")
    catalog = client.request("GET", "/api/catalog")
    products = {item["id"]: item for item in catalog.get("items", [])}
    if not products:
        raise SmokeFailure("The catalog is empty.")
    plan = client.request("POST", "/api/plans", {
        "prompt": "Build a calm home office for video calls under $300", "budget_cents": 30000,
    })
    expected_source = "provider" if config["ai_mode"] == "provider" else "local"
    if plan.get("ai_source") != expected_source:
        raise SmokeFailure("The plan did not identify its actual planner mode.")
    if plan.get("budget_cents") != 30000:
        raise SmokeFailure("The plan did not retain the requested $300 budget.")
    validate_plan(plan, products)
    plan = client.request("POST", "/api/plans/" + quote(str(plan["id"]), safe="") + "/revise", {
        "items": [{"product_id": item["product_id"], "quantity": item["quantity"]} for item in plan["items"]],
    })
    validate_plan(plan, products)
    order = client.request("POST", "/api/orders", {"plan_id": plan["id"]})
    if (order.get("mode") != "rehearsal" or order.get("status") != "CREATED"
            or order.get("total_cents") != plan["total_cents"]):
        raise SmokeFailure("Refused capture: the server did not create the expected rehearsal order.")
    receipt = client.request("POST", "/api/orders/" + quote(str(order["id"]), safe="") + "/capture", {})
    if (receipt.get("status") != "SIMULATED" or receipt.get("mode") != "rehearsal"
            or receipt.get("total_cents") != plan["total_cents"]):
        raise SmokeFailure("The rehearsal did not return a clearly labeled simulated receipt.")
    history = client.request("GET", "/api/orders")
    if not any(item.get("id") == receipt["id"] and item.get("status") == "SIMULATED" for item in history.get("orders", [])):
        raise SmokeFailure("The receipt was not available in its own session history.")
    return {"planner": config["ai_mode"], "products": len(plan["items"]),
            "total_cents": plan["total_cents"], "payment_status": "SIMULATED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--allow-provider", action="store_true", help="Permit one real provider request using AI credits; payments must still be rehearsal.")
    args = parser.parse_args(argv)
    try:
        result = run_smoke(args.base_url, args.allow_provider)
    except SmokeFailure as error:
        print("SMOKE CHECK FAILED: " + str(error))
        return 1
    print("PASS: session, catalog prices, budget, revision, order, simulated receipt and history.")
    print("Planner: %s; products: %s; total: $%.2f USD; status: SIMULATED." % (
        result["planner"], result["products"], result["total_cents"] / 100))
    print("No PayPal request or real-money payment was authorized by this check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
