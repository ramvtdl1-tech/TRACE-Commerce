# Primary sources

Checked 1 November 2026. Linked services and rules may change; recheck them before the final submission.

- [PayPal AI Hackathon official rules](https://paypalaihackathon.devpost.com/rules): entrant/project requirements, schedule, judging access, intellectual property and prize conditions. The user supplied sections 1–7; the complete page also includes sections 8–15.
- [PayPal AI Hackathon overview](https://paypalaihackathon.devpost.com/): submission fields, including disclosure of AI tools and how they are used. When materials conflict, use the official rules.
- [Official resource index](https://paypalaihackathon.devpost.com/resources): sponsor pages, webinars, PayPal platform/SDK/payment capabilities and AI development references. See `RESOURCES.md` for actual-use status.
- [Official FAQ](https://paypalaihackathon.devpost.com/details/faqs): sponsor tools are optional, sandbox account availability is separate from entrant eligibility, and team/prize conditions remain subject to the rules.
- [Postman sponsor page](https://paypalaihackathon.devpost.com/details/postman): links to API testing resources and PayPal's API collection. An included collection does not prove an actual Postman execution.
- [Render sponsor page](https://paypalaihackathon.devpost.com/details/render), [Blueprint specification](https://render.com/docs/blueprint-spec) and [persistent disks](https://render.com/docs/disks): hosting preparation. A Blueprint is not evidence of deployment or Render Workflows use.
- [PayPal REST authentication](https://developer.paypal.com/api/rest/authentication/): server-side OAuth client-credentials access tokens for the sandbox API.
- [PayPal Orders v2 API](https://developer.paypal.com/api/orders/v2): create orders, retrieve order details and capture approved orders.
- [Create order](https://developer.paypal.com/api/orders/v2/orders-create) and [capture payment for order](https://developer.paypal.com/api/orders/v2/orders-capture): request/response contracts used by the integration.
- [PayPal sandbox accounts](https://developer.paypal.com/tools/sandbox/accounts/): separate test merchant and buyer accounts.
- [PayPal REST idempotency](https://developer.paypal.com/api/rest/reference/idempotency/): request IDs for supported POST operations and safe retry behavior.
- [Nebius inference API](https://api.tokenfactory.nebius.com/docs): compatible chat-completions protocol used by the configured AI provider.

The **Thursday, 5 November early eligibility-review target** comes from the organizer reminder supplied by the user. That reminder states no exact cutoff time/timezone for the early review. A focused check of accessible official pages did not independently establish that time. The final deadline remains the date/time in the official rules. No precise IST conversion for the early-review date is invented.

These links explain integration contracts; their presence does not establish that credentials, deployment or a live provider/sandbox transaction have been tested. Record actual verification in the release README.
