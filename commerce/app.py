import json
import re
import secrets
import sqlite3
import time
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .planner import local_recommend, make_plan
from .providers import AIClient, PayPalClient, ProviderError
from .settings import ROOT, Settings
from .store import Store, now_iso

PROJECT_VERSION = "2.0.1"


class PlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=5, max_length=2000)
    budget_cents: StrictInt = Field(ge=1200, le=500000)


class CartItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(min_length=1, max_length=80)
    quantity: StrictInt = Field(ge=1, le=5)


class RevisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: List[CartItem] = Field(min_length=1, max_length=12)


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    plan_id: str = Field(min_length=1, max_length=80)


def verify_paypal_order(provider, order):
    if not isinstance(provider, dict) or provider.get("id") != order["provider_order_id"]:
        raise ProviderError("PayPal returned an unexpected order. No receipt has been issued.")
    units = provider.get("purchase_units", [])
    if not isinstance(units, list) or len(units) != 1:
        raise ProviderError("The PayPal order could not be verified. No receipt has been issued.")
    unit = units[0]
    if not isinstance(unit, dict):
        raise ProviderError("The PayPal order could not be verified. No receipt has been issued.")
    amount = unit.get("amount", {})
    if not isinstance(amount, dict):
        raise ProviderError("The PayPal amount could not be verified. No receipt has been issued.")
    try:
        raw_value = amount.get("value", "NaN")
        if not isinstance(raw_value, str):
            raise TypeError()
        value = Decimal(raw_value)
        valid_amount = value.is_finite() and value == Decimal(order["total_cents"]) / 100
    except (InvalidOperation, TypeError):
        valid_amount = False
    if not valid_amount or amount.get("currency_code") != "USD" or unit.get("custom_id") != order["id"]:
        raise ProviderError("The PayPal amount, currency, or cart reference did not match. No receipt has been issued.")
    return unit


def verified_capture(provider, order):
    unit = verify_paypal_order(provider, order)
    payments = unit.get("payments", {})
    if not isinstance(payments, dict):
        raise ProviderError("The PayPal capture could not be verified. No receipt has been issued.")
    captures = payments.get("captures", [])
    if not isinstance(captures, list) or len(captures) != 1:
        raise ProviderError("A single verified capture is required before a receipt can be issued.")
    capture = captures[0]
    if not isinstance(capture, dict):
        raise ProviderError("The PayPal capture could not be verified. No receipt has been issued.")
    try:
        amount = capture.get("amount", {})
        if not isinstance(amount, dict):
            raise TypeError()
        raw_value = amount.get("value", "NaN")
        if not isinstance(raw_value, str):
            raise TypeError()
        value = Decimal(raw_value)
        valid = value.is_finite() and value == Decimal(order["total_cents"]) / 100
    except (InvalidOperation, TypeError):
        valid = False
    if not valid or amount.get("currency_code") != "USD" or not isinstance(capture.get("id"), str) or not re.fullmatch(r"[A-Za-z0-9]{5,64}", capture["id"]):
        raise ProviderError("The captured amount could not be verified. No receipt has been issued.")
    if capture.get("status") == "COMPLETED" and provider.get("status") == "COMPLETED":
        return "COMPLETED", capture["id"]
    if capture.get("status") == "PENDING":
        return "PENDING", capture["id"]
    raise ProviderError("PayPal has not completed this payment. No receipt has been issued.")



def trusted_approval_url(*documents):
    """Find a sandbox approval link, tolerating minimal provider responses."""
    for document in documents:
        links = document.get("links", []) if isinstance(document, dict) else []
        if not isinstance(links, list):
            continue
        for link in links:
            if not isinstance(link, dict) or link.get("rel") not in {"approve", "payer-action"}:
                continue
            candidate = link.get("href")
            if not isinstance(candidate, str):
                continue
            try:
                parsed = urlparse(candidate)
            except ValueError:
                continue
            if parsed.scheme == "https" and parsed.hostname in {"sandbox.paypal.com", "www.sandbox.paypal.com"} and not parsed.username and not parsed.password:
                return candidate
    return None


def create_app(settings=None, ai_client=None, paypal_client=None):
    settings = settings or Settings.from_env()
    settings.validate()
    store = Store(settings.database_path)
    ai = ai_client or AIClient(settings)
    paypal = paypal_client or PayPalClient(settings)
    catalog = json.loads((ROOT / "catalog.json").read_text())
    app = FastAPI(title="TRACE Commerce", version=PROJECT_VERSION, docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    app.state.settings, app.state.store = settings, store
    app.state.ai, app.state.paypal = ai, paypal

    @app.middleware("http")
    async def security(request, call_next):
        token = None
        response = None
        if request.url.path.startswith("/api/"):
            session, token = store.session(request.cookies.get("trace_session"), settings.session_days)
            request.state.session = session
            if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                allowed_origins = {settings.public_base_url.rstrip("/")}
                origin = request.headers.get("origin")
                if origin and origin not in allowed_origins:
                    response = JSONResponse({"detail": "This action must be made from this application's own page."}, status_code=403)
                csrf = request.headers.get("x-csrf-token", "")
                if not response and not secrets.compare_digest(csrf.encode("utf-8"), session["csrf"].encode("utf-8")):
                    response = JSONResponse({"detail": "Your session needs to be refreshed before continuing."}, status_code=403)
                if not response:
                    size = 0
                    parts = []
                    async for part in request.stream():
                        size += len(part)
                        if size > 16384:
                            response = JSONResponse({"detail": "Request body is too large."}, status_code=413)
                            break
                        parts.append(part)
                    if response is None:
                        request._body = b"".join(parts)
        if response is None:
            response = await call_next(request)
        if token:
            response.set_cookie("trace_session", token, max_age=settings.session_days * 86400,
                                httponly=True, secure=settings.cookie_secure, samesite="lax", path="/")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; "
            "base-uri 'self'; object-src 'none'; form-action 'self' https://www.sandbox.paypal.com https://sandbox.paypal.com"
        )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        if settings.cookie_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response

    @app.exception_handler(ProviderError)
    async def provider_failure(request, error):
        return JSONResponse({"detail": str(error)}, status_code=502)

    @app.exception_handler(sqlite3.Error)
    async def database_failure(request, error):
        return JSONResponse({"detail": "Storage is temporarily unavailable. Please retry shortly."}, status_code=503)

    def session_id(request):
        return request.state.session["id"]

    def rate_limit(request, kind):
        if kind == "ai":
            allowed = store.limit(session_id(request), kind, settings.ai_session_limit, settings.ai_global_limit)
        else:
            allowed = store.limit(session_id(request), kind, settings.payment_session_limit, settings.payment_global_limit)
        if not allowed:
            raise HTTPException(429, "The hourly demo request limit has been reached. Please try again later.", headers={"Retry-After": "3600"})

    def owned_order(request, order_id):
        order = store.get_order(session_id(request), order_id)
        if not order:
            raise HTTPException(404, "Order not found in this browser session.")
        return order

    @app.get("/healthz")
    def health():
        with store.connection() as db:
            db.execute("SELECT 1").fetchone()
        return {"status": "ok", "service": "trace-commerce"}

    @app.get("/api/config")
    def config(request: Request):
        sandbox_configured = bool(settings.paypal_client_id and settings.paypal_client_secret)
        ai_configured = bool(settings.ai_api_key and settings.ai_model)
        return {"app_name": "TRACE Commerce", "mode": settings.payment_mode, "ai_mode": settings.ai_mode,
                "csrf_token": request.state.session["csrf"], "currency": "USD",
                "project_version": PROJECT_VERSION, **settings.planner_identity(),
                "sandbox_ready": sandbox_configured, "ai_ready": ai_configured,
                # Configuration state is not proof that an external integration ran.
                "integration_modes_enabled": bool(settings.payment_mode == "sandbox" and
                                                  settings.ai_mode == "provider" and
                                                  sandbox_configured and ai_configured)}

    @app.get("/api/catalog")
    def get_catalog():
        return {"items": catalog, "currency": "USD"}

    @app.post("/api/plans")
    def plan(body: PlanRequest, request: Request):
        if not body.prompt.strip() or len(body.prompt.strip()) < 5:
            raise HTTPException(422, "Tell us a little more about the setup you need.")
        rate_limit(request, "ai")
        recommendation = ai.recommend(body.prompt, body.budget_cents, catalog) if settings.ai_mode == "provider" else local_recommend(body.prompt, body.budget_cents, catalog)
        try:
            result = make_plan(body.prompt, body.budget_cents, recommendation, catalog,
                               "provider" if settings.ai_mode == "provider" else "local")
        except ValueError as error:
            if settings.ai_mode == "provider":
                raise ProviderError("The AI recommendation did not pass catalog and budget checks. Try a different request.") from None
            raise HTTPException(422, str(error)) from None
        result.update(settings.planner_identity())
        store.put_plan(session_id(request), result)
        return result

    @app.post("/api/plans/{plan_id}/revise")
    def revise(plan_id: str, body: RevisionRequest, request: Request):
        current = store.get_plan(session_id(request), plan_id)
        if not current:
            raise HTTPException(404, "Plan not found in this browser session.")
        rate_limit(request, "ai")
        recommendation = {"items": [dict(item.model_dump(), reason="Reviewed and selected by you.") for item in body.items],
                          "summary": "Your reviewed setup, with catalog prices rechecked by the server.",
                          "tradeoffs": ["You changed this setup. Original recommendations may no longer apply; review quantities and budget before checkout."]}
        try:
            result = make_plan(current["prompt"], current["budget_cents"], recommendation, catalog, current["ai_source"])
        except ValueError as error:
            raise HTTPException(422, str(error)) from None
        # Preserve the generator recorded with the original immutable plan, even
        # if deployment settings change before a user edits or checks out.
        result.update(ai_provider=current.get("ai_provider", "AI provider (not recorded)" if current["ai_source"] == "provider" else "Local rehearsal planner"),
                      ai_model=current.get("ai_model"))
        store.put_plan(session_id(request), result)
        return result

    @app.get("/api/orders")
    def orders(request: Request):
        return {"orders": store.orders(session_id(request))}

    @app.post("/api/orders")
    def create_order(body: OrderRequest, request: Request):
        plan = store.get_plan(session_id(request), body.plan_id)
        if not plan:
            raise HTTPException(404, "Plan not found in this browser session.")
        rate_limit(request, "payment")
        proposed = {"id": str(uuid.uuid4()), "plan_id": plan["id"], "provider_order_id": None,
                    "status": "CREATING", "total_cents": plan["total_cents"], "currency": "USD",
                    "mode": settings.payment_mode, "created_at": now_iso(), "created_timestamp": time.time(),
                    "capture_id": None, "approval_url": None, "items": plan["items"],
                    "budget_cents": plan["budget_cents"], "ai_source": plan["ai_source"],
                    "ai_provider": plan.get("ai_provider", "AI provider (not recorded)" if plan["ai_source"] == "provider" else "Local rehearsal planner"),
                    "ai_model": plan.get("ai_model")}
        order = store.reserve_order(session_id(request), proposed)
        if order["mode"] != settings.payment_mode:
            raise HTTPException(409, "This plan belongs to another payment mode. Build a fresh setup.")
        if order["status"] in {"COMPLETED", "SIMULATED", "PENDING", "CAPTURING"}:
            return order
        if settings.payment_mode == "rehearsal":
            order.update(provider_order_id="REHEARSAL-" + order["id"], status="CREATED")
            return store.update_order(session_id(request), order, allow_restart=True)
        provider = None
        if not order["provider_order_id"]:
            # PayPal stores idempotency keys for a finite window. Do not risk
            # creating another order after a long ambiguous create timeout.
            if time.time() - order["created_timestamp"] > 5 * 3600:
                raise HTTPException(409, "This checkout expired. Build a new setup before trying again.")
            provider = paypal.create(order)
            if not isinstance(provider, dict):
                raise ProviderError("PayPal did not return a valid sandbox order. Please retry.")
            provider_id = provider.get("id", "")
            if not isinstance(provider_id, str) or not re.fullmatch(r"[A-Za-z0-9]{5,64}", provider_id):
                raise ProviderError("PayPal did not return a valid sandbox order. Please retry.")
            order["provider_order_id"] = provider_id
            # Retain the reference even if a subsequent GET times out. A trusted
            # link is a candidate only until authoritative cart checks pass.
            order["approval_candidate"] = trusted_approval_url(provider)
            order = store.update_order(session_id(request), order)
        details = paypal.details(order["provider_order_id"])
        verify_paypal_order(details, order)
        if details.get("status") == "COMPLETED":
            status, capture_id = verified_capture(details, order)
            order.update(status=status, capture_id=capture_id)
            if status == "COMPLETED":
                order["captured_at"] = now_iso()
            return store.update_order(session_id(request), order)
        if details.get("status") == "APPROVED":
            order["status"] = "APPROVED"
            return store.update_order(session_id(request), order, allow_restart=True)
        if details.get("status") not in {"CREATED", "SAVED", "PAYER_ACTION_REQUIRED"}:
            raise HTTPException(409, "This PayPal order is no longer available for checkout. Build a new setup.")
        candidate_document = {"links": [{"rel": "approve", "href": order.get("approval_candidate") or order.get("approval_url")}]}
        approval = trusted_approval_url(details, provider, candidate_document)
        if not approval:
            raise ProviderError("PayPal did not return a trusted sandbox approval link. Please retry this checkout.")
        order.update(approval_url=approval, status="CREATED")
        return store.update_order(session_id(request), order, allow_restart=True)

    @app.post("/api/orders/{order_id}/capture")
    def capture_order(order_id: str, request: Request):
        order = owned_order(request, order_id)
        if order["status"] in {"COMPLETED", "SIMULATED"}:
            return order
        rate_limit(request, "payment")
        if order["mode"] != settings.payment_mode:
            raise HTTPException(409, "The payment mode changed. Build a fresh setup.")
        if settings.payment_mode == "rehearsal":
            if order["status"] not in {"CREATED", "CAPTURING"}:
                raise HTTPException(409, "Restart this checkout before simulating payment.")
            order.update(status="SIMULATED", capture_id="SIM-" + order["id"], captured_at=now_iso())
            return store.update_order(session_id(request), order)
        if not order["provider_order_id"]:
            raise HTTPException(409, "Create and approve this sandbox order before capture.")
        provider = paypal.details(order["provider_order_id"])
        verify_paypal_order(provider, order)
        if provider.get("status") == "COMPLETED":
            status, capture_id = verified_capture(provider, order)
        elif provider.get("status") == "APPROVED":
            order["status"] = "CAPTURING"
            order = store.update_order(session_id(request), order)
            if order["status"] in {"COMPLETED", "PENDING"}:
                return order
            paypal.capture(order)
            # The capture response can be a minimal representation. Verify the
            # authoritative order document after capture, also supporting retries.
            result = paypal.details(order["provider_order_id"])
            status, capture_id = verified_capture(result, order)
        else:
            raise HTTPException(409, "Approve this order on PayPal sandbox before completing payment.")
        order.update(status=status, capture_id=capture_id)
        if status == "COMPLETED":
            order["captured_at"] = now_iso()
        return store.update_order(session_id(request), order)

    @app.post("/api/orders/{order_id}/cancel")
    def cancel_order(order_id: str, request: Request):
        order = owned_order(request, order_id)
        if order["status"] in {"COMPLETED", "SIMULATED", "PENDING", "CAPTURING"}:
            return order
        order["status"] = "CANCELLED"
        return store.update_order(session_id(request), order)

    static_path = ROOT / "static"
    static_path.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        if not (static_path / "index.html").exists():
            return JSONResponse({"detail": "Frontend files are not installed."}, status_code=503)
        return FileResponse(static_path / "index.html")

    return app


app = create_app()
