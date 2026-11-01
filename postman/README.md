# PayPal + AI API checks in Postman

Import `trace-commerce.postman_collection.json` and
`trace-commerce.postman_environment.json`. Select the supplied environment and
keep Postman's cookie jar enabled. Its only environment value is `base_url`.
Do not enter PayPal merchant secrets, AI keys or buyer passwords into Postman.
The application server owns those integrations.

## Automated rehearsal

Start the app with `AI_MODE=local`, `PAYMENT_MODE=rehearsal` and an exact matching
`PUBLIC_BASE_URL`. Run the **Rehearsal smoke** folder. It establishes a cookie/CSRF
session, reads catalog prices, creates and revises a plan, creates a rehearsal
order, simulates approval, and checks its session history. Every mutation refuses
provider or PayPal sandbox modes. The expected receipt status is `SIMULATED`.

Using [Newman, Postman's open-source collection runner](https://learning.postman.com/docs/reference/newman-cli/installing-running-newman):

```bash
newman run postman/trace-commerce.postman_collection.json \
  -e postman/trace-commerce.postman_environment.json \
  --folder 'Rehearsal smoke' --bail
```

Install Newman from the official npm `newman` package if needed. To test a
different local port, append `--env-var base_url=http://127.0.0.1:8001` and set the
app's `PUBLIC_BASE_URL` to the same origin. Do not use load testing or repeated
iterations against the public demo.

## Manual real AI + PayPal sandbox

Configure the server according to the main README. This folder is an API
inspection tool; the browser app remains the recommended end-to-end demo.

1. Send **Manual: establish session and inspect real modes**, then
   **Manual: read catalog**. Confirm `ai_mode=provider` and `mode=sandbox`.
2. Set the collection variable `manual_action` to `generate_ai_plan` immediately
   before sending **Manual: request one real AI plan**. This uses one model call.
3. Review the plan and its total. Set `manual_action=create_sandbox_order`, then
   send **Manual: create PayPal sandbox order**. Inspect `approval_url`; it must
   be an HTTPS PayPal sandbox URL. Open it in a browser and explicitly approve
   with a dedicated sandbox buyer.
4. In Postman set `manual_action=capture_approved_sandbox_order` and
   `buyer_approved_order_id` to the local `order_id` saved by step 3. Send
   **Manual: capture buyer-approved sandbox order** once. The server independently
   checks approval, order/cart references, currency and amount before recording
   success. `PENDING` is not a completed payment.
5. Send **Manual: inspect resulting payment history**. A completed sandbox
   receipt has `status=COMPLETED`, `mode=sandbox` and a capture reference.

Each action token is consumed before its request. Capture also consumes the
approved-order confirmation. The exported collection leaves both blank. Do not
run the manual folder with the Collection Runner, Newman or a monitor, and do
not save opted-in collection variables back into the public source.

The Postman cookie jar and browser cookies are separate. If PayPal redirects
into a browser that lacks the API session, the app cannot find that Postman
order there. Complete step 4 in the same Postman session. For the final hackathon
video, perform the whole flow in the browser app instead.

`csrf_token`, plan IDs and order IDs are session access material. Clear them and
the cookie jar after testing; do not export a populated private session. No
private environment or collection export belongs in the repository.

## What this proves

The collection checks actual application responses and server catalog totals.
Running the local folder proves the rehearsal API works and demonstrates use of
Postman's runner; it does not prove a real AI response or PayPal transaction.
Record the actual tools and results in `docs/VERIFICATION.md`. Importing these
files alone is not a sponsor-prize claim.

References: [cookies](https://learning.postman.com/docs/use/send-requests/response-data/cookies/),
[test scripts](https://learning.postman.com/docs/tests-and-scripts/write-scripts/test-examples/),
[request workflows and skipping](https://learning.postman.com/docs/collections/running-collections/building-workflows/),
[Newman options](https://learning.postman.com/docs/collections/using-newman-cli/newman-options).
