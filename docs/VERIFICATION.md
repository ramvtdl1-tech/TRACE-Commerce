# Verification record · Hackathon Edition 2.0.1

Verified 1 November 2026 using Python 3.11 on macOS. This is an integration record, not a hosted deployment receipt.

## Passed

- **Real end-to-end AI + PayPal sandbox checkout:** the user generated a Nebius plan, reviewed the cart, approved checkout as the sandbox buyer and completed capture. The stored receipt reports **$215.00 USD, COMPLETED**. A separate read-only PayPal Orders v2 request independently verified the order ID, cart reference, USD amount and completed capture ID against the stored receipt. No duplicate capture was attempted.
- **Recorded AI identity:** Nebius Token Factory / `nvidia/Nemotron-3_5-Lightning`. The original plan's provider/model and budget are retained on the order receipt.
- **41 automated backend/tooling tests:** `python -m unittest discover -s tests -v` passed. Controlled providers and isolated databases cover authoritative prices/budgets, session ownership, CSRF, quotas, malformed data, retries, pending captures, protected payment transitions, immutable AI provenance and tooling guards. Automated tests do not call real providers.
- **Actual Postman Newman 6.2.2 execution:** 7 rehearsal requests, 18 assertions, zero failures. The collection checks session/cookies/CSRF, catalog, plan/revision totals, simulated receipt and history. Its manual sandbox operations require separate one-shot opt-ins.
- **Python rehearsal smoke checker:** a $226.00 cart within $300.00 completed with a SIMULATED receipt. The checker refuses sandbox mutations and requires explicit opt-in for provider spending.
- **Real AI checks:** separate provider and browser-to-provider requests produced valid five-product $215.00 and $220.00 plans within $300.00. Updated provider credentials were subsequently checked against the model catalog and a real $215.00 planning result.
- **Browser checks:** planning, edits, over-budget rejection, reload restoration, catalog filtering, integration details, simulated approval/history/receipt download, narrow and desktop layouts. The user subsequently completed the real provider+sandbox browser journey above.
- **Source checks:** JavaScript syntax, Python compilation, dependency consistency, configuration and artifact preflight checks. Strict preflight distinguishes rehearsal from configured provider+sandbox; configuration alone does not prove payment success.
- **Deployment preparation:** Compose configuration and CI YAML parse. Clean source extraction previously served assets/health and completed rehearsal. GitHub-hosted CI and a Docker image build have not been run here.
- **Credential handling:** runtime keys are held in ignored private `.env` files; publishable example files contain placeholders. Source archives exclude credentials, SQLite/session records, virtual environments and caches.

Hosting configuration additionally verifies automatic Render origin selection, explicit custom-domain precedence and HTTPS validation. The Blueprint prompts privately for required credentials and selects provider + sandbox modes; it uses the documented `0.5c-512mb` plan ID.

## Remaining external work

1. Build/run the Docker image with Docker Engine available, or validate the chosen Python-capable host directly. Keep SQLite on persistent writable storage and use a single application instance.
2. Deploy if desired. Configure the exact HTTPS PUBLIC_BASE_URL and COOKIE_SECURE=true, then retest PayPal approval/return/capture. Render configuration alone is not proof of Render hosting.
3. Publish the public repository with its root MIT LICENSE, record/upload a publicly visible YouTube demo under three minutes, and submit the Devpost entry. Keep judge access available through 15 December 2026, 9:30 pm IST. Personal eligibility and ownership remain the entrant's responsibility.

Local/rehearsal mode is still available for practice; use provider+sandbox for the final demonstration. Real-money payments and product fulfillment are outside this project.

Provider diagnostics now distinguish authentication, permission, billing/quota, invalid model/request, network and upstream availability errors without returning provider bodies or credentials. Hosted AI planning reproduced a generic failure; the deployment must be retested after the diagnostic update to identify its upstream status.
