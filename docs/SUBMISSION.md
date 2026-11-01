# TRACE Commerce

> Submission draft: replace bracketed fields and verify every feature against the build you submit. This document is not a submitted Devpost entry.

**Tagline:** AI plans your workspace. You approve the budget and PayPal sandbox checkout.

**Short description:** TRACE Commerce uses **Nebius AI** to turn a budget and workspace brief into an explained, catalog-backed cart, then uses **PayPal sandbox Orders v2** to create, approve and capture that reviewed checkout. The server owns prices and verifies the payment; the buyer has the final say.

## Inspiration

A student or remote worker setting up a desk has a concrete problem: choose a useful combination of equipment without exceeding a fixed budget. A product list gives them options, but it does not explain trade-offs or turn a recommendation into a payment journey. TRACE Commerce connects those steps in one browser workspace.

## What it does

Describe your workspace needs and set a USD budget. TRACE selects a combination from a small, fictional 12-product catalog and explains its choices. Review the recommendation and cart before continuing to payment.

The server checks product IDs, quantities and budget constraints and calculates prices from its own catalog. An AI response cannot set the checkout price. Checkout creates a PayPal sandbox order, sends the buyer to PayPal to approve it, and captures the approved order on the server. The result is an order receipt linked to that cart.

The interface shows the active payment integration and AI provider/model. Plans and receipts retain which provider/model generated the original selection, even after cart edits, so the recommendation-to-payment trail is inspectable.

The catalog and checkout are a demonstration: there is no real inventory, shipping, fulfillment or live-money payment.

## How we built it

The browser interface is backed by a Python service and SQLite order storage. The provider mode sends the shopping request, budget and catalog to a configurable chat-completions AI service. A real request to **Nebius Token Factory, model `nvidia/Nemotron-3_5-Lightning`**, was verified on 1 November 2026. **[Confirm the same provider/model is used in the submitted recording, or replace with the actual choice.]** Server validation separates model suggestions from trusted checkout data.

PayPal's sandbox REST APIs provide OAuth access tokens, Orders v2 order creation and capture. Merchant credentials stay on the server. The buyer explicitly approves payment using a sandbox buyer account.

For development without credentials, a local planner and clearly labeled payment rehearsal let judges inspect the interface and exercise the cart flow. Those modes are not evidence of real AI or PayPal integration; the submitted video and combined integration check must use provider and PayPal sandbox modes.

## Built With

Use these names in Devpost's Built With fields, and explain both core integrations in the video:

| Tool | Role and current evidence |
| --- | --- |
| **PayPal Developer Platform / PayPal sandbox / Orders v2 REST API / OAuth 2.0** | Central checkout lifecycle: server-held merchant authentication, order creation, buyer approval, capture and verified receipt. Implemented, covered by controlled tests, and verified through a real $215.00 USD sandbox buyer approval/capture on 1 November 2026. |
| **Nebius Token Factory / `nvidia/Nemotron-3_5-Lightning`** | Generates structured product selections, reasons and trade-offs from the brief, budget and fictional catalog. Real provider and browser-to-provider requests verified. Replace this model name if the final recording uses another model. |
| **Python / FastAPI / SQLite** | Validates catalog IDs, quantities and integer-cent totals; stores session-owned plans and order references. |
| **JavaScript / HTML / CSS** | Browser workspace, cart review, approval handoff, payment history and receipts. |

An importable **Postman** API collection and **Render** deployment Blueprint are included in the repository. Add them to an actual-use claim only after running the collection in Postman or deploying on Render. The other optional sponsor products and PayPal SDK/AI Toolkit/MCP resources are references, not implemented dependencies. See `docs/RESOURCES.md`.

## Why it matters

The intended audience is people making a small workspace purchase with a firm spending limit. The demonstration addresses recommendation overload while keeping price validation and payment approval visible. Our contribution is the complete brief-to-validated-cart-to-sandbox-receipt journey, rather than an isolated chatbot response.

## Significant work during this hackathon

The earlier TRACE project was a general chatbot with session memory. This separate commerce application adds a curated catalog, budget-oriented AI planning, authoritative cart validation and a PayPal sandbox checkout lifecycle. **[Add dated commit/release references and any team contributions.]**

## Validation and limits

`python -m unittest discover -s tests -v`: **35 tests passed**. Postman’s Newman runner also passed **7 requests and 18 assertions**. Automated tests use controlled responses. The real Nebius request on 1 November 2026 produced five valid catalog items totaling **$215.00 within a $300.00 budget**; the browser integration also produced a valid five-product **$220.00** setup. Both results passed server catalog and budget validation. The combined browser journey completed a **$215.00 USD PayPal sandbox capture on 1 November 2026**. A separate read-only PayPal API request independently verified the completed capture, cart reference, currency and amount. See `docs/VERIFICATION.md` for scope and limitations.

This is a single-instance sandbox prototype. It does not provide production commerce fulfillment, live payments or evidence of real-world savings. No external deployment or successful PayPal transaction is implied by this draft.

## Submission links

- Public source: [ramvtdl1-tech/TRACE-Commerce](https://github.com/ramvtdl1-tech/TRACE-Commerce)
- Working demo or complete setup: **[demo URL or repository README URL]**
- Public YouTube demonstration, under three minutes: **[URL]**
- Testing instructions: `docs/JUDGE_GUIDE.md`
- License: `LICENSE`
- Built With: **PayPal sandbox Orders v2; OAuth 2.0; Nebius Token Factory; `nvidia/Nemotron-3_5-Lightning`; Python; FastAPI; SQLite; JavaScript; HTML; CSS.** **[Update final integration status and model; add Postman or Render only if actually used.]**

Provide any dedicated test account or access code in the appropriate private judging field. Do not paste merchant secrets or AI API keys into this public description.

Aim to submit for the organizer reminder's early eligibility review by **Thursday, 5 November 2026**; the reminder supplies no exact time. Editing remains available until the final **Thursday, 12 November, noon PST / Friday, 13 November, 1:30 am IST** deadline. Submitting or requesting early review has not been performed by this project generation.
