# TRACE Commerce · PayPal + AI Hackathon Edition

Public source: [ramvtdl1-tech/TRACE-Commerce](https://github.com/ramvtdl1-tech/TRACE-Commerce).

**An AI shopping assistant that shows its math, then asks before it pays.**

Turn a home-office brief and a dollar budget into a curated setup. Review the
reasons, change quantities, and approve a PayPal **sandbox** checkout. Prices,
budget limits and receipts are verified on the server; the model cannot create
payments or set prices.

This standalone project was created for the PayPal AI Hackathon. It lives beside
the earlier TRACE AI Streamlit app and does not load its conversations, database
or credentials. All catalog products are fictional. Nothing is shipped.

## Built With

| Tool | Concrete role |
| --- | --- |
| **PayPal sandbox REST API** | OAuth 2.0; Orders v2 create, buyer approval, authoritative order lookup and capture. The checkout is part of the main product flow. |
| **Nebius Token Factory AI** | Turns the brief, budget and catalog into structured recommendations. `nvidia/Nemotron-3_5-Lightning` was verified; the deployment can use another compatible model. |
| **Postman** | Included API collection, assertions and environment for inspecting the real app API and running the guarded rehearsal flow. See the verification record for runner results. |
| **Render** | Deployment Blueprint with persistent SQLite storage. Hosting has not yet been performed. |
| **FastAPI, SQLite, HTML/CSS/JavaScript** | Server validation, session-owned plans/orders, accessible browser interface and receipts. |

The app displays both active integration modes and the AI service/model. Receipts
retain the original plan's AI identity and budget alongside payment references.
Configuration labels are not proof of a successful PayPal or AI request.
The complete [resource map](docs/RESOURCES.md) covers every supplied sponsor,
webinar and PayPal resource, including which are references rather than runtime
dependencies. Optional sponsor tools are not all required by the hackathon.

**Integration verified:** on 1 November 2026, the real Nebius planning → buyer approval → PayPal sandbox capture journey completed for **$215.00 USD**. An independent read-only PayPal check confirmed the completed capture. See [verification details](docs/VERIFICATION.md). Hosting and submission remain pending.

## Run in five minutes

Requires Python 3.11+; no Node build or frontend dependencies.

```bash
cd trace-commerce
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp -n .env.example .env
python -m uvicorn commerce.app:app --host 127.0.0.1 --port 8000 --no-access-log
```

Open <http://127.0.0.1:8000>. If this directory is your repository root, omit the
first `cd`. On Windows, activate `.venv\Scripts\activate` instead.

The default **local planner + rehearsal checkout** runs without keys. It is a
deterministic practice mode, not evidence of meeting the hackathon's PayPal + AI
requirement. The interface and receipts label it as simulated.

## Enable the actual PayPal + AI demo

`.env.hackathon.example` is the provider + sandbox configuration profile. If
starting fresh, copy it to `.env` instead of the rehearsal profile. If `.env`
already exists, edit it instead of overwriting credentials.

1. Create a [PayPal Developer](https://developer.paypal.com/dashboard/) sandbox
   REST app. Copy its **Sandbox** client ID and secret into this project's `.env`.
   Create a separate sandbox **personal/buyer** account; do not approve as the
   merchant account. Use only fictional sandbox account details.
2. Obtain a compatible text-model API key, such as Nebius Token Factory, and a
   model ID available in your account. Set the following in `.env`:

   ```dotenv
   PAYMENT_MODE=sandbox
   AI_MODE=provider
   PAYPAL_CLIENT_ID=your_sandbox_client_id
   PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
   AI_API_KEY=your_provider_key
   AI_MODEL=your_available_chat_model
   AI_BASE_URL=https://api.tokenfactory.nebius.com/v1
   PUBLIC_BASE_URL=http://127.0.0.1:8000
   COOKIE_SECURE=false
   DATABASE_PATH=data/commerce.sqlite3
   ```

3. Restart the server. Verify both mode badges. Generate a plan, review it,
   continue to PayPal, sign in as the sandbox buyer, approve, and return to
   **Complete sandbox payment**. Confirm a `COMPLETED` receipt with a PayPal order
   ID and capture ID. Try cancellation and a repeated capture as well.
4. For a hosted demo use your exact **HTTPS origin** as `PUBLIC_BASE_URL` and
   `COOKIE_SECURE=true`. Keep the same hostname through approval and return so
   the browser's session cookie remains available.

Existing `NEBIUS_API_KEY`, `NEBIUS_MODEL` and `NEBIUS_BASE_URL` environment
variables are aliases. Nonempty `AI_*` values take precedence. The parent app's
`.env` is deliberately not read. Provider keys and PayPal secrets stay server-side.
Provider failures are reported; they do not silently become local recommendations.

After setting the provider credentials, `python scripts/check_ai.py` sends one
small real planning request and validates its catalog/budget result. It uses
provider credits and never calls PayPal. `AI_MAX_TOKENS` defaults to 4000 so a
reasoning model has space for its structured answer; set it between 512 and 8192
for the chosen model. A non-reasoning chat model can use a smaller limit.

## Deployment

**Docker Compose** (requires Docker Engine/Compose):

```bash
cp -n .env.example .env  # preserves an existing configuration
docker compose up --build -d
curl --fail http://127.0.0.1:8000/healthz
```

Compose binds to localhost and uses a named volume for the SQLite database.
For internet access put it behind an HTTPS reverse proxy, set the public origin
and secure cookie, and retain the volume. Run **one application instance with one
worker**. Do not mount the SQLite file across multiple hosts. The container runs
as a non-root user and includes a health check.

**Render**: publish the clean standalone source, create a Blueprint from
`render.yaml`, and enter your exact HTTPS service origin for `PUBLIC_BASE_URL`.
The configuration uses a persistent disk and a compatible paid service; review
Render's displayed cost before creating it. If keeping the parent repository,
select `trace-commerce/render.yaml` as the Blueprint path and add
`rootDir: trace-commerce` to the service. After the first rehearsal deployment,
set `PAYMENT_MODE=sandbox`, `AI_MODE=provider`, and add the four secret/model
variables in Render's environment settings. Redeploy and run the judge guide.
Configuration alone is not a Render deployment or a sponsor-prize claim.

Health endpoint: `/healthz`. SQLite must remain writable. A failed database check
fails readiness. Use `/api/config` to confirm active modes without revealing keys.
Hosting on Sites is not used: this Python backend needs a Python-capable host.

## Verification and release

```bash
python -m unittest discover -s tests -v
node --check static/app.js
python scripts/check_config.py
python scripts/check_submission.py --artifacts-only
python scripts/package_release.py
```

Tests use isolated temporary databases and fake providers; they never charge an
account. The release script writes `dist/trace-commerce-deploy.zip` using a source
allowlist, excluding `.env`, sessions, databases, virtual environments and caches.
Extract that archive as the root of a **public** GitHub/GitLab/Bitbucket repository
so this MIT `LICENSE` is detectable at the repository root.

See [verification results](docs/VERIFICATION.md) for the checks actually run and
the remaining live-service checks. CI is provided for the standalone repository.

With the app running, `python scripts/smoke_demo.py` checks the full no-key
rehearsal. It refuses sandbox mode; it does not approve payments or silently use
AI credits. Import the [Postman collection and environment](postman/README.md)
for an equivalent API walkthrough. AI provider checks require an explicit opt-in.

Before recording or submitting, run `python scripts/check_submission.py` with
the actual deployment configuration. It fails when provider + sandbox are not
both configured, even if the local rehearsal works. A passing configuration check
does not replace a real buyer approval/capture, eligibility review or public video.

## Architecture and limits

```text
Browser brief + budget
  -> FastAPI -> AI chat-completions API (or labeled local rehearsal planner)
  -> validate catalog IDs, quantities, integer-cent totals and budget
  -> save immutable plan -> human review / revised immutable plan
  -> PayPal sandbox OAuth + Orders v2 create -> buyer approval on PayPal
  -> explicit capture -> validate order, capture status, USD total and reference
  -> session-owned receipt in SQLite
```

The browser holds an opaque HttpOnly session cookie. Plans/orders belong to that
session, and mutations require its CSRF token. Clearing the cookie loses access
to its history. Sessions last seven days; expired-session records are cleaned on
new-session creation. There is no account login, real inventory, live payments,
refund handling or shipping fulfillment. Pending payments are not completed sales.
An unattended background webhook/reconciliation service is outside this demo;
an interrupted checkout can be resumed from its history.

SQLite stores prompts, recommendations and order/capture references. It does not
store card details or buyer passwords. The AI receives the brief, budget and
fictional catalog, not PayPal credentials or buyer payment details. Avoid entering
personal or sensitive information into the brief. Back up the database securely;
do not place it or API credentials in a public repository.

Hourly guards default to 20 plans/revisions and 40 payment attempts per session,
100 plans/revisions and 200 payment attempts across the instance. They include
failed requests and are stored in SQLite. Override with
`AI_SESSION_HOURLY_LIMIT`, `AI_GLOBAL_HOURLY_LIMIT`,
`PAYMENT_SESSION_HOURLY_LIMIT`, `PAYMENT_GLOBAL_HOURLY_LIMIT`.
Provider account limits remain necessary for controlling public-demo spend.

## Hackathon handoff

- [Rules analysis and submission checklist](docs/HACKATHON.md)
- [Judge setup and walkthrough](docs/JUDGE_GUIDE.md)
- [Devpost description draft](docs/SUBMISSION.md)
- [2 minute 40 second recording script](docs/DEMO_SCRIPT.md)
- [Data, attribution and dependencies](docs/DATA_AND_ATTRIBUTION.md)
- [Official sources](docs/SOURCES.md)

Your organizer reminder offers early eligibility review for entries submitted by
**Thursday, 5 November 2026**; it does not specify a cutoff time. You can continue
editing until the final deadline, **13 November 2026, 1:30 am IST**
(12 November, noon PST). A public source repository,
working provider + sandbox demonstration, publicly visible YouTube video under
three minutes, and Devpost submission still require the entrant's action.
Keep judge access available through **15 December 2026, 9:30 pm IST**.
