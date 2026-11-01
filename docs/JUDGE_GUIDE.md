# Judge guide

Use the main README for the exact install/run command and required Python version. The app has two independent switches so a no-key rehearsal can be distinguished from external integrations.

| Configuration | What it proves |
| --- | --- |
| `AI_MODE=local`, `PAYMENT_MODE=rehearsal` | Browser workflow, deterministic product planning, cart validation and simulated order flow. No AI provider or PayPal calls are made. |
| `AI_MODE=provider`, `PAYMENT_MODE=sandbox` | A real configured AI model and PayPal sandbox checkout. Valid credentials, network access and a sandbox buyer are required. |

Local rehearsal is not a substitute for the hackathon's PayPal-plus-AI requirement.

## No-key rehearsal

1. Copy `.env.example` to `.env` if needed. Retain `AI_MODE=local` and `PAYMENT_MODE=rehearsal`.
2. Start the service using the README. Open its local URL.
3. Set a $150 budget and enter “A comfortable study desk for video calls; prioritize lighting and a keyboard.” Select **Build my setup**.
4. Review the suggested products and explanation. Change the cart and confirm that totals and remaining budget update.
5. Select **Review rehearsal checkout**, **Start rehearsal**, then **Simulate approval**. Inspect the simulated receipt or use **Download receipt**. It is not a PayPal transaction.

## Real provider and PayPal sandbox

The owner configures these values on the server; visitors must not enter merchant secrets in the browser:

```dotenv
AI_MODE=provider
AI_API_KEY=your_private_provider_key
AI_MODEL=an_available_chat_model_id
AI_BASE_URL=https://your-compatible-provider.example/v1
PAYMENT_MODE=sandbox
PAYPAL_CLIENT_ID=your_sandbox_app_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_app_secret
PUBLIC_BASE_URL=http://127.0.0.1:8000
DATABASE_PATH=./data/commerce.sqlite3
COOKIE_SECURE=false
```

Use the actual listening port from the README. `PUBLIC_BASE_URL` must exactly match the external origin used in the browser so approval/cancel returns reach the application. For a hosted demo, use its HTTPS URL and `COOKIE_SECURE=true`. The README explains supported Nebius aliases; configure one unambiguous set of provider credentials.

1. In the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/), create or select a **sandbox** REST application for a business test account. Copy that app's sandbox client ID and secret into the server configuration.
2. Prepare a separate sandbox personal buyer account with test funds. Use it on PayPal's **sandbox** approval site; never use a real buyer login for this test.
3. Set the AI provider's real key, available model and compatible endpoint. Check the provider's terms, data handling and spending settings.
4. Restart the app. Confirm the visible modes are provider AI and PayPal sandbox. Run the shopping example and obtain an AI plan.
5. Review the cart, create checkout, follow the PayPal approval link, approve using the sandbox buyer, then return to the application and select **Complete sandbox payment**.
6. Confirm the final receipt reports a successful sandbox capture and the expected USD amount. Refresh the receipt to confirm that reviewing it does not create another payment.
7. In a separate attempt, cancel on PayPal and confirm the app gives a recoverable outcome. A canceled or merely approved order is not a completed capture.

## Access for evaluation

For a hosted build, include the URL and any dedicated demo access code and sandbox buyer login in the organizer's private testing field. Keep access available, free of charge, through **15 December 2026, 9:30 pm IST**. Keep merchant credentials and AI API keys in the hosting provider's secret settings, never in the repository, screenshots or video.

If providing a local build, give complete setup instructions and a clear way for judges to obtain any required test access. Do not silently make judges pay for API usage. A no-key rehearsal alone does not demonstrate the real integration; provide a configured build or an organizer-approved access route for evaluating it.

On failure, note the visible error and order reference without sharing secrets. Check server logs privately and verify the provider model, sandbox credentials and `PUBLIC_BASE_URL`. If capture timed out, inspect the existing order before starting a replacement checkout.
